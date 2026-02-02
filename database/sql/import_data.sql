BEGIN;

-- =========================================================
-- 3.3 IMPORTAÇÃO COM STAGING + TRATAMENTO (PostgreSQL >10)
--
-- Arquivos:
--  - data/consolidated/consolidado_despesas.csv (UTF-8, delimiter ',')
--  - data/final/despesas_agregadas.csv         (UTF-8, delimiter ',')
--  - data/processed/dados_cadastrais_operadoras.csv (delimiter ';', geralmente LATIN1)
--
-- Estratégia:
-- 1) Carrega bruto em tabelas staging (tudo TEXT)
-- 2) Insere nas tabelas finais convertendo tipos e tratando inconsistências
--
-- Tratamentos documentados:
-- - NULL em campos obrigatórios:
--     * operadoras: rejeita se registro_ans ou cnpj vazios
--     * consolidadas: rejeita se RegistroANS, Trimestre ou Ano vazios
--     * agregadas: rejeita se RegistroANS vazio
-- - Strings em campos numéricos:
--     * consolidadas: tenta conversão; se falhar -> 0.00
--     * agregadas: tenta conversão; se falhar -> NULL (métrica derivada)
-- - Datas inconsistentes:
--     * No cadastro, Data_Registro_ANS fica em staging (TEXT) para documentação.
--       Se precisar normalizar, fazer ETL específico com TO_DATE (não exigido no 3.4).
-- =========================================================

-- =========================================================
-- 0) STAGING
-- =========================================================

DROP TABLE IF EXISTS stg_consolidado_despesas;
DROP TABLE IF EXISTS stg_despesas_agregadas;
DROP TABLE IF EXISTS stg_operadoras;

CREATE TABLE stg_consolidado_despesas (
  RegistroANS   TEXT,
  CNPJ          TEXT,
  RazaoSocial   TEXT,
  Trimestre     TEXT,
  Ano           TEXT,
  ValorDespesas TEXT
);

CREATE TABLE stg_despesas_agregadas (
  RegistroANS      TEXT,
  CNPJ             TEXT,
  RazaoSocial      TEXT,
  UF               TEXT,
  Modalidade       TEXT,
  Total_Despesas   TEXT,
  Media_Trimestral TEXT,
  Desvio_Padrao    TEXT
);

CREATE TABLE stg_operadoras (
  REGISTRO_OPERADORA        TEXT,
  CNPJ                      TEXT,
  Razao_Social              TEXT,
  Nome_Fantasia             TEXT,
  Modalidade                TEXT,
  Logradouro                TEXT,
  Numero                    TEXT,
  Complemento               TEXT,
  Bairro                    TEXT,
  Cidade                    TEXT,
  UF                        TEXT,
  CEP                       TEXT,
  DDD                       TEXT,
  Telefone                  TEXT,
  Fax                       TEXT,
  Endereco_eletronico       TEXT,
  Representante             TEXT,
  Cargo_Representante       TEXT,
  Regiao_de_Comercializacao TEXT,
  Data_Registro_ANS         TEXT
);

-- =========================================================
-- 1) IMPORTAÇÃO (COPY)
-- =========================================================
-- Observação Windows:
-- - COPY lê do servidor do PostgreSQL e pode falhar por permissão/caminho.
-- - No psql, prefira \copy (client-side).
--
-- Exemplos (psql):
-- \copy stg_consolidado_despesas FROM 'C:/.../data/consolidated/consolidado_despesas.csv' CSV HEADER DELIMITER ',' ENCODING 'UTF8';
-- \copy stg_despesas_agregadas   FROM 'C:/.../data/final/despesas_agregadas.csv'       CSV HEADER DELIMITER ',' ENCODING 'UTF8';
-- \copy stg_operadoras           FROM 'C:/.../data/processed/dados_cadastrais_operadoras.csv' CSV HEADER DELIMITER ';' ENCODING 'LATIN1';

-- =========================================================
-- 2) CARGA NAS TABELAS FINAIS (com tratamento)
-- =========================================================

-- ---------------------------------------------------------
-- (A) OPERADORAS
-- ---------------------------------------------------------
-- Regras:
-- - registro_ans e cnpj obrigatórios (rejeita linhas sem ambos)
-- - cnpj é normalizado para apenas dígitos
-- - uf em uppercase
-- - cnpj_valido: não existe no CSV -> NULL (pode ser preenchido depois por ETL)
INSERT INTO despesas_consolidadas (registro_ans, cnpj, razao_social, trimestre, ano, valor_despesas)
SELECT
  NULLIF(TRIM(RegistroANS), '') AS registro_ans,
  NULLIF(regexp_replace(CNPJ, '[^0-9]', '', 'g'), '') AS cnpj,
  NULLIF(TRIM(RazaoSocial), '') AS razao_social,
  NULLIF(UPPER(TRIM(Trimestre)), '')::CHAR(2) AS trimestre,
  NULLIF(TRIM(Ano), '')::INTEGER AS ano,
  CASE
    WHEN ValorDespesas IS NULL OR TRIM(ValorDespesas) = '' THEN 0::NUMERIC(18,2)
    ELSE
      CASE
        WHEN regexp_replace(ValorDespesas, '[^0-9,.-]', '', 'g') ~ '^-?[0-9\.,]+$' THEN
          ROUND(REPLACE(REPLACE(regexp_replace(ValorDespesas, '[^0-9,.-]', '', 'g'), '.', ''), ',', '.')::NUMERIC, 2)
        ELSE 0::NUMERIC(18,2)
      END
  END AS valor_despesas
