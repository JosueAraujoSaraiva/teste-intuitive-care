BEGIN;

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
-- INSERT (apenas 1, para evitar duplicidade)
-- =========================================================
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

-- =========================================================
-- INSERT agregadas (mantido como está)
-- =========================================================
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

-- =========================================================
-- CORREÇÃO PRINCIPAL: preencher CNPJ após os inserts (JOIN NORMALIZADO)
-- =========================================================
UPDATE despesas_consolidadas dc
SET cnpj = o.cnpj
FROM operadoras o
WHERE
  TRIM(dc.registro_ans::text) = TRIM(o.registro_ans::text)
  AND (dc.cnpj IS NULL OR TRIM(dc.cnpj) = '')
  AND o.cnpj IS NOT NULL
  AND TRIM(o.cnpj) <> '';

UPDATE despesas_agregadas da
SET cnpj = o.cnpj
FROM operadoras o
WHERE
  TRIM(da.registro_ans::text) = TRIM(o.registro_ans::text)
  AND (da.cnpj IS NULL OR TRIM(da.cnpj) = '')
  AND o.cnpj IS NOT NULL
  AND TRIM(o.cnpj) <> '';

COMMIT;
