"""Queries sobre `movimentacoes` (histórico append-only — nunca UPDATE/DELETE).

Só escrita por enquanto — a leitura do histórico global fica em
models/dashboard.py (`movimentacoes recentes`). Não há tela de histórico por
equipamento ainda; quando houver, a query de listagem entra aqui."""


# ---------------------------------------------------------------- escrita --
def inserir(cursor, patrimonio, funcionario_anterior_id, funcionario_novo_id,
            localizacao_anterior_id, localizacao_nova_id, observacao=None):
    cursor.execute(
        """INSERT INTO movimentacoes
           (equipamento_patrimonio, funcionario_anterior_id, funcionario_novo_id,
            localizacao_anterior_id, localizacao_nova_id, observacao)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (patrimonio, funcionario_anterior_id, funcionario_novo_id,
         localizacao_anterior_id, localizacao_nova_id, observacao),
    )
