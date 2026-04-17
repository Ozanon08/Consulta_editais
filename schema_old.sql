PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS subtema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tema_id INTEGER,
    nome TEXT NOT NULL,
    UNIQUE(tema_id, nome),
    FOREIGN KEY (tema_id) REFERENCES tema(id)
);

CREATE TABLE IF NOT EXISTS pais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS estado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pais_id INTEGER,
    sigla TEXT,
    nome TEXT NOT NULL UNIQUE,
    FOREIGN KEY (pais_id) REFERENCES pais(id)
);

CREATE TABLE IF NOT EXISTS municipio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estado_id INTEGER,
    nome TEXT NOT NULL,
    UNIQUE(estado_id, nome),
    FOREIGN KEY (estado_id) REFERENCES estado(id)
);

CREATE TABLE IF NOT EXISTS tipo_edital (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS unidade (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS fonte_dado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS servico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS edital (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tema_id INTEGER,
    subtema_id INTEGER,
    pais_id INTEGER,
    estado_id INTEGER,
    municipio_id INTEGER,
    nome_edital TEXT,
    descricao TEXT,
    esforco TEXT,
    unidade_id INTEGER,
    prazo_meses REAL,
    tipo_edital_id INTEGER,
    codigo_planilha TEXT,
    fonte_dado_id INTEGER,
    observacao TEXT,
    custo_execucao REAL,
    data_edital TEXT,
    metodo_calculo TEXT,
    valor_min REAL,
    valor_max REAL,
    FOREIGN KEY (tema_id) REFERENCES tema(id),
    FOREIGN KEY (subtema_id) REFERENCES subtema(id),
    FOREIGN KEY (pais_id) REFERENCES pais(id),
    FOREIGN KEY (estado_id) REFERENCES estado(id),
    FOREIGN KEY (municipio_id) REFERENCES municipio(id),
    FOREIGN KEY (unidade_id) REFERENCES unidade(id),
    FOREIGN KEY (tipo_edital_id) REFERENCES tipo_edital(id),
    FOREIGN KEY (fonte_dado_id) REFERENCES fonte_dado(id)
);

CREATE TABLE IF NOT EXISTS edital_servico (
    edital_id INTEGER NOT NULL,
    servico_id INTEGER NOT NULL,
    PRIMARY KEY (edital_id, servico_id),
    FOREIGN KEY (edital_id) REFERENCES edital(id) ON DELETE CASCADE,
    FOREIGN KEY (servico_id) REFERENCES servico(id)
);

CREATE TABLE IF NOT EXISTS user_account (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('ADMIN', 'PMO', 'COORDENADOR', 'GERAL')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS theme_request (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requested_theme TEXT NOT NULL,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'PENDENTE' CHECK (status IN ('PENDENTE', 'EM ANÁLISE', 'CONCLUÍDA', 'REJEITADA')),
    requested_by TEXT NOT NULL,
    requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_by TEXT,
    reviewed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_edital_tema ON edital(tema_id);
CREATE INDEX IF NOT EXISTS idx_edital_subtema ON edital(subtema_id);
CREATE INDEX IF NOT EXISTS idx_edital_estado ON edital(estado_id);
CREATE INDEX IF NOT EXISTS idx_edital_municipio ON edital(municipio_id);
CREATE INDEX IF NOT EXISTS idx_edital_tipo ON edital(tipo_edital_id);
CREATE INDEX IF NOT EXISTS idx_edital_data ON edital(data_edital);
CREATE INDEX IF NOT EXISTS idx_user_role ON user_account(role);
CREATE INDEX IF NOT EXISTS idx_request_status ON theme_request(status);

DROP VIEW IF EXISTS vw_consulta_editais;

CREATE VIEW vw_consulta_editais AS
SELECT
    e.id,
    t.nome AS tema,
    st.nome AS subtema,
    p.nome AS pais,
    es.nome AS estado,
    m.nome AS municipio,
    e.nome_edital,
    e.descricao,
    e.esforco,
    u.nome AS unidade,
    e.prazo_meses,
    te.nome AS tipo_edital,
    e.codigo_planilha,
    fd.nome AS fonte_dado,
    e.observacao,
    e.custo_execucao,
    e.data_edital,
    e.metodo_calculo,
    e.valor_min,
    e.valor_max,
    COALESCE((
        SELECT GROUP_CONCAT(s.nome, ', ')
        FROM edital_servico esv
        JOIN servico s ON s.id = esv.servico_id
        WHERE esv.edital_id = e.id
        ORDER BY s.nome
    ), '') AS servicos
FROM edital e
LEFT JOIN tema t ON t.id = e.tema_id
LEFT JOIN subtema st ON st.id = e.subtema_id
LEFT JOIN pais p ON p.id = e.pais_id
LEFT JOIN estado es ON es.id = e.estado_id
LEFT JOIN municipio m ON m.id = e.municipio_id
LEFT JOIN unidade u ON u.id = e.unidade_id
LEFT JOIN tipo_edital te ON te.id = e.tipo_edital_id
LEFT JOIN fonte_dado fd ON fd.id = e.fonte_dado_id;
