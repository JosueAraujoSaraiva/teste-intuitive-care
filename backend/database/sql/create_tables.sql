-- JUSTIFICATIVA TÉCNICA (Item 3.2): 
-- Abordagem: Opção B (Normalizada). 
-- Justificativa: Reduz redundância de dados cadastrais em milhões de registros de despesas, 
-- facilitando a manutenção e garantindo integridade referencial.
-- Tipos de Dados: NUMERIC(18,2) para valores monetários (garante precisão decimal que FLOAT não possui).
-- Tipos de Período: INTEGER/CHAR para Ano/Trimestre para facilitar filtros sem overhead de conversão de data complexa.

BEGIN;

CREATE TABLE IF NOT EXISTS operadoras (
    id            BIGSERIAL PRIMARY KEY,
    registro_ans  VARCHAR(20) NOT NULL UNIQUE,
    cnpj          VARCHAR(14) NOT NULL UNIQUE,
    razao_social  TEXT,
    uf            CHAR(2),
    modalidade    TEXT,
    cnpj_valido   BOOLEAN
);

CREATE TABLE IF NOT EXISTS despesas_consolidadas (
    id             BIGSERIAL PRIMARY KEY,
    registro_ans   VARCHAR(20) NOT NULL,
    cnpj           VARCHAR(14),
    razao_social   TEXT,
    trimestre      CHAR(2) NOT NULL,
    ano            INTEGER NOT NULL,
    valor_despesas NUMERIC(18,2) NOT NULL,
    CONSTRAINT ck_trimestre_valido CHECK (trimestre IN ('1T','2T','3T','4T')),
    CONSTRAINT ck_ano_valido CHECK (ano BETWEEN 2000 AND 2100)
);

CREATE TABLE IF NOT EXISTS despesas_agregadas (
    id               BIGSERIAL PRIMARY KEY,
    registro_ans     VARCHAR(20) NOT NULL,
    cnpj             VARCHAR(14),
    razao_social     TEXT,
    uf               CHAR(2),
    modalidade       TEXT,
    total_despesas   NUMERIC(18,2),
    media_trimestral NUMERIC(18,2),
    desvio_padrao    NUMERIC(18,2)
);

-- Índices para performance em queries analíticas (JOINs e Agrupamentos por UF/Registro)
CREATE INDEX IF NOT EXISTS idx_dc_periodo ON despesas_consolidadas (ano, trimestre);
CREATE INDEX IF NOT EXISTS idx_dc_registro ON despesas_consolidadas (registro_ans);
CREATE INDEX IF NOT EXISTS idx_operadoras_uf ON operadoras (uf);

COMMIT;