"""Queries sobre `funcionarios`.

Exclusão é sempre soft-delete (`excluido_em`) — o registro nunca some do
banco, porque equipamentos/movimentacoes/ocorrencias antigos podem apontar
pra ele. NULL = ativo, preenchido = excluído."""
from banco import cursor_leitura

CAMPOS = "id, nome, setor, cargo, email, telefone, excluido_em"


def listar(termo=None, setor=None):
    """Só os ativos — é o que aparece nas telas normais e nos seletores.
    `termo` busca em nome/setor/cargo; `setor` filtra por um setor exato."""
    sql = f"SELECT {CAMPOS} FROM funcionarios WHERE excluido_em IS NULL"
    params = []
    if setor:
        sql += " AND setor = %s"
        params.append(setor)
    if termo:
        sql += " AND (nome LIKE %s OR setor LIKE %s OR cargo LIKE %s)"
        params += [f"%{termo}%", f"%{termo}%", f"%{termo}%"]
    sql += " ORDER BY nome"
    with cursor_leitura() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def listar_setores():
    with cursor_leitura(dictionary=False) as cursor:
        cursor.execute("SELECT DISTINCT setor FROM funcionarios "
                       "WHERE setor IS NOT NULL AND excluido_em IS NULL ORDER BY setor")
        return [linha[0] for linha in cursor.fetchall()]


def listar_excluidos():
    with cursor_leitura() as cursor:
        cursor.execute(f"SELECT {CAMPOS} FROM funcionarios WHERE excluido_em IS NOT NULL "
                       f"ORDER BY excluido_em DESC")
        return cursor.fetchall()


def buscar_por_id(id_):
    with cursor_leitura() as cursor:
        cursor.execute(f"SELECT {CAMPOS} FROM funcionarios WHERE id=%s", (id_,))
        return cursor.fetchone()


def contar_equipamentos_sob_responsabilidade(id_):
    with cursor_leitura(dictionary=False) as cursor:
        cursor.execute("SELECT COUNT(*) FROM equipamentos WHERE responsavel_atual_id=%s",
                       (id_,))
        return cursor.fetchone()[0]


# ---------------------------------------------------------------- escrita --
def buscar_ou_criar(cursor, nome, setor=None, cargo=None):
    """find-or-create por (nome, setor) entre os ATIVOS — mesma regra usada na
    migração: duas pessoas de mesmo nome em setores diferentes são pessoas
    diferentes. Se achar só um excluído com esse nome/setor, cria um novo em
    vez de reativar por engano (reativar é uma ação explícita, na tela de
    excluídos). `cursor` já deve estar dentro da transação do service chamador."""
    if not nome:
        return None
    cursor.execute(
        "SELECT id, cargo FROM funcionarios WHERE nome=%s AND "
        "(setor=%s OR (setor IS NULL AND %s IS NULL)) AND excluido_em IS NULL",
        (nome, setor, setor))
    linha = cursor.fetchone()
    if linha:
        id_, cargo_atual = linha
        if cargo and not cargo_atual:
            cursor.execute("UPDATE funcionarios SET cargo=%s WHERE id=%s", (cargo, id_))
        return id_
    cursor.execute("INSERT INTO funcionarios (nome, setor, cargo) VALUES (%s, %s, %s)",
                   (nome, setor, cargo))
    return cursor.lastrowid


def excluir(cursor, id_):
    cursor.execute("UPDATE funcionarios SET excluido_em=NOW() WHERE id=%s", (id_,))


def restaurar(cursor, id_):
    cursor.execute("UPDATE funcionarios SET excluido_em=NULL WHERE id=%s", (id_,))


def atualizar(cursor, id_, dados):
    cursor.execute(
        """UPDATE funcionarios SET nome=%(nome)s, setor=%(setor)s, cargo=%(cargo)s,
             email=%(email)s, telefone=%(telefone)s WHERE id=%(id)s""",
        {**dados, "id": id_})
