from pathlib import Path
import logging
from connection import get_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def find_project_root(start: Path) -> Path:
    """
    Sobe diretórios até encontrar um diretório que contenha:
    - pasta 'data'
    - arquivo 'README.md'
    Isso torna o script robusto independente de estar em /dataBase/scripts.
    """
    p = start.resolve()
    for parent in [p] + list(p.parents):
        if (parent / "data").exists() and (parent / "README.md").exists():
            return parent
   
    return p.parents[2]


PROJECT_ROOT = find_project_root(Path(__file__))
DATA_DIR = PROJECT_ROOT / "data"

# Caminhos CORRETOS usando DATA_DIR
CSV_CONSOLIDADO = DATA_DIR / "consolidated" / "consolidado_despesas.csv"
CSV_AGREGADAS   = DATA_DIR / "final" / "despesas_agregadas.csv"
CSV_CADASTRO    = DATA_DIR / "processed" / "dados_cadastrais_operadoras.csv"

STAGING_SQL = """
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
"""

POPULATE_SQL = """
-- Limpa tabelas finais (para rodar quantas vezes quiser, sem duplicar)
TRUNCATE TABLE despesas_consolidadas;
TRUNCATE TABLE despesas_agregadas;
TRUNCATE TABLE operadoras;

-- (A) OPERADORAS
INSERT INTO operadoras (registro_ans, cnpj, razao_social, uf, modalidade, cnpj_valido)
SELECT
  NULLIF(TRIM(REGISTRO_OPERADORA), '') AS registro_ans,
  NULLIF(regexp_replace(CNPJ, '[^0-9]', '', 'g'), '') AS cnpj,
  NULLIF(TRIM(Razao_Social), '') AS razao_social,
  NULLIF(UPPER(TRIM(UF)), '')::CHAR(2) AS uf,
  NULLIF(TRIM(Modalidade), '') AS modalidade,
  NULL::BOOLEAN AS cnpj_valido
FROM stg_operadoras
WHERE
  NULLIF(TRIM(REGISTRO_OPERADORA), '') IS NOT NULL
  AND NULLIF(regexp_replace(CNPJ, '[^0-9]', '', 'g'), '') IS NOT NULL
ON CONFLICT (registro_ans) DO UPDATE
SET
  cnpj = EXCLUDED.cnpj,
  razao_social = COALESCE(EXCLUDED.razao_social, operadoras.razao_social),
  uf = COALESCE(EXCLUDED.uf, operadoras.uf),
  modalidade = COALESCE(EXCLUDED.modalidade, operadoras.modalidade);

-- (B) DESPESAS CONSOLIDADAS
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
        WHEN regexp_replace(ValorDespesas, '[^0-9,.-]', '', 'g') ~ '^-?[0-9\\.,]+$' THEN
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

-- (C) DESPESAS AGREGADAS
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
    WHEN regexp_replace(Total_Despesas, '[^0-9,.-]', '', 'g') ~ '^-?[0-9\\.,]+$' THEN
      ROUND(REPLACE(REPLACE(regexp_replace(Total_Despesas, '[^0-9,.-]', '', 'g'), '.', ''), ',', '.')::NUMERIC, 2)
    ELSE NULL
  END AS total_despesas,

  CASE
    WHEN Media_Trimestral IS NULL OR TRIM(Media_Trimestral) = '' THEN NULL
    WHEN regexp_replace(Media_Trimestral, '[^0-9,.-]', '', 'g') ~ '^-?[0-9\\.,]+$' THEN
      ROUND(REPLACE(REPLACE(regexp_replace(Media_Trimestral, '[^0-9,.-]', '', 'g'), '.', ''), ',', '.')::NUMERIC, 2)
    ELSE NULL
  END AS media_trimestral,

  CASE
    WHEN Desvio_Padrao IS NULL OR TRIM(Desvio_Padrao) = '' THEN NULL
    WHEN regexp_replace(Desvio_Padrao, '[^0-9,.-]', '', 'g') ~ '^-?[0-9\\.,]+$' THEN
      ROUND(REPLACE(REPLACE(regexp_replace(Desvio_Padrao, '[^0-9,.-]', '', 'g'), '.', ''), ',', '.')::NUMERIC, 2)
    ELSE NULL
  END AS desvio_padrao
FROM stg_despesas_agregadas
WHERE
  NULLIF(TRIM(RegistroANS), '') IS NOT NULL;
"""

def _assert_exists(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {path}")


def copy_to_table(table: str, csv_path: Path, delimiter: str, encoding: str):
    _assert_exists(csv_path)

    copy_sql = f"COPY {table} FROM STDIN WITH (FORMAT csv, HEADER true, DELIMITER '{delimiter}')"

    with get_connection() as conn:
        with conn.cursor() as cur:
            with csv_path.open("r", encoding=encoding, errors="replace", newline="") as f:
                cur.copy_expert(copy_sql, f)
        conn.commit()

    logging.info(f"COPY concluído: {table} <- {csv_path.name}")


def fetch_counts():
    q = """
    SELECT 'operadoras' AS tabela, COUNT(*) FROM operadoras
    UNION ALL SELECT 'despesas_consolidadas', COUNT(*) FROM despesas_consolidadas
    UNION ALL SELECT 'despesas_agregadas', COUNT(*) FROM despesas_agregadas
    UNION ALL SELECT 'stg_operadoras', COUNT(*) FROM stg_operadoras
    UNION ALL SELECT 'stg_consolidado_despesas', COUNT(*) FROM stg_consolidado_despesas
    UNION ALL SELECT 'stg_despesas_agregadas', COUNT(*) FROM stg_despesas_agregadas;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(q)
            return cur.fetchall()


def main():
    logging.info(f"Raiz do projeto: {PROJECT_ROOT}")
    logging.info(f"Data dir: {DATA_DIR}")
    logging.info(f"CSV consolidado: {CSV_CONSOLIDADO}")
    logging.info(f"CSV agregadas:   {CSV_AGREGADAS}")
    logging.info(f"CSV cadastro:    {CSV_CADASTRO}")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(STAGING_SQL)
        conn.commit()

    copy_to_table("stg_consolidado_despesas", CSV_CONSOLIDADO, delimiter=",", encoding="utf-8")
    copy_to_table("stg_despesas_agregadas", CSV_AGREGADAS, delimiter=",", encoding="utf-8")
    copy_to_table("stg_operadoras", CSV_CADASTRO, delimiter=";", encoding="latin1")

    # 3) Popular tabelas finais com tratamento
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(POPULATE_SQL)
        conn.commit()

    # 4) Mostrar contagens
    print("\nContagens após carga:")
    for row in fetch_counts():
        print(row)


if __name__ == "__main__":
    main()
