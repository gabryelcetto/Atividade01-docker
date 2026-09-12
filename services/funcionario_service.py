"""Camada de serviço de `funcionarios`.

Exclusão é sempre soft-delete: o registro fica no banco (histórico de
movimentações/ocorrências antigas continua íntegro), só sai das listas e
seletores ativos. Por isso não existe "excluir de vez" aqui como existe em
equipamentos — não tem por quê: nada é perdido mantendo o registro."""
from mysql.connector import IntegrityError

from banco import transacao
from models import funcionario as funcionario_model
from services import ServiceError


def atualizar_funcionario(id_, dados):
    """dados: nome, setor, cargo, email, telefone. `nome`/`setor` continuam
    únicos juntos (uk_nome_setor) — se colidir com outro funcionário já
    existente, devolve um erro amigável em vez do IntegrityError cru."""
    if not funcionario_model.buscar_por_id(id_):
        raise ServiceError(f"Funcionário #{id_} não encontrado.")
    if not dados.get("nome"):
        raise ServiceError("Nome é obrigatório.")

    try:
        with transacao() as cursor:
            funcionario_model.atualizar(cursor, id_, dados)
    except IntegrityError:
        raise ServiceError(
            f"Já existe outro funcionário chamado '{dados['nome']}' no mesmo setor.")


def excluir_funcionario(id_):
    """Retorna quantos equipamentos esse funcionário ainda tem sob
    responsabilidade — a rota usa isso pra avisar o usuário (a exclusão
    acontece de qualquer jeito; a pessoa pode ter saído da empresa antes de
    devolver o equipamento)."""
    funcionario = funcionario_model.buscar_por_id(id_)
    if not funcionario:
        raise ServiceError(f"Funcionário #{id_} não encontrado.")
    if funcionario["excluido_em"]:
        raise ServiceError(f"{funcionario['nome']} já está excluído.")

    with transacao() as cursor:
        funcionario_model.excluir(cursor, id_)

    return funcionario_model.contar_equipamentos_sob_responsabilidade(id_)


def restaurar_funcionario(id_):
    funcionario = funcionario_model.buscar_por_id(id_)
    if not funcionario:
        raise ServiceError(f"Funcionário #{id_} não encontrado.")
    if not funcionario["excluido_em"]:
        raise ServiceError(f"{funcionario['nome']} já está ativo.")

    with transacao() as cursor:
        funcionario_model.restaurar(cursor, id_)
