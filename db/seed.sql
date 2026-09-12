-- ============================================================================
-- seed.sql — dados fictícios para demonstração (nenhum dado real).
--
-- 12 funcionários, 8 localizações e 40 equipamentos (30 propriedade='Empresa',
-- 10 propriedade='Particular'), além de um punhado de ocorrências e
-- movimentações para o histórico ter o que mostrar. Executado depois de
-- schema.sql pelo entrypoint do MySQL (docker-entrypoint-initdb.d/), só na
-- primeira inicialização do volume.
--
-- IDs de categoria/status usados abaixo (na ordem de inserção do schema.sql):
--   categorias: 1 Notebook, 2 Monitor, 3 Periférico, 4 Fone, 5 Outros
--   status_equipamento: 1 Em uso, 2 Disponível, 3 Manutenção, 4 Emprestado, 5 Baixado
--   status_ocorrencia: 1 Aberto, 2 Em análise, 3 Em manutenção, 4 Resolvido
-- ============================================================================

SET NAMES utf8mb4;

-- ==========================================
-- FUNCIONÁRIOS (12, fictícios)
-- ==========================================
INSERT INTO funcionarios (nome, setor, cargo, email, telefone) VALUES
('Ana Beatriz Ferreira',      'TI',         'Analista de Suporte',     'ana.ferreira@uvv-equipamentos.local',      '(27) 99999-0001'),
('Carlos Eduardo Lima',       'TI',         'Coordenador de TI',       'carlos.lima@uvv-equipamentos.local',       '(27) 99999-0002'),
('Mariana Souza Ribeiro',     'Financeiro', 'Analista Financeiro',     'mariana.ribeiro@uvv-equipamentos.local',   '(27) 99999-0003'),
('João Pedro Almeida',        'Financeiro', 'Assistente Financeiro',   'joao.almeida@uvv-equipamentos.local',      '(27) 99999-0004'),
('Fernanda Costa Martins',    'RH',         'Analista de RH',          'fernanda.martins@uvv-equipamentos.local',  '(27) 99999-0005'),
('Rafael Henrique Duarte',    'RH',         'Coordenador de RH',       'rafael.duarte@uvv-equipamentos.local',     '(27) 99999-0006'),
('Juliana Alves Cardoso',     'Comercial',  'Vendedora',               'juliana.cardoso@uvv-equipamentos.local',   '(27) 99999-0007'),
('Bruno Teixeira Rocha',      'Comercial',  'Gerente Comercial',       'bruno.rocha@uvv-equipamentos.local',       '(27) 99999-0008'),
('Camila Nascimento Pires',   'Operações',  'Assistente Operacional',  'camila.pires@uvv-equipamentos.local',      '(27) 99999-0009'),
('Diego Santos Barbosa',      'Operações',  'Supervisor Operacional',  'diego.barbosa@uvv-equipamentos.local',     '(27) 99999-0010'),
('Larissa Gomes Freitas',     'Marketing',  'Analista de Marketing',   'larissa.freitas@uvv-equipamentos.local',   '(27) 99999-0011'),
('Thiago Correia Vieira',     'Marketing',  'Coordenador de Marketing','thiago.vieira@uvv-equipamentos.local',     '(27) 99999-0012');

-- ==========================================
-- LOCALIZAÇÕES (8, fictícias)
-- ==========================================
INSERT INTO localizacoes (sala, mesa) VALUES
('Sala 1', 'Mesa 1'),
('Sala 1', 'Mesa 2'),
('Sala 1', 'Mesa 3'),
('Sala 2', 'Mesa 1'),
('Sala 2', 'Mesa 2'),
('Sala TI', 'Mesa 1'),
('Recepção', NULL),
('Sala de Reuniões', NULL);

-- ==========================================
-- EQUIPAMENTOS (40: 30 Empresa + 10 Particular)
-- ==========================================
INSERT INTO equipamentos
    (patrimonio, categoria_id, marca, modelo, numero_serie, endereco_mac,
     responsavel_atual_id, localizacao_atual_id, status_id, propriedade,
     uso_externo, data_compra, garantia_meses, data_cadastro, observacao)
