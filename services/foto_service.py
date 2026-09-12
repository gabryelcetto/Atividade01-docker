"""Camada de serviço de `fotos`.

Grava o arquivo no armazenamento (disco local ou bucket S3 — ver
`services/armazenamento.py`) e registra a linha no banco como uma operação só:
se o INSERT falhar depois do arquivo já ter subido, o arquivo é apagado de
novo (não fica lixo órfão).

Aplica os limites que garantem que o bucket R2 nunca sai do tier gratuito
(tamanho do arquivo, nº de fotos por equipamento, uso total). Esses limites
vêm da config e são passados pela rota — esta camada não conhece Flask.
"""
from banco import transacao
from models import foto as foto_model
from services import ServiceError
from services.armazenamento import ErroArmazenamento

EXTENSOES_PERMITIDAS = {"jpg", "jpeg", "png", "gif", "webp"}
TIPOS_PERMITIDOS = {"cadastro", "problema"}
CONTENT_TYPE = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "gif": "image/gif", "webp": "image/webp",
}


def _extensao(nome_arquivo):
    return nome_arquivo.rsplit(".", 1)[-1].lower() if "." in nome_arquivo else ""


def _mb(n_bytes):
    return n_bytes / (1024 * 1024)


def salvar_foto(armazenamento, patrimonio, arquivo, tipo, ocorrencia_id=None, *,
                max_arquivo_bytes, max_por_equipamento, max_total_bytes):
    """
    armazenamento: instância de ArmazenamentoLocal/ArmazenamentoS3.
    arquivo: o werkzeug FileStorage vindo de request.files.
    max_arquivo_bytes / max_por_equipamento / max_total_bytes: travas (config).
    """
    if tipo not in TIPOS_PERMITIDOS:
        raise ServiceError(f"Tipo de foto inválido: '{tipo}'.")
    if not arquivo or not arquivo.filename:
        raise ServiceError("Escolha um arquivo de imagem.")

    extensao = _extensao(arquivo.filename)
    if extensao not in EXTENSOES_PERMITIDAS:
        raise ServiceError(
            f"Formato não aceito ('.{extensao}'). Use: "
            f"{', '.join(sorted(EXTENSOES_PERMITIDAS))}.")

    dados = arquivo.read()
    tamanho = len(dados)
    if not tamanho:
        raise ServiceError("O arquivo enviado está vazio.")
    if tamanho > max_arquivo_bytes:
        raise ServiceError(
            f"Imagem muito grande ({_mb(tamanho):.1f} MB). "
            f"O limite por foto é {_mb(max_arquivo_bytes):.0f} MB.")

    if foto_model.contar_por_equipamento(patrimonio) >= max_por_equipamento:
        raise ServiceError(
            f"Este equipamento já tem {max_por_equipamento} fotos (o limite). "
            "Remova alguma antes de enviar outra.")

    # Trava dura de uso total — só faz sentido no bucket (no disco local o
    # limite é o espaço da máquina). Impede o R2 de passar do tier gratuito.
    if getattr(armazenamento, "modo", None) == "s3":
        usado = foto_model.total_bytes()
        if usado + tamanho > max_total_bytes:
            raise ServiceError(
                f"Limite de armazenamento de fotos atingido "
                f"({_mb(usado):.0f} MB de {_mb(max_total_bytes):.0f} MB). "
                "Remova fotos antigas pra liberar espaço.")

    try:
        referencia = armazenamento.salvar(
            patrimonio, extensao, dados, CONTENT_TYPE.get(extensao))
    except ErroArmazenamento as erro:
        raise ServiceError(f"Não consegui salvar a imagem: {erro}") from erro

    try:
        with transacao() as cursor:
            foto_model.inserir(
                cursor, patrimonio, referencia, tipo, tamanho, ocorrencia_id)
    except Exception:
        armazenamento.remover(referencia)
        raise

    return referencia


def excluir_foto(armazenamento, foto_id):
    foto = foto_model.buscar_por_id(foto_id)
    if not foto:
        raise ServiceError("Foto não encontrada.")
    with transacao() as cursor:
        foto_model.excluir(cursor, foto_id)
    armazenamento.remover(foto["caminho_arquivo"])
