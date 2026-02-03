import os
import zipfile
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PASTA_RAW = os.path.join(BASE_DIR, "data", "raw")
PASTA_EXTRACTED = os.path.join(BASE_DIR, "data", "extracted")

os.makedirs(PASTA_EXTRACTED, exist_ok=True)


def extrair_zip(caminho_zip, pasta_destino):
    
    try:
        with zipfile.ZipFile(caminho_zip, "r") as zip_ref:
            zip_ref.extractall(pasta_destino)
        return True
    except zipfile.BadZipFile:
        logging.error(
            f"Arquivo ZIP corrompido ou inválido: {os.path.basename(caminho_zip)}"
        )
        return False


arquivos_zip = [
    arquivo for arquivo in os.listdir(PASTA_RAW)
    if arquivo.lower().endswith(".zip")
]

if not arquivos_zip:
    logging.warning("Nenhum arquivo ZIP encontrado em data/raw")
else:
    for arquivo_zip in arquivos_zip:
        nome_trimestre = arquivo_zip.replace(".zip", "")
        caminho_zip = os.path.join(PASTA_RAW, arquivo_zip)

        pasta_destino = os.path.join(PASTA_EXTRACTED, nome_trimestre)
        os.makedirs(pasta_destino, exist_ok=True)

        sucesso = extrair_zip(caminho_zip, pasta_destino)

        if sucesso:
            logging.info(
                f"{arquivo_zip} extraído com sucesso para data/extracted/{nome_trimestre}"
            )
        else:
            logging.warning(
                f"{arquivo_zip} ignorado devido a erro na extração"
            )
