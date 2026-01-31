import logging
import zipfile
from pathlib import Path
import pandas as pd

# Configuração de logging para visibilidade do processo
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def main():
    logging.info("🚀 INICIANDO CONSOLIDAÇÃO DE DADOS")

    # Definição de caminhos (ajustado para subir 1 nível da pasta scripts/src)
    raiz_projeto = Path(__file__).resolve().parents[1]
    pasta_processed = raiz_projeto / "data" / "processed"
    pasta_output = raiz_projeto / "data" / "consolidated"

    if not pasta_processed.exists():
        logging.error(f"Pasta não encontrada: {pasta_processed}")
        return

    pasta_output.mkdir(parents=True, exist_ok=True)

    # Coleta de arquivos seguindo o padrão clean_*.csv
    arquivos = list(pasta_processed.glob("padronizado*.csv"))

    if not arquivos:
        logging.error("Nenhum arquivo 'clean_*.csv' encontrado para processar.")
        return

    lista_dataframes = []

    for arquivo in arquivos:
        logging.info(f"Processando: {arquivo.name}")
        
        # Leitura com dtypes definidos para evitar surpresas
        df = pd.read_csv(arquivo, dtype={"REG_ANS": str, "VL_SALDO_FINAL": str}, sep=None, engine='python')

        # Validação de colunas mínimas
        colunas_necessarias = {"DATA", "REG_ANS", "VL_SALDO_FINAL"}
        if not colunas_necessarias.issubset(df.columns):
            logging.warning(f"Campos ausentes em {arquivo.name}. Pulando...")
            continue

        # --- TRANSFORMAÇÕES ---
        
        # 1. Tratamento de Data e Extração Temporal
        df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce")
        df = df.dropna(subset=["DATA"]) # Remove registros sem data válida
        
        df["Ano"] = df["DATA"].dt.year.astype(int)
        df["Trimestre"] = df["DATA"].dt.quarter.astype(str) + "T"

        # 2. Conversão Numérica (Lidando com separadores brasileiros)
        df["ValorDespesas"] = (
            df["VL_SALDO_FINAL"]
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        df["ValorDespesas"] = pd.to_numeric(df["ValorDespesas"], errors="coerce").fillna(0.0)

        # 3. Mapeamento para o Schema Alvo
        df_temp = pd.DataFrame({
            "RegistroANS": df["REG_ANS"],
            "CNPJ": None,           # Preparado para enriquecimento
            "RazaoSocial": None,    # Preparado para enriquecimento
            "Trimestre": df["Trimestre"],
            "Ano": df["Ano"],
            "ValorDespesas": df["ValorDespesas"]
        })

        lista_dataframes.append(df_temp)

    if not lista_dataframes:
        logging.error("Nenhum dado processável encontrado.")
        return

    # --- CONSOLIDAÇÃO FINAL ---
    
    # Consolidação incremental via concat
    df_consolidado = pd.concat(lista_dataframes, ignore_index=True)

    # Agrupamento para garantir unicidade e somar valores de despesas se houver duplicatas de chave
    df_consolidado = (
        df_consolidado
        .groupby(["RegistroANS", "CNPJ", "RazaoSocial", "Trimestre", "Ano"], dropna=False)
        .agg({"ValorDespesas": "sum"})
        .reset_index()
    )

    # Ordenação lógica: Recentes primeiro
    df_consolidado = df_consolidado.sort_values(by=["Ano", "Trimestre", "RegistroANS"], ascending=[False, False, True])

    # --- EXPORTAÇÃO ---
    
    caminho_csv = pasta_output / "consolidado_despesas.csv"
    df_consolidado.to_csv(caminho_csv, index=False, encoding="utf-8")
    
    logging.info(f"✅ CSV gerado em: {caminho_csv}")

    # Compactação para economia de espaço/transferência
    caminho_zip = pasta_output / "consolidado_despesas.zip"
    with zipfile.ZipFile(caminho_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(caminho_csv, arcname="consolidado_despesas.csv")

    logging.info(f"📦 ZIP concluído: {caminho_zip.name}")

if __name__ == "__main__":
    main()