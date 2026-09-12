"""Queries sobre `equipamentos` (+ tabelas relacionadas via JOIN).

Funções de LEITURA abrem/fecham a própria conexão (uso direto pelas rotas).
Funções de ESCRITA recebem um `cursor` já aberto — só devem ser chamadas de
dentro de uma transação de `services/equipamento_service.py`. Nenhuma rota
deve importar as funções de escrita diretamente.
"""
import time

from banco import cursor_leitura

# view "achatada" usada pelas telas — nome exposto -> coluna real (join já resolvido)
CAMPOS_LISTAGEM = """
    e.patrimonio, e.marca, e.modelo, e.numero_serie, e.endereco_mac,
    e.uso_externo, e.propriedade, e.data_compra, e.garantia_meses,
    e.data_fim_garantia, e.data_cadastro, e.observacao,
    c.id AS categoria_id, c.nome AS categoria,
    s.id AS status_id, s.nome AS status,
    f.id AS responsavel_id, f.nome AS responsavel, f.setor, f.cargo,
    l.id AS localizacao_id, l.sala, l.mesa
"""

BASE_FROM = """
    FROM equipamentos e
    JOIN categorias_equipamento c ON c.id = e.categoria_id
    JOIN status_equipamento s ON s.id = e.status_id
    LEFT JOIN funcionarios f ON f.id = e.responsavel_atual_id
    LEFT JOIN localizacoes l ON l.id = e.localizacao_atual_id
"""

# whitelist: nome vindo da URL (?filtro=) -> coluna SQL real.
# NUNCA montar WHERE/ORDER BY com o valor da URL direto na query (SQL injection).
FILTROS_PERMITIDOS = {
    "patrimonio": "e.patrimonio",
    "marca": "e.marca",
    "modelo": "e.modelo",
    "numero_serie": "e.numero_serie",
    "responsavel": "f.nome",
    "setor": "f.setor",
    "sala": "l.sala",
    "mesa": "l.mesa",
    "status": "s.nome",
    "endereco_mac": "e.endereco_mac",
    "data_cadastro": "e.data_cadastro",
    "observacao": "e.observacao",
    "propriedade": "e.propriedade",
}


# ---------------------------------------------------------------- leitura --
def listar(categoria_id=None, termo=None, filtro=None):
    """categoria_id=None lista todas as categorias juntas (a tela padrão de
    equipamentos); passando um id, filtra só aquela categoria."""
    sql = f"SELECT {CAMPOS_LISTAGEM} {BASE_FROM} WHERE 1=1"
    params = []

    if categoria_id:
        sql += " AND e.categoria_id = %s"
        params.append(categoria_id)

    if termo:
        if filtro and filtro in FILTROS_PERMITIDOS:
            sql += f" AND {FILTROS_PERMITIDOS[filtro]} LIKE %s"
            params.append(f"%{termo}%")
        else:
            sql += " AND (e.marca LIKE %s OR e.patrimonio LIKE %s OR f.nome LIKE %s)"
            params += [f"%{termo}%", f"%{termo}%", f"%{termo}%"]
    elif filtro and filtro in FILTROS_PERMITIDOS:
        sql += f" ORDER BY {FILTROS_PERMITIDOS[filtro]}"

    if "ORDER BY" not in sql:
        sql += " ORDER BY e.patrimonio"

    with cursor_leitura() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def listar_por_responsavel(funcionario_id):
    with cursor_leitura() as cursor:
        cursor.execute(f"SELECT {CAMPOS_LISTAGEM} {BASE_FROM} WHERE e.responsavel_atual_id = %s "
                       f"ORDER BY e.patrimonio", (funcionario_id,))
        return cursor.fetchall()


def listar_para_mapa():
    """Lista enxuta pro autocomplete do mapa das salas: patrimônio + o que
    ajuda a identificar o equipamento na hora de posicionar no mapa."""
    with cursor_leitura() as cursor:
        cursor.execute(
            """SELECT e.patrimonio, e.marca, e.modelo,
                      c.nome AS categoria, f.nome AS responsavel
               FROM equipamentos e
               JOIN categorias_equipamento c ON c.id = e.categoria_id
               LEFT JOIN funcionarios f ON f.id = e.responsavel_atual_id
               ORDER BY e.patrimonio""")
        return cursor.fetchall()