FROM stg_consolidado_despesas
WHERE NULLIF(TRIM(RegistroANS), '') IS NOT NULL; -- Rejeição de Nulos

-- ---------------------------------------------------------
-- (B) DESPESAS CONSOLIDADAS  ✅ (aqui estava o erro do WHERE)
-- ---------------------------------------------------------
-- Regras:
-- - RegistroANS, Trimestre, Ano obrigatórios (rejeita se ausentes)
-- - ValorDespesas:
--   * tenta converter "1.234,56" / "1234.56"
--   * se falhar -> 0.00
INSERT INTO despesas_consolidadas (registro_ans, cnpj, razao_social, trimestre, ano, valor_despesas)
SELECT
  NULLIF(TRIM(RegistroANS), '') AS registro_ans,
  NULLIF(regexp_replace(CNPJ, '[^0-9]', '', 'g'), '') AS cnpj,
  NULLIF(TRIM(RazaoSocial), '') AS razao_social,
  NULLIF(UPPER(TRIM(Trimestre)), '')::CHAR(2) AS trimestre,
  NULLIF(TRIM(Ano), '')::INTEGER AS ano,
  CASE
    WHEN ValorDespesas IS NULL OR TRIM(ValorDespesas) = '' THEN 0::NUMERIC(18,2)
    ELSE
      CASE
        WHEN regexp_replace(ValorDespesas, '[^0-9,.-]', '', 'g') ~ '^-?[0-9\.,]+$' THEN
          ROUND(
            REPLACE(
              REPLACE(regexp_replace(ValorDespesas, '[^0-9,.-]', '', 'g'), '.', ''),
              ',', '.'
            )::NUMERIC,
            2
          )
        ELSE 0::NUMERIC(18,2)
      END
  END AS valor_despesas
FROM stg_consolidado_despesas
WHERE
  NULLIF(TRIM(RegistroANS), '') IS NOT NULL
  AND NULLIF(TRIM(Trimestre), '') IS NOT NULL
  AND NULLIF(TRIM(Ano), '') IS NOT NULL;

-- ---------------------------------------------------------
-- (C) DESPESAS AGREGADAS
-- ---------------------------------------------------------
-- Regras:
-- - RegistroANS obrigatório (rejeita se ausente)
-- - Numéricos: tenta converter; se falhar -> NULL (métrica derivada)
INSERT INTO despesas_agregadas (
  registro_ans, cnpj, razao_social, uf, modalidade,
  total_despesas, media_trimestral, desvio_padrao
)
SELECT
  NULLIF(TRIM(RegistroANS), '') AS registro_ans,
  NULLIF(regexp_replace(CNPJ, '[^0-9]', '', 'g'), '') AS cnpj,
  NULLIF(TRIM(RazaoSocial), '') AS razao_social,
  NULLIF(UPPER(TRIM(UF)), '')::CHAR(2) AS uf,
  NULLIF(TRIM(Modalidade), '') AS modalidade,

  CASE
    WHEN Total_Despesas IS NULL OR TRIM(Total_Despesas) = '' THEN NULL
    WHEN regexp_replace(Total_Despesas, '[^0-9,.-]', '', 'g') ~ '^-?[0-9\.,]+$' THEN
      ROUND(REPLACE(REPLACE(regexp_replace(Total_Despesas, '[^0-9,.-]', '', 'g'), '.', ''), ',', '.')::NUMERIC, 2)
    ELSE NULL
  END AS total_despesas,

  CASE
    WHEN Media_Trimestral IS NULL OR TRIM(Media_Trimestral) = '' THEN NULL
    WHEN regexp_replace(Media_Trimestral, '[^0-9,.-]', '', 'g') ~ '^-?[0-9\.,]+$' THEN
      ROUND(REPLACE(REPLACE(regexp_replace(Media_Trimestral, '[^0-9,.-]', '', 'g'), '.', ''), ',', '.')::NUMERIC, 2)
    ELSE NULL
  END AS media_trimestral,

  CASE
    WHEN Desvio_Padrao IS NULL OR TRIM(Desvio_Padrao) = '' THEN NULL
    WHEN regexp_replace(Desvio_Padrao, '[^0-9,.-]', '', 'g') ~ '^-?[0-9\.,]+$' THEN
      ROUND(REPLACE(REPLACE(regexp_replace(Desvio_Padrao, '[^0-9,.-]', '', 'g'), '.', ''), ',', '.')::NUMERIC, 2)
    ELSE NULL
  END AS desvio_padrao

FROM stg_despesas_agregadas
WHERE
  NULLIF(TRIM(RegistroANS), '') IS NOT NULL;

COMMIT;