VALUES
-- Notebooks (14: 10 Empresa + 4 Particular)
('NB-001', 1, 'Dell',     'Vostro 3510',     'SN-UVV-0001', '02:1A:2B:00:00:01',  2, 6, 1, 'Empresa',    FALSE, '2024-02-10', 24, '2024-02-12', NULL),
('NB-002', 1, 'Dell',     'Inspiron 15',     'SN-UVV-0002', '02:1A:2B:00:00:02',  3, 4, 1, 'Empresa',    FALSE, '2023-11-05', 24, '2023-11-07', NULL),
('NB-003', 1, 'Lenovo',   'ThinkPad E14',    'SN-UVV-0003', '02:1A:2B:00:00:03',  1, 6, 1, 'Empresa',    TRUE,  '2024-06-20', 36, '2024-06-22', 'Uso externo para atendimento técnico.'),
('NB-004', 1, 'Lenovo',   'IdeaPad 3',       'SN-UVV-0004', '02:1A:2B:00:00:04',  5, 2, 1, 'Empresa',    FALSE, '2023-08-14', 12, '2023-08-16', NULL),
('NB-005', 1, 'Positivo', 'Master N140i',    'SN-UVV-0005', '02:1A:2B:00:00:05',  7, 1, 1, 'Empresa',    TRUE,  '2024-01-09', 24, '2024-01-10', 'Uso externo para visitas a clientes.'),
('NB-006', 1, 'Acer',     'Aspire 5',        'SN-UVV-0006', '02:1A:2B:00:00:06',  8, 1, 1, 'Empresa',    TRUE,  '2024-03-01', 24, '2024-03-03', 'Uso externo para visitas a clientes.'),
('NB-007', 1, 'HP',       '240 G8',          'SN-UVV-0007', '02:1A:2B:00:00:07',  9, 5, 1, 'Empresa',    FALSE, '2023-05-22', 12, '2023-05-24', NULL),
('NB-008', 1, 'Samsung',  'Book X30',        'SN-UVV-0008', '02:1A:2B:00:00:08', 11, 3, 1, 'Empresa',    FALSE, '2024-07-18', 24, '2024-07-19', NULL),
('NB-009', 1, 'Lenovo',   'V15',             'SN-UVV-0009', '02:1A:2B:00:00:09', NULL, NULL, 2, 'Empresa',  FALSE, '2024-09-01', 24, '2024-09-02', 'Aguardando alocação para novo colaborador.'),
('NB-010', 1, 'Dell',     'Vostro 3510',     'SN-UVV-0010', '02:1A:2B:00:00:0A', NULL, NULL, 3, 'Empresa',  FALSE, '2022-10-10', 12, '2022-10-12', 'Tela com defeito, aguardando peça.'),
('NB-011', 1, 'Lenovo',   'ThinkPad E14',    'SN-UVV-0011', '02:1A:2B:00:00:0B',  4, 4, 1, 'Particular', FALSE, '2023-03-15', 12, '2023-03-16', 'Notebook pessoal, uso autorizado.'),
('NB-012', 1, 'Asus',     'VivoBook 15',     'SN-UVV-0012', '02:1A:2B:00:00:0C',  6, 2, 1, 'Particular', FALSE, '2023-12-01', 12, '2023-12-02', 'Notebook pessoal, uso autorizado.'),
('NB-013', 1, 'HP',       '240 G8',          'SN-UVV-0013', '02:1A:2B:00:00:0D', 10, 5, 1, 'Particular', FALSE, '2024-04-04', 12, '2024-04-05', 'Notebook pessoal, uso autorizado.'),
('NB-014', 1, 'Samsung',  'Book X30',        'SN-UVV-0014', '02:1A:2B:00:00:0E', 12, 3, 5, 'Particular', FALSE, '2021-05-10', 12, '2021-05-11', 'Equipamento pessoal, baixado do inventário (desligamento).'),

