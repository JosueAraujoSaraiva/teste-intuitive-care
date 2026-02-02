import logging
from pathlib import Path
from connection import get_connection

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"
PROJECT_ROOT = ROOT.parent
CSV_MAP = {
    "stg_consolidado_despesas": (PROJECT_ROOT / "data" / "consolidated" / "consolidado_despesas.csv", ",", "utf-8"),
    "stg_despesas_agregadas": (PROJECT_ROOT / "data" / "final" / "despesas_agregadas.csv", ",", "utf-8"),
    "stg_operadoras": (PROJECT_ROOT / "data" / "processed" / "dados_cadastrais_operadoras.csv", ";", "latin1")
}

def execute_sql_file(filename):
    path = SQL_DIR / filename
    logging.info(f"Executando {filename}...")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(path.read_text(encoding="utf-8"))
        conn.commit()

def main():
    # 1. Cria tabelas e limpa staging
    execute_sql_file("create_tables.sql")
    
    # 2. Carga via COPY (Alta performance para grandes volumes)
    for table, (path, delim, enc) in CSV_MAP.items():
        copy_sql = f"COPY {table} FROM STDIN WITH (FORMAT csv, HEADER true, DELIMITER '{delim}')"
        with get_connection() as conn:
            with conn.cursor() as cur:
                with path.open("r", encoding=enc, errors="replace") as f:
                    cur.copy_expert(copy_sql, f)
            conn.commit()
        logging.info(f"Carga concluída: {table}")

   
    execute_sql_file("import_data.sql")
    execute_sql_file("analytics.sql")
    print(" Pipeline finalizado com sucesso!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()