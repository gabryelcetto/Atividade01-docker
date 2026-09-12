import os
import queue
import time
from contextlib import contextmanager

from dotenv import load_dotenv
from mysql.connector.cursor import MySQLCursor, MySQLCursorDict
from mysql.connector.errors import InterfaceError, PoolError
from mysql.connector.pooling import (
    CONNECTION_POOL_LOCK,
    MySQLConnectionPool,
    PooledMySQLConnection,
)

load_dotenv()


def _parametros_conexao():
    parametros = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "controle_equipamentos"),
    }

    ssl_ca = os.getenv("DB_SSL_CA")
    if ssl_ca:
        parametros["ssl_ca"] = ssl_ca
        parametros["ssl_verify_cert"] = True

    # Em algumas máquinas a C-extension do mysql-connector-python falha ao
    # conectar no MySQL local com "RuntimeError: Failed raising error" (bug
    # ao reportar o erro real). DB_USE_PURE=true no .env força o conector
    # Python puro, que não tem esse problema.
    if os.getenv("DB_USE_PURE", "").lower() in ("1", "true", "yes"):
        parametros["use_pure"] = True

    # autocommit=True é importante com pool: sem isso, um simples SELECT (com
    # autocommit desligado) deixa uma transação implícita aberta na conexão, que
    # volta pro pool assim e faz o próximo `transacao()` estourar
    # "Transaction already in progress". Com autocommit ligado, leitura não abre
    # transação, e o `transacao()` usa START TRANSACTION explícito.
    parametros["autocommit"] = True

    return parametros


# ---------------------------------------------------------------------------
# Pool de conexões
#
# Antes, cada `cursor_leitura()`/`transacao()` abria uma conexão nova e fechava
# no fim. Contra um MySQL local (~1 ms) isso passava batido; contra um banco
# remoto, abrir conexão custa ~5 idas-e-voltas de rede (TCP + handshake TLS +
# login) — pode chegar à casa dos segundos. Um load do dashboard fazendo isso
# 2x já ficava perceptível.
#
# O pool mantém as conexões vivas e as reaproveita. `pool_reset_session=False`
# porque ninguém deixa estado de sessão sujo (o `transacao()` sempre fecha a
# transação com commit/rollback) e resetar a sessão num banco remoto seria
# mais uma ida-e-volta.
#
# O `MySQLConnectionPool.get_connection()` padrão manda um COM_PING pro servidor
# TODA vez que entrega uma conexão (pra ver se está viva) — mais uma ida-e-volta
# de rede por request quando o banco é remoto. Como o `wait_timeout` costuma ser
# de várias horas, uma conexão usada há poucos segundos com certeza ainda está
# viva; a subclasse abaixo pula o ping nesse caso e só checa/reconecta quando a
# conexão ficou parada além de _JANELA_CONFIAVEL.
# ---------------------------------------------------------------------------

_JANELA_CONFIAVEL = 25  # segundos


class _PoolReaproveitando(MySQLConnectionPool):
    def _queue_connection(self, cnx):
        cnx._devolvida_em = time.monotonic()
        super()._queue_connection(cnx)

    def get_connection(self):
        with CONNECTION_POOL_LOCK:
            try:
                cnx = self._cnx_queue.get(block=False)
            except queue.Empty:
                raise PoolError("Failed getting connection; pool exhausted")

            recente = (
                time.monotonic() - getattr(cnx, "_devolvida_em", 0.0)
                < _JANELA_CONFIAVEL
            )
            viva = recente or cnx.is_connected()
            if not viva or self._config_version != cnx.pool_config_version:
                cnx.config(**self._cnx_config)
                try:
                    cnx.reconnect()
                except InterfaceError:
                    self._queue_connection(cnx)
                    raise
                cnx.pool_config_version = self._config_version

            return PooledMySQLConnection(self, cnx)


_pool = None


def _obter_pool():
    global _pool
    if _pool is None:
        _pool = _PoolReaproveitando(
            pool_name="controle_equipamentos",
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            pool_reset_session=False,
            **_parametros_conexao(),
        )
    return _pool


# Pega uma conexão do pool.
# Toda credencial vem de variável de ambiente (.env) — nunca fixa no código.
# Isso vale mesmo rodando fora de container: se um dia o banco for pra Docker,
# só muda o valor das variáveis, não o código que lê elas.
def conectar():
    try:
        return _obter_pool().get_connection()
    except Exception as erro:
        # Antes isso engolia o erro e devolvia None, o que virava um
        # AttributeError confuso ("NoneType has no attribute cursor") lá na
        # frente. Melhor deixar o erro real de conexão subir.
        print("Falha na conexão com o banco:", erro)
        raise


def _abrir_cursor(conexao, dictionary):
    """Cria o cursor direto da classe, em vez de `conexao.cursor()`.

    `PooledMySQLConnection.cursor()` chama `is_connected()` toda vez, que manda
    um COM_PING ao servidor — mais uma ida-e-volta de rede (cara se o banco for
    remoto) além da que o pool já fez no `get_connection()`. Instanciando o
    cursor direto a gente pula esse ping duplicado."""
    classe = MySQLCursorDict if dictionary else MySQLCursor
    return classe(conexao._cnx)


@contextmanager
def cursor_leitura(dictionary=True):
    """Abre conexão + cursor pra uma leitura simples e devolve os dois pro pool
    no final. Uso: `with cursor_leitura() as cursor: cursor.execute(...)`."""
    conexao = conectar()
    cursor = _abrir_cursor(conexao, dictionary)
    try:
        yield cursor
    finally:
        cursor.close()
        conexao.close()  # volta pro pool, não destrói


@contextmanager
def transacao():
    """Abre conexão + cursor dentro de uma transação: commit se o bloco
    terminar sem erro, rollback se estourar qualquer exceção — e sempre
    devolve cursor/conexão pro pool no final. É o jeito único de escrever nas
    tabelas protegidas (equipamentos.responsavel_atual_id/localizacao_atual_id/
    status_id), conforme a regra da camada de serviço.
    Uso: `with transacao() as cursor: cursor.execute(...)`."""
    conexao = conectar()
    cursor = _abrir_cursor(conexao, dictionary=False)
    try:
        conexao.start_transaction()
        yield cursor
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        cursor.close()
        conexao.close()