-- Monitores (12: 9 Empresa + 3 Particular)
('MN-001', 2, 'Samsung',    'F24T450',        'SN-UVV-0015', NULL,  2, 6, 1, 'Empresa',    FALSE, '2024-02-10', 24, '2024-02-12', NULL),
('MN-002', 2, 'Samsung',    'F24T450',        'SN-UVV-0016', NULL,  1, 6, 1, 'Empresa',    FALSE, '2024-02-10', 24, '2024-02-12', NULL),
('MN-003', 2, 'LG',         '22MK400',        'SN-UVV-0017', NULL,  3, 4, 1, 'Empresa',    FALSE, '2023-11-05', 24, '2023-11-07', NULL),
('MN-004', 2, 'LG',         '22MK400',        'SN-UVV-0018', NULL,  4, 4, 1, 'Empresa',    FALSE, '2023-11-05', 24, '2023-11-07', NULL),
('MN-005', 2, 'AOC',        '24B2XH',         'SN-UVV-0019', NULL,  5, 2, 1, 'Empresa',    FALSE, '2023-08-14', 12, '2023-08-16', NULL),
('MN-006', 2, 'Dell',       'E2222H',         'SN-UVV-0020', NULL,  7, 1, 1, 'Empresa',    FALSE, '2024-01-09', 24, '2024-01-10', NULL),
('MN-007', 2, 'Dell',       'E2222H',         'SN-UVV-0021', NULL,  8, 1, 1, 'Empresa',    FALSE, '2024-03-01', 24, '2024-03-03', NULL),
('MN-008', 2, 'Multilaser', '21.5" M2159',    'SN-UVV-0022', NULL,  9, 5, 1, 'Empresa',    FALSE, '2023-05-22', 12, '2023-05-24', NULL),
('MN-009', 2, 'AOC',        '24B2XH',         'SN-UVV-0023', NULL, 11, 3, 1, 'Particular', FALSE, '2024-07-18', 12, '2024-07-19', 'Monitor pessoal, uso autorizado.'),
('MN-010', 2, 'Samsung',    'F24T450',        'SN-UVV-0024', NULL, NULL, NULL, 2, 'Empresa', FALSE, '2024-09-01', 24, '2024-09-02', NULL),
('MN-011', 2, 'LG',         '22MK400',        'SN-UVV-0025', NULL,  6, 2, 1, 'Particular', FALSE, '2023-02-20', 12, '2023-02-21', 'Monitor pessoal, uso autorizado.'),
('MN-012', 2, 'AOC',        '24B2XH',         'SN-UVV-0026', NULL, 10, 5, 1, 'Particular', FALSE, '2024-05-05', 12, '2024-05-06', 'Monitor pessoal, uso autorizado.'),

-- Periféricos (6: 5 Empresa + 1 Particular)
('PF-001', 3, 'Logitech',   'Kit MK540',      'SN-UVV-0027', NULL,  2, 6, 1, 'Empresa',    FALSE, '2024-02-10', 12, '2024-02-12', NULL),
('PF-002', 3, 'Multilaser', 'Kit TC195',      'SN-UVV-0028', NULL,  3, 4, 1, 'Empresa',    FALSE, '2023-11-05', 12, '2023-11-07', NULL),
('PF-003', 3, 'Dell',       'Kit KM3322W',    'SN-UVV-0029', NULL,  9, 5, 1, 'Empresa',    FALSE, '2023-05-22', 12, '2023-05-24', NULL),
('PF-004', 3, 'Logitech',   'Mouse M170',     'SN-UVV-0030', NULL, NULL, NULL, 2, 'Empresa', FALSE, '2024-09-01', 12, '2024-09-02', NULL),
('PF-005', 3, 'Multilaser', 'Teclado TC090',  'SN-UVV-0031', NULL,  5, 2, 1, 'Empresa',    FALSE, '2023-08-14', 12, '2023-08-16', NULL),
('PF-006', 3, 'Logitech',   'Kit MK540',      'SN-UVV-0032', NULL,  6, 2, 1, 'Particular', FALSE, '2023-02-20', 12, '2023-02-21', 'Periférico pessoal, uso autorizado.'),

-- Fones (4: 3 Empresa + 1 Particular)
('FN-001', 4, 'JBL',        'T110',           'SN-UVV-0033', NULL,  1, 6, 1, 'Empresa',    FALSE, '2024-02-10', 12, '2024-02-12', NULL),
('FN-002', 4, 'Multilaser', 'PH216',          'SN-UVV-0034', NULL,  7, 1, 1, 'Empresa',    FALSE, '2024-01-09', 12, '2024-01-10', NULL),
('FN-003', 4, 'Philips',    'TAUH202',        'SN-UVV-0035', NULL, NULL, NULL, 4, 'Empresa', FALSE, '2023-10-01', 12, '2023-10-03', 'Emprestado para reunião externa.'),
('FN-004', 4, 'JBL',        'Tune 510BT',     'SN-UVV-0036', NULL, 11, 3, 1, 'Particular', FALSE, '2024-06-01', 12, '2024-06-02', 'Fone pessoal, uso autorizado.'),

