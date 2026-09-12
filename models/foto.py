"""Queries sobre `fotos`.

A coluna `caminho_arquivo` guarda:
  - caminho relativo à pasta static/ (quando o armazenamento é local), ou
  - a URL pública completa (quando é bucket S3).
Ver services/armazenamento.py e o helper `url_foto()` em app.py.

`tamanho_bytes` é somado antes de cada upload pra travar o uso do bucket
dentro do tier gratuito (ver services/foto_service.py).
"""
from banco import cursor_leitura


def listar_por_equipamento(patrimonio):
    with cursor_leitura() as cursor:
        cursor.execute(
            "SELECT id, ocorrencia_id, caminho_arquivo, tipo, data_upload FROM fotos "
            "WHERE equipamento_patrimonio=%s ORDER BY data_upload DESC", (patrimonio,))
        return cursor.fetchall()


def buscar_por_id(foto_id):
    with cursor_leitura() as cursor:
        cursor.execute(
            "SELECT id, equipamento_patrimonio, ocorrencia_id, caminho_arquivo, tipo, "
            "tamanho_bytes, data_upload FROM fotos WHERE id=%s", (foto_id,))
        return cursor.fetchone()


def contar_por_equipamento(patrimonio):
    with cursor_leitura() as cursor:
        cursor.execute(
            "SELECT COUNT(*) AS n FROM fotos WHERE equipamento_patrimonio=%s",
            (patrimonio,))
        return cursor.fetchone()["n"]


def total_bytes():
    """Soma do tamanho de todas as fotos — usado pra não estourar o teto do bucket."""
    with cursor_leitura() as cursor:
        cursor.execute("SELECT COALESCE(SUM(tamanho_bytes), 0) AS total FROM fotos")
        return int(cursor.fetchone()["total"])


# ---------------------------------------------------------------- escrita --
def inserir(cursor, patrimonio, caminho_arquivo, tipo, tamanho_bytes, ocorrencia_id=None):
    cursor.execute(
        """INSERT INTO fotos
             (equipamento_patrimonio, ocorrencia_id, caminho_arquivo, tipo, tamanho_bytes)
           VALUES (%s, %s, %s, %s, %s)""",
        (patrimonio, ocorrencia_id, caminho_arquivo, tipo, tamanho_bytes),
    )
    return cursor.lastrowid


def excluir(cursor, foto_id):
    cursor.execute("DELETE FROM fotos WHERE id=%s", (foto_id,))