def buscar_por_patrimonio(patrimonio):
    with cursor_leitura() as cursor:
        cursor.execute(f"SELECT {CAMPOS_LISTAGEM} {BASE_FROM} WHERE e.patrimonio = %s",
                       (patrimonio,))
        return cursor.fetchone()


def existe(patrimonio):
    with cursor_leitura(dictionary=False) as cursor:
        cursor.execute("SELECT 1 FROM equipamentos WHERE patrimonio = %s", (patrimonio,))
        return cursor.fetchone() is not None


# Categorias e status são tabelas de referência — mudam só via migração, quase
# nunca em produção. Cadastro/listagem/edição consultam elas o tempo todo, e
# se o banco for remoto cada consulta custa uma ida-e-volta de rede. Um cache
# curto na memória do processo tira essas idas-e-voltas do caminho sem risco
# de mostrar dado velho (TTL de 5 min; reiniciar o app também limpa).
_CACHE_REF = {}
_CACHE_REF_TTL = 300  # segundos


def _referencia(chave, sql):
    agora = time.monotonic()
    valor, expira_em = _CACHE_REF.get(chave, (None, 0))
    if valor is None or agora >= expira_em:
        with cursor_leitura() as cursor:
            cursor.execute(sql)
            valor = cursor.fetchall()
        _CACHE_REF[chave] = (valor, agora + _CACHE_REF_TTL)
    return valor


def listar_categorias():
    return _referencia(
        "categorias", "SELECT id, nome FROM categorias_equipamento ORDER BY nome")


def listar_status():
    return _referencia(
        "status", "SELECT id, nome FROM status_equipamento ORDER BY id")


# ---------------------------------------------------------------- escrita --
# (recebem `cursor` já aberto — só chamar de dentro de uma transação do service)

def inserir(cursor, dados):
    cursor.execute(
        """INSERT INTO equipamentos
           (patrimonio, categoria_id, marca, modelo, numero_serie, endereco_mac,
            responsavel_atual_id, localizacao_atual_id, status_id, propriedade,
            uso_externo, data_compra, garantia_meses, data_cadastro, observacao)
           VALUES (%(patrimonio)s, %(categoria_id)s, %(marca)s, %(modelo)s,
            %(numero_serie)s, %(endereco_mac)s, %(responsavel_atual_id)s,
            %(localizacao_atual_id)s, %(status_id)s, %(propriedade)s,
            %(uso_externo)s, %(data_compra)s, %(garantia_meses)s,
            %(data_cadastro)s, %(observacao)s)""",
        dados,
    )


def atualizar_campos_simples(cursor, patrimonio, dados):
    """Atualiza só os campos que NÃO são cache de responsável/local/status."""
    cursor.execute(
        """UPDATE equipamentos SET
             marca=%(marca)s, modelo=%(modelo)s, numero_serie=%(numero_serie)s,
             endereco_mac=%(endereco_mac)s, propriedade=%(propriedade)s,
             uso_externo=%(uso_externo)s, data_compra=%(data_compra)s,
             garantia_meses=%(garantia_meses)s, observacao=%(observacao)s
           WHERE patrimonio=%(patrimonio)s""",
        {**dados, "patrimonio": patrimonio},
    )


def atualizar_cache_responsavel_local(cursor, patrimonio, funcionario_id, localizacao_id):
    cursor.execute(
        "UPDATE equipamentos SET responsavel_atual_id=%s, localizacao_atual_id=%s "
        "WHERE patrimonio=%s",
        (funcionario_id, localizacao_id, patrimonio),
    )


def atualizar_status(cursor, patrimonio, status_id):
    cursor.execute("UPDATE equipamentos SET status_id=%s WHERE patrimonio=%s",
                   (status_id, patrimonio))


def atualizar_observacao(cursor, patrimonio, observacao):
    cursor.execute("UPDATE equipamentos SET observacao=%s WHERE patrimonio=%s",
                   (observacao, patrimonio))


def excluir(cursor, patrimonio):
    cursor.execute("DELETE FROM equipamentos WHERE patrimonio=%s", (patrimonio,))
