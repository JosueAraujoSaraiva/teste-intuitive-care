import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

from pathlib import Path
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

def _get_env(name: str, default: str | None = None) -> str:
    val = os.getenv(name, default)
    if val is None or str(val).strip() == "":
        raise RuntimeError(f"Variável de ambiente ausente: {name}")
    return str(val)

def get_dsn() -> str:
    host = _get_env("DB_HOST")
    port = _get_env("DB_PORT", "5432")
    dbname = _get_env("DB_NAME")
    user = _get_env("DB_USER")
    password = _get_env("DB_PASSWORD")
    return f"host={host} port={port} dbname={dbname} user={user} password={password}"

@contextmanager
def get_conn():
    conn = psycopg2.connect(get_dsn(), cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def fetch_all(sql: str, params: tuple = ()):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

def fetch_one(sql: str, params: tuple = ()):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()
