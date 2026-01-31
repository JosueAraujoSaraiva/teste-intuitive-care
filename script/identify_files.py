import csv
import logging
import shutil
import unicodedata
from pathlib import Path

import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""

    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ASCII", "ignore").decode("ASCII")
    texto = texto.lower()
    texto = texto.replace(" / ", "/").replace("/ ", "/").replace(" /", "/")
    return texto.strip()


def buscar_linhas_csv_txt(caminho_arquivo: Path, termo_normalizado: str):
    linhas_encontradas = []

    try:
        with caminho_arquivo.open("r", encoding="utf-8", errors="ignore") as f:
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

        if linhas:
            destino = pasta_processed / arquivo.name
            shutil.copy2(arquivo, destino)
            arquivos_validos += 1

            logging.info(f"✔ Arquivo COPIADO para processed: {arquivo.name}")
            logging.info(f"↳ {len(linhas)} ocorrência(s) encontrada(s):")

            for numero_linha, conteudo in linhas:
                logging.info(f"   Linha {numero_linha}: {conteudo}")

        else:
            logging.info(f"✖ Ignorado (não contém despesas): {arquivo.name}")

    logging.info("PROCESSAMENTO FINALIZADO")
    logging.info(f"Total de arquivos válidos: {arquivos_validos}")


if __name__ == "__main__":
    main()