-- Outros (4: 3 Empresa + 1 Particular)
('OT-001', 5, 'APC',        'Back-UPS 600VA', 'SN-UVV-0037', NULL, NULL, 6, 1, 'Empresa',    FALSE, '2023-01-15', 24, '2023-01-17', 'Nobreak da sala de TI.'),
('OT-002', 5, 'TP-Link',    'Hub USB UH400',  'SN-UVV-0038', NULL,  2, 6, 1, 'Empresa',    FALSE, '2024-02-10', 12, '2024-02-12', NULL),
('OT-003', 5, 'Multilaser', 'Webcam AC340',   'SN-UVV-0039', NULL, NULL, 8, 4, 'Empresa',    FALSE, '2024-03-20', 12, '2024-03-22', 'Webcam da sala de reuniões, emprestada para home office.'),
('OT-004', 5, 'Multilaser', 'Caixa de Som SP150', 'SN-UVV-0040', NULL, 12, 3, 1, 'Particular', FALSE, '2024-08-01', 12, '2024-08-02', 'Caixa de som pessoal, uso autorizado.');

-- ==========================================
-- MOVIMENTAÇÕES (histórico fictício)
-- ==========================================
INSERT INTO movimentacoes
    (equipamento_patrimonio, funcionario_anterior_id, funcionario_novo_id,
     localizacao_anterior_id, localizacao_nova_id, data_movimentacao, observacao)
VALUES
('NB-001', NULL, 2,    NULL, 6,    '2024-02-12 09:00:00', 'Cadastro inicial e entrega ao colaborador.'),
('NB-002', NULL, 3,    NULL, 4,    '2023-11-07 10:00:00', 'Cadastro inicial e entrega ao colaborador.'),
('NB-004', NULL, 5,    NULL, 2,    '2023-08-16 09:30:00', 'Cadastro inicial e entrega ao colaborador.'),
('MN-001', NULL, 2,    NULL, 6,    '2024-02-12 09:05:00', 'Cadastro inicial junto com o notebook NB-001.'),
('NB-009', NULL, NULL, NULL, NULL, '2024-09-02 11:00:00', 'Cadastrado em estoque, aguardando alocação.'),
('NB-014', 12,   NULL, 3,    NULL, '2026-07-01 15:00:00', 'Colaborador desligado; equipamento particular, baixado do inventário.'),
('FN-003', NULL, 7,    NULL, 1,    '2023-10-03 14:00:00', 'Emprestado para reunião externa.'),
('FN-003', 7,    NULL, 1,    NULL, '2023-10-20 16:00:00', 'Devolvido após a reunião.'),
('PF-004', NULL, NULL, NULL, NULL, '2024-09-02 11:10:00', 'Cadastrado em estoque.'),
('OT-003', NULL, 8,    8,    NULL, '2024-03-22 08:00:00', 'Emprestada para uso em home office.');

-- ==========================================
-- OCORRÊNCIAS (histórico fictício de problemas)
-- ==========================================
INSERT INTO ocorrencias
    (equipamento_patrimonio, funcionario_id, data_abertura, problema_relatado,
     descricao, status_id, tecnico_responsavel_id, solucao_aplicada, data_resolucao)
VALUES
('NB-010', NULL, '2024-08-01 10:00:00', 'Tela com falhas de exibição (manchas e flicker)',
    'Passou a apresentar manchas na tela após uma queda leve.', 3, 1, NULL, NULL),
('FN-003', 7,    '2023-10-05 09:00:00', 'Fone sem áudio no canal esquerdo',
    NULL, 4, 2, 'Substituído o cabo P2; funcionando normalmente.', '2023-10-15 16:00:00'),
('OT-003', 8,    '2024-03-21 08:30:00', 'Webcam não é reconhecida pelo notebook',
    NULL, 4, 1, 'Reinstalado o driver USB; webcam voltou a funcionar.', '2024-03-25 11:00:00'),
('NB-007', 9,    '2026-08-20 13:00:00', 'Bateria não segura carga',
    'Notebook desliga sozinho às vezes, mesmo com o carregador conectado.', 1, NULL, NULL, NULL),
('MN-008', 9,    '2026-09-01 09:15:00', 'Monitor com linha vertical na tela',
    NULL, 2, 2, NULL, NULL),
('PF-003', 9,    '2023-06-02 11:00:00', 'Mouse do kit com clique duplo indevido',
    NULL, 4, 1, 'Equipamento trocado por unidade nova do estoque.', '2023-06-10 15:00:00');
