import csv
import logging
import shutil
import unicodedata
from pathlib import Path
import pandas as pd
import re

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = texto.encode("ASCII", "ignore").decode("ASCII")
    texto = texto.lower()
    texto = texto.replace(" / ", "/").replace("/ ", "/").replace(" /", "/")
    return texto.strip()

def converter_valor_numerico(valor):
   
    if pd.isna(valor) or str(valor).strip() == "":
        return 0.0
    try:
        valor_limpo = str(valor).replace(".", "").replace(",", ".")
        return float(valor_limpo)
    except ValueError:
        return 0.0

def buscar_linhas_csv_txt(caminho_arquivo: Path, termo_normalizado: str):
    linhas_encontradas = []
    try:
        with caminho_arquivo.open("r", encoding="latin1", errors="replace") as f:
            leitor = csv.reader(f, delimiter=";")
            for numero_linha, linha in enumerate(leitor, start=1):
                for campo in linha:
                    if termo_normalizado in normalizar_texto(campo):
                        linhas_encontradas.append((numero_linha, linha))
                        break
    except Exception as erro:
        logging.error(f"Erro ao ler {caminho_arquivo.name}: {erro}")
    return linhas_encontradas

def buscar_linhas_xlsx(caminho_arquivo: Path, termo_normalizado: str):
    linhas_encontradas = []
    try:
        df = pd.read_excel(caminho_arquivo, dtype=str)
        for indice, linha in df.iterrows():
            for valor in linha.values:
                if termo_normalizado in normalizar_texto(str(valor)):
                    linhas_encontradas.append((indice + 2, linha.tolist()))
                    break
    except Exception as erro:
        logging.error(f"Erro ao ler {caminho_arquivo.name}: {erro}")
    return linhas_encontradas

def buscar_despesas_por_formato(caminho_arquivo: Path, termo_normalizado: str):
    extensao = caminho_arquivo.suffix.lower()
    if extensao in [".csv", ".txt"]:
        return buscar_linhas_csv_txt(caminho_arquivo, termo_normalizado)
    if extensao == ".xlsx":
        return buscar_linhas_xlsx(caminho_arquivo, termo_normalizado)
    return []

def extrair_metadados_pasta(caminho_arquivo: Path):
    pasta_pai = caminho_arquivo.parent.name

    match = re.search(r"([1-4]T)(\d{4})", pasta_pai, re.IGNORECASE)
    if match:
        return match.group(2), match.group(1).upper()

    match_invertido = re.search(r"(\d{4}).*([1-4]T)", pasta_pai, re.IGNORECASE)
    if match_invertido:
        return match_invertido.group(1), match_invertido.group(2).upper()

    return "0000", "UNK"

def linha_contem_despesa(row, termo_busca):
    texto_linha = " ".join(row.astype(str).values)
    return termo_busca in normalizar_texto(texto_linha)

def main():
    logging.info("INÍCIO DO PROCESSAMENTO")

    raiz_projeto = Path(__file__).resolve().parents[1]
    pasta_extracted = raiz_projeto / "data" / "extracted"
    pasta_processed = raiz_projeto / "data" / "processed"

    if not pasta_extracted.exists():
        logging.error(f"Pasta não encontrada: {pasta_extracted}")
        return

    pasta_processed.mkdir(parents=True, exist_ok=True)

    termo_busca = normalizar_texto("Despesas com Eventos/Sinistros")

    arquivos = list(pasta_extracted.rglob("*"))
    arquivos_validos = 0

    for arquivo in arquivos:
        if arquivo.suffix.lower() not in [".csv", ".txt", ".xlsx"]:
            continue

        logging.info(f"Analisando arquivo: {arquivo}")

        linhas = buscar_despesas_por_formato(arquivo, termo_busca)

        if not linhas:
            logging.info(f"✖ Ignorado: {arquivo.name}")
            continue

        logging.info(f"✔ Arquivo ENCONTRADO: {arquivo.name}")

        try:
            if arquivo.suffix == ".xlsx":
                df = pd.read_excel(arquivo, dtype=str)
            else:
                df = pd.read_csv(
                    arquivo,
                    sep=";",
                    encoding="latin1",
                    encoding_errors="replace",
                    dtype=str,
                    on_bad_lines="skip"
                )

            # FILTRO EFETIVO DAS LINHAS DE DESPESA
            df = df[df.apply(lambda row: linha_contem_despesa(row, termo_busca), axis=1)]

            if df.empty:
                logging.warning(f"⚠ Nenhuma linha válida após filtragem em {arquivo.name}")
                continue

            colunas_valor = [c for c in df.columns if str(c).upper().startswith("VL_")]

            for col in colunas_valor:
                df[col] = df[col].apply(converter_valor_numerico)

            ano, trimestre = extrair_metadados_pasta(arquivo)
            df["ano"] = ano
            df["trimestre"] = trimestre

            nome_novo = f"padronizado_{ano}_{trimestre}_{arquivo.stem}.csv"
            destino = pasta_processed / nome_novo

            df.to_csv(destino, index=False, encoding="utf-8", sep=",")

            arquivos_validos += 1
            logging.info(f"   ↳ Transformado e salvo em: {destino.name}")

        except Exception as e:
            logging.error(f"Erro crítico ao transformar {arquivo.name}: {e}")
            shutil.copy2(arquivo, pasta_processed / arquivo.name)

    logging.info("PROCESSAMENTO FINALIZADO")
    logging.info(f"Total de arquivos transformados com sucesso: {arquivos_validos}")

if __name__ == "__main__":
    main()
