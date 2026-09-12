"""Camada de serviço de `equipamentos`.

Regra central do documento de arquitetura: nenhuma rota Flask pode fazer
UPDATE direto em responsavel_atual_id, localizacao_atual_id ou status_id de
`equipamentos`. Toda alteração desses campos passa obrigatoriamente por uma
destas funções, cada uma dentro de `banco.transacao()` (commit automático no
fim do bloco, rollback automático se algo der errado).
"""
import datetime

from mysql.connector import IntegrityError

from banco import transacao
from models import equipamento as equipamento_model
from models import funcionario as funcionario_model
from models import localizacao as localizacao_model
from models import movimentacao as movimentacao_model
from services import ServiceError


def _status_id(cursor, nome):
    cursor.execute("SELECT id FROM status_equipamento WHERE nome=%s", (nome,))
    linha = cursor.fetchone()
    if not linha:
        raise ServiceError(f"Status '{nome}' não existe.")
    return linha[0]


def _mover(cursor, patrimonio, novo_funcionario_id, nova_localizacao_id, observacao):
    """Lê o responsável/local atuais, loga a movimentação e atualiza o cache.
    Só é chamada quando responsável e/ou local realmente mudaram."""
    cursor.execute(
        "SELECT responsavel_atual_id, localizacao_atual_id FROM equipamentos "
        "WHERE patrimonio=%s FOR UPDATE", (patrimonio,))
    linha = cursor.fetchone()
    if not linha:
        raise ServiceError(f"Equipamento '{patrimonio}' não encontrado.")
    funcionario_anterior_id, localizacao_anterior_id = linha

    movimentacao_model.inserir(cursor, patrimonio, funcionario_anterior_id,
                               novo_funcionario_id, localizacao_anterior_id,
                               nova_localizacao_id, observacao)
    equipamento_model.atualizar_cache_responsavel_local(
        cursor, patrimonio, novo_funcionario_id, nova_localizacao_id)


def criar_equipamento(dados):
    """dados: dict já validado pela rota. Chaves esperadas: patrimonio,
    categoria_id, marca, modelo, numero_serie, endereco_mac, responsavel_nome,
    setor, cargo, sala, mesa, status, propriedade, uso_externo, data_compra,
    garantia_meses, data_cadastro, observacao."""
    if equipamento_model.existe(dados["patrimonio"]):
        raise ServiceError(f"Já existe um equipamento com o patrimônio "
                           f"'{dados['patrimonio']}'.")

    with transacao() as cursor:
        funcionario_id = funcionario_model.buscar_ou_criar(
            cursor, dados.get("responsavel_nome"), dados.get("setor"), dados.get("cargo"))
        localizacao_id = localizacao_model.buscar_ou_criar(
            cursor, dados.get("sala"), dados.get("mesa"))
        status_id = _status_id(cursor, dados["status"])

        equipamento_model.inserir(cursor, {
            "patrimonio": dados["patrimonio"],
            "categoria_id": dados["categoria_id"],
            "marca": dados.get("marca") or None,
            "modelo": dados.get("modelo") or None,
            "numero_serie": dados.get("numero_serie") or None,
            "endereco_mac": dados.get("endereco_mac") or None,
            "responsavel_atual_id": funcionario_id,
            "localizacao_atual_id": localizacao_id,
            "status_id": status_id,
            "propriedade": dados.get("propriedade") or "Empresa",
            "uso_externo": bool(dados.get("uso_externo")),
            "data_compra": dados.get("data_compra") or None,
            "garantia_meses": dados.get("garantia_meses") or None,
            "data_cadastro": dados["data_cadastro"],
            "observacao": dados.get("observacao") or None,
        })

        if funcionario_id or localizacao_id:
            movimentacao_model.inserir(cursor, dados["patrimonio"], None, funcionario_id,
                                       None, localizacao_id, "Cadastro inicial")


