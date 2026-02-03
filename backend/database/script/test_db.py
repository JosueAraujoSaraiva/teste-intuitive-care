from connection import get_connection

def main():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        print("✅ Conexão OK. Resultado:", cur.fetchone()[0])
        cur.close()
        conn.close()
    except Exception as e:
        print("❌ Falha na conexão:")
        print(e)

if __name__ == "__main__":
    main()
