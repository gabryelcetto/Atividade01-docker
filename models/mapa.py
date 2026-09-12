"""Query da tabela `mapa_salas` — uma linha só (id=1) com o layout do mapa
das salas inteiro serializado em JSON.

`mapa_salas_historico` guarda as últimas versões salvas (rede de segurança:
migração 011). Ver services/mapa_service.py.
"""
from banco import cursor_leitura

_ID = 1
MAX_HISTORICO = 30


def carregar():
    """Devolve {'layout_json': str, 'atualizado_em': datetime} ou None se
    ninguém salvou o mapa ainda."""
    with cursor_leitura() as cursor:
        cursor.execute(
            "SELECT layout_json, atualizado_em FROM mapa_salas WHERE id=%s", (_ID,))
        return cursor.fetchone()


def listar_historico():
    """Só metadados das versões guardadas (id + quando), mais nova primeiro."""
    with cursor_leitura() as cursor:
        cursor.execute(
            "SELECT id, salvo_em FROM mapa_salas_historico "
            "ORDER BY salvo_em DESC, id DESC")
        return cursor.fetchall()


def buscar_versao(historico_id):
    with cursor_leitura() as cursor:
        cursor.execute(
            "SELECT id, salvo_em, layout_json FROM mapa_salas_historico WHERE id=%s",
            (historico_id,))
        return cursor.fetchone()


# ---------------------------------------------------------------- escrita --
def _snapshot(cursor):
    """Copia o mapa atual (se existir) pro histórico e poda os antigos."""
    cursor.execute("SELECT layout_json FROM mapa_salas WHERE id=%s", (_ID,))
    atual = cursor.fetchone()
    if not atual:
        return
    cursor.execute(
        "INSERT INTO mapa_salas_historico (layout_json) VALUES (%s)", (atual[0],))
    cursor.execute(
        """DELETE FROM mapa_salas_historico
           WHERE id NOT IN (
             SELECT id FROM (
               SELECT id FROM mapa_salas_historico
               ORDER BY salvo_em DESC, id DESC LIMIT %s
             ) t
           )""",
        (MAX_HISTORICO,))


def salvar(cursor, layout_json):
    """Guarda o estado atual no histórico e grava o novo."""
    _snapshot(cursor)
    cursor.execute(
        """INSERT INTO mapa_salas (id, layout_json) VALUES (%s, %s)
           ON DUPLICATE KEY UPDATE layout_json = VALUES(layout_json)""",
        (_ID, layout_json),
    )