def mover_equipamento(patrimonio, novo_funcionario_id, nova_localizacao_id, observacao=None):
    """Troca responsável e/ou localização, registrando o histórico."""
    with transacao() as cursor:
        _mover(cursor, patrimonio, novo_funcionario_id, nova_localizacao_id, observacao)


def atualizar_equipamento(patrimonio, dados):
    """Edição geral: campos simples sempre; responsável/local só via
    movimentação (se mudaram); status só se mudou."""
    with transacao() as cursor:
        cursor.execute(
            "SELECT responsavel_atual_id, localizacao_atual_id, status_id FROM equipamentos "
            "WHERE patrimonio=%s FOR UPDATE", (patrimonio,))
        linha = cursor.fetchone()
        if not linha:
            raise ServiceError(f"Equipamento '{patrimonio}' não encontrado.")
        resp_atual_id, local_atual_id, status_atual_id = linha

        novo_funcionario_id = funcionario_model.buscar_ou_criar(
            cursor, dados.get("responsavel_nome"), dados.get("setor"), dados.get("cargo"))
        nova_localizacao_id = localizacao_model.buscar_ou_criar(
            cursor, dados.get("sala"), dados.get("mesa"))

        if novo_funcionario_id != resp_atual_id or nova_localizacao_id != local_atual_id:
            motivo = dados.get("motivo_movimentacao") or "Editado na tela de edição"
            movimentacao_model.inserir(cursor, patrimonio, resp_atual_id, novo_funcionario_id,
                                       local_atual_id, nova_localizacao_id, motivo)
            equipamento_model.atualizar_cache_responsavel_local(
                cursor, patrimonio, novo_funcionario_id, nova_localizacao_id)

        novo_status_id = _status_id(cursor, dados["status"])
        if novo_status_id != status_atual_id:
            equipamento_model.atualizar_status(cursor, patrimonio, novo_status_id)

        equipamento_model.atualizar_campos_simples(cursor, patrimonio, {
            "marca": dados.get("marca") or None,
            "modelo": dados.get("modelo") or None,
            "numero_serie": dados.get("numero_serie") or None,
            "endereco_mac": dados.get("endereco_mac") or None,
            "propriedade": dados.get("propriedade") or "Empresa",
            "uso_externo": bool(dados.get("uso_externo")),
            "data_compra": dados.get("data_compra") or None,
            "garantia_meses": dados.get("garantia_meses") or None,
            "observacao": dados.get("observacao") or None,
        })


def dar_baixa_equipamento(patrimonio, motivo):
    """Baixa = status 'Baixado' + motivo anotado. Não apaga o equipamento
    (ele continua consultável, só sai de uso)."""
    with transacao() as cursor:
        status_id = _status_id(cursor, "Baixado")
        cursor.execute("SELECT observacao FROM equipamentos WHERE patrimonio=%s FOR UPDATE",
                       (patrimonio,))
        linha = cursor.fetchone()
        if not linha:
            raise ServiceError(f"Equipamento '{patrimonio}' não encontrado.")
        hoje = datetime.date.today().strftime("%d/%m/%Y")
        nova_obs = f"{linha[0] or ''}\n[Baixa em {hoje}] {motivo}".strip()

        equipamento_model.atualizar_status(cursor, patrimonio, status_id)
        equipamento_model.atualizar_observacao(cursor, patrimonio, nova_obs)


def excluir_equipamento(patrimonio):
    """DELETE de verdade — só pra corrigir cadastro errado. Se o equipamento
    já tem histórico (movimentação/ocorrência/foto), a FK barra e a gente
    devolve um erro amigável em vez do IntegrityError cru; nesse caso use
    dar_baixa_equipamento."""
    try:
        with transacao() as cursor:
            equipamento_model.excluir(cursor, patrimonio)
    except IntegrityError:
        raise ServiceError(
            "Não é possível excluir: este equipamento já tem histórico "
            "(movimentação, ocorrência ou foto). Use 'dar baixa' em vez de excluir.")
