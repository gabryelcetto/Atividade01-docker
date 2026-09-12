"""Camada de serviço de `ocorrencias` — funções obrigatórias do documento de
arquitetura. Ainda sem rota/tela própria (fica pra uma próxima etapa); a
camada já fica pronta pra quando isso entrar."""
from banco import transacao
from models import equipamento as equipamento_model
from models import ocorrencia as ocorrencia_model
from services import ServiceError


def _status_equipamento_id(cursor, nome):
    cursor.execute("SELECT id FROM status_equipamento WHERE nome=%s", (nome,))
    linha = cursor.fetchone()
    if not linha:
        raise ServiceError(f"Status de equipamento '{nome}' não existe.")
    return linha[0]


def abrir_ocorrencia(patrimonio, funcionario_id, problema_relatado, descricao,
                     muda_status_para=None):
    with transacao() as cursor:
        status_aberto_id = ocorrencia_model.status_id_por_nome(cursor, "Aberto")
        if not status_aberto_id:
            raise ServiceError("Status 'Aberto' não existe em status_ocorrencia.")

        ocorrencia_id = ocorrencia_model.inserir(
            cursor, patrimonio, funcionario_id, problema_relatado, descricao, status_aberto_id)

        if muda_status_para:
            equipamento_model.atualizar_status(
                cursor, patrimonio, _status_equipamento_id(cursor, muda_status_para))

    return ocorrencia_id


def resolver_ocorrencia(ocorrencia_id, solucao_aplicada, tecnico_id,
                        novo_status_equipamento=None):
    with transacao() as cursor:
        status_resolvido_id = ocorrencia_model.status_id_por_nome(cursor, "Resolvido")
        if not status_resolvido_id:
            raise ServiceError("Status 'Resolvido' não existe em status_ocorrencia.")

        cursor.execute("SELECT equipamento_patrimonio FROM ocorrencias WHERE id=%s FOR UPDATE",
                       (ocorrencia_id,))
        linha = cursor.fetchone()
        if not linha:
            raise ServiceError(f"Ocorrência #{ocorrencia_id} não encontrada.")
        patrimonio = linha[0]

        ocorrencia_model.resolver(cursor, ocorrencia_id, status_resolvido_id,
                                  solucao_aplicada, tecnico_id)

        if novo_status_equipamento:
            equipamento_model.atualizar_status(
                cursor, patrimonio, _status_equipamento_id(cursor, novo_status_equipamento))
