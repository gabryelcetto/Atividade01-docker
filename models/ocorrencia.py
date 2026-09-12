"""Queries sobre `ocorrencias`."""
from banco import cursor_leitura

CAMPOS = """
    o.id, o.equipamento_patrimonio, o.data_abertura, o.problema_relatado,
    o.descricao, o.solucao_aplicada, o.data_resolucao,
    s.id AS status_id, s.nome AS status,
    f.nome AS funcionario, t.nome AS tecnico_responsavel
"""
BASE_FROM = """
    FROM ocorrencias o
    JOIN status_ocorrencia s ON s.id = o.status_id
    LEFT JOIN funcionarios f ON f.id = o.funcionario_id
    LEFT JOIN funcionarios t ON t.id = o.tecnico_responsavel_id
"""


def listar_por_equipamento(patrimonio):
    with cursor_leitura() as cursor:
        cursor.execute(f"SELECT {CAMPOS} {BASE_FROM} WHERE o.equipamento_patrimonio = %s "
                       f"ORDER BY o.data_abertura DESC", (patrimonio,))
        return cursor.fetchall()


def buscar_por_id(id_):
    with cursor_leitura() as cursor:
        cursor.execute(f"SELECT {CAMPOS} {BASE_FROM} WHERE o.id = %s", (id_,))
        return cursor.fetchone()


def listar_abertas():
    with cursor_leitura() as cursor:
        cursor.execute(f"SELECT {CAMPOS} {BASE_FROM} WHERE s.nome <> 'Resolvido' "
                       f"ORDER BY o.data_abertura")
        return cursor.fetchall()


# ---------------------------------------------------------------- escrita --
def inserir(cursor, patrimonio, funcionario_id, problema_relatado, descricao, status_id):
    cursor.execute(
        """INSERT INTO ocorrencias
           (equipamento_patrimonio, funcionario_id, problema_relatado, descricao, status_id)
           VALUES (%s, %s, %s, %s, %s)""",
        (patrimonio, funcionario_id, problema_relatado, descricao, status_id),
    )
    return cursor.lastrowid


def resolver(cursor, ocorrencia_id, status_id, solucao_aplicada, tecnico_id):
    cursor.execute(
        """UPDATE ocorrencias
           SET status_id=%s, solucao_aplicada=%s, tecnico_responsavel_id=%s,
               data_resolucao=NOW()
           WHERE id=%s""",
        (status_id, solucao_aplicada, tecnico_id, ocorrencia_id),
    )


def status_id_por_nome(cursor, nome):
    cursor.execute("SELECT id FROM status_ocorrencia WHERE nome=%s", (nome,))
    linha = cursor.fetchone()
    return linha[0] if linha else None
