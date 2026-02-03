import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def carregar_sql(arquivo_sql: Path) -> str:
    """Lê o conteúdo de um arquivo SQL."""
    with arquivo_sql.open("r", encoding="utf-8") as f:
        return f.read()


def executar_sql(conn, arquivo_sql: Path):
    """Executa um arquivo SQL no PostgreSQL."""
    logging.info(f"Executando: {arquivo_sql.name}")
    sql = carregar_sql(arquivo_sql)

    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def main():

    BASE_DIR = Path(__file__).resolve().parents[1]
    SQL_DIR = BASE_DIR / "sql"

    logging.info(f" Raiz do projeto: {BASE_DIR}")
    logging.info(f" Pasta SQL: {SQL_DIR}")

    if not SQL_DIR.exists():
        raise FileNotFoundError(
            f"Pasta SQL não encontrada: {SQL_DIR}\n"
            "Crie a pasta database/sql e adicione os arquivos .sql."
        )

    load_dotenv()

    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        raise EnvironmentError(
            "Variáveis de ambiente do banco não configuradas corretamente.\n"
            "Verifique o arquivo .env"
        )

    logging.info("Conectando ao PostgreSQL...")

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    logging.info("Conexão estabelecida com sucesso")

    ordem_execucao = [
        "create_tables.sql",      
        "import_data.sql",      
        "analytics.sql"   
    ]

    for nome_arquivo in ordem_execucao:
        caminho_sql = SQL_DIR / nome_arquivo

        if not caminho_sql.exists():
            logging.warning(f"Arquivo não encontrado: {nome_arquivo} — pulando")
            continue

        executar_sql(conn, caminho_sql)

    conn.close()
    logging.info(" Execução SQL finalizada com sucesso")

if __name__ == "__main__":
    main()
