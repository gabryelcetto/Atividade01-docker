-- ============================================================================
-- schema.sql — schema completo do Controle de Equipamentos (UVV).
--
-- Executado automaticamente pela imagem oficial do MySQL na primeira
-- inicialização do container (docker-entrypoint-initdb.d/), antes de
-- seed.sql. Idempotente (CREATE TABLE IF NOT EXISTS / INSERT IGNORE), mas na
-- prática só roda uma vez por volume: o entrypoint do MySQL só executa esses
-- scripts quando /var/lib/mysql ainda está vazio.
-- ============================================================================

-- ==========================================
-- TABELAS DE APOIO (listas fechadas / lookup)
-- ==========================================

CREATE TABLE IF NOT EXISTS categorias_equipamento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT IGNORE INTO categorias_equipamento (nome) VALUES
    ('Notebook'), ('Monitor'), ('Periférico'), ('Fone'), ('Outros');

CREATE TABLE IF NOT EXISTS status_equipamento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT IGNORE INTO status_equipamento (nome) VALUES
    ('Em uso'), ('Disponível'), ('Manutenção'), ('Emprestado'), ('Baixado');

CREATE TABLE IF NOT EXISTS status_ocorrencia (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT IGNORE INTO status_ocorrencia (nome) VALUES
    ('Aberto'), ('Em análise'), ('Em manutenção'), ('Resolvido');

CREATE TABLE IF NOT EXISTS funcionarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    setor VARCHAR(100),
    cargo VARCHAR(100),
    email VARCHAR(150),
    telefone VARCHAR(20),
    -- soft delete: NULL = ativo, preenchido = excluído (mas continua no banco,
    -- porque equipamentos/movimentacoes/ocorrencias antigos podem referenciar
    -- esse id).
    excluido_em DATETIME NULL,
    UNIQUE KEY uk_nome_setor (nome, setor)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS localizacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sala VARCHAR(50) NOT NULL,
    mesa VARCHAR(50),
    UNIQUE KEY uk_sala_mesa (sala, mesa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ==========================================
-- TABELA CENTRAL
-- ==========================================

CREATE TABLE IF NOT EXISTS equipamentos (
    patrimonio VARCHAR(20) PRIMARY KEY,
    categoria_id INT NOT NULL,
    marca VARCHAR(100),
    modelo VARCHAR(100),
    numero_serie VARCHAR(100),
    endereco_mac VARCHAR(20),
    responsavel_atual_id INT NULL,
    localizacao_atual_id INT NULL,
    status_id INT NOT NULL,
    propriedade ENUM('Empresa', 'Particular') NOT NULL DEFAULT 'Empresa',
    uso_externo BOOLEAN NOT NULL DEFAULT FALSE,
    data_compra DATE NULL,
    garantia_meses INT NULL,
    data_fim_garantia DATE GENERATED ALWAYS AS (
        DATE_ADD(data_compra, INTERVAL garantia_meses MONTH)
    ) STORED,
    data_cadastro DATE NOT NULL,
    observacao TEXT NULL,

    FOREIGN KEY (categoria_id) REFERENCES categorias_equipamento(id),
    FOREIGN KEY (responsavel_atual_id) REFERENCES funcionarios(id),
    FOREIGN KEY (localizacao_atual_id) REFERENCES localizacoes(id),
    FOREIGN KEY (status_id) REFERENCES status_equipamento(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ==========================================
-- HISTÓRICO (append-only — nunca UPDATE/DELETE)
-- ==========================================

CREATE TABLE IF NOT EXISTS movimentacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    equipamento_patrimonio VARCHAR(20) NOT NULL,
    funcionario_anterior_id INT NULL,
    funcionario_novo_id INT NULL,
    localizacao_anterior_id INT NULL,
    localizacao_nova_id INT NULL,
    data_movimentacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observacao TEXT NULL,

    FOREIGN KEY (equipamento_patrimonio) REFERENCES equipamentos(patrimonio),
    FOREIGN KEY (funcionario_anterior_id) REFERENCES funcionarios(id),
    FOREIGN KEY (funcionario_novo_id) REFERENCES funcionarios(id),
    FOREIGN KEY (localizacao_anterior_id) REFERENCES localizacoes(id),
    FOREIGN KEY (localizacao_nova_id) REFERENCES localizacoes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS ocorrencias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    equipamento_patrimonio VARCHAR(20) NOT NULL,
    funcionario_id INT NULL,
    data_abertura DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    problema_relatado VARCHAR(255) NOT NULL,
    descricao TEXT NULL,
    status_id INT NOT NULL,
    tecnico_responsavel_id INT NULL,
    solucao_aplicada TEXT NULL,
    data_resolucao DATETIME NULL,

    FOREIGN KEY (equipamento_patrimonio) REFERENCES equipamentos(patrimonio),
    FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id),
    FOREIGN KEY (status_id) REFERENCES status_ocorrencia(id),
    FOREIGN KEY (tecnico_responsavel_id) REFERENCES funcionarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS fotos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    equipamento_patrimonio VARCHAR(20) NOT NULL,
    ocorrencia_id INT NULL,
    caminho_arquivo VARCHAR(255) NOT NULL,
    tipo ENUM('cadastro', 'problema') NOT NULL,
    tamanho_bytes INT UNSIGNED NOT NULL DEFAULT 0,
    data_upload DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (equipamento_patrimonio) REFERENCES equipamentos(patrimonio),
    FOREIGN KEY (ocorrencia_id) REFERENCES ocorrencias(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ==========================================
-- MAPA DAS SALAS (layout salvo como JSON, uma linha)
-- ==========================================

CREATE TABLE IF NOT EXISTS mapa_salas (
    id            TINYINT UNSIGNED NOT NULL PRIMARY KEY,
    layout_json   LONGTEXT NOT NULL,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                  ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS mapa_salas_historico (
    id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    salvo_em      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    layout_json   LONGTEXT NOT NULL,
    KEY idx_salvo_em (salvo_em)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
