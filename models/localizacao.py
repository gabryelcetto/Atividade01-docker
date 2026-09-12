"""Queries sobre `localizacoes`.

Não está na lista de arquivos do documento de arquitetura (que só previa
equipamento/funcionario/movimentacao/ocorrencia/foto) — adicionado porque
tanto o cadastro quanto a edição de equipamento precisam de find-or-create
de sala/mesa, e isso não cabia limpo em nenhum dos arquivos previstos.
"""
# Só find-or-create por enquanto — sala/mesa são campos de texto livre no
# formulário, não um seletor. Se virar seletor, a listagem entra aqui.


# ---------------------------------------------------------------- escrita --
def buscar_ou_criar(cursor, sala, mesa=None):
    if not sala:
        return None
    cursor.execute(
        "SELECT id FROM localizacoes WHERE sala=%s AND (mesa=%s OR (mesa IS NULL AND %s IS NULL))",
        (sala, mesa, mesa))
    linha = cursor.fetchone()
    if linha:
        return linha[0]
    cursor.execute("INSERT INTO localizacoes (sala, mesa) VALUES (%s, %s)", (sala, mesa))
    return cursor.lastrowid
