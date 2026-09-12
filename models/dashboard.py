"""Consultas agregadas pro dashboard. Não estava na lista de arquivos do
documento de arquitetura — adicionado pra tela de entrada do design novo.

As duas consultas rodam na MESMA conexão (um `with cursor_leitura()` só), pra
não pagar duas idas-e-voltas de rede até o banco num único load da tela."""
from banco import cursor_leitura


SQL_RESUMO = """
    SELECT
      COUNT(*) AS total,
      SUM(s.nome = 'Em uso') AS em_uso,
      SUM(s.nome = 'Disponível') AS disponiveis,
      SUM(s.nome = 'Manutenção') AS manutencao,
      SUM(e.data_fim_garantia IS NOT NULL
          AND e.data_fim_garantia BETWEEN CURDATE() AND CURDATE() + INTERVAL 60 DAY
      ) AS garantias_vencendo
    FROM equipamentos e
    JOIN status_equipamento s ON s.id = e.status_id
"""

SQL_MOVIMENTACOES = """
    SELECT m.data_movimentacao, e.patrimonio, e.marca, e.modelo,
           c.nome AS categoria, s.nome AS status,
           fn.nome AS responsavel, ln.sala, ln.mesa
    FROM movimentacoes m
    JOIN equipamentos e ON e.patrimonio = m.equipamento_patrimonio
    JOIN categorias_equipamento c ON c.id = e.categoria_id
    JOIN status_equipamento s ON s.id = e.status_id
    LEFT JOIN funcionarios fn ON fn.id = m.funcionario_novo_id
    LEFT JOIN localizacoes ln ON ln.id = m.localizacao_nova_id
    ORDER BY m.data_movimentacao DESC
    LIMIT %s
"""


def carregar(limite_movimentacoes=6):
    """Devolve (resumo, movimentacoes) numa conexão só."""
    with cursor_leitura() as cursor:
        cursor.execute(SQL_RESUMO)
        resumo = cursor.fetchone()
        for chave in resumo:
            resumo[chave] = int(resumo[chave] or 0)

        cursor.execute(SQL_MOVIMENTACOES, (limite_movimentacoes,))
        movimentacoes = cursor.fetchall()

    return resumo, movimentacoes
