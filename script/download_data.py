import requests
import os
import re

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pasta_destino = os.path.join(base_dir, "data", "raw")

os.makedirs(pasta_destino, exist_ok=True)

url_base = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/"

def obter_html(url):
    resposta = requests.get(url, timeout=30)
    resposta.raise_for_status()
    return resposta.text

def extrair_links(html):
    return re.findall(r'href="([^"]+)"', html)

def baixar_arquivo(url_arquivo, caminho_destino):
    resposta = requests.get(url_arquivo, timeout=30)
    
    if resposta.status_code == 200:
        with open(caminho_destino, "wb") as arquivo:
            arquivo.write(resposta.content)
        print(f"✔ Baixado: {caminho_destino}")


html_base = obter_html(url_base)
links_base = extrair_links(html_base)

anos = sorted(
    [link.replace("/", "") for link in links_base if link.endswith("/") and link[:4].isdigit()],
    reverse=True
)

trimestres_encontrados = []


for ano in anos:
    url_ano = f"{url_base}{ano}/"
    html_ano = obter_html(url_ano)
    links_ano = extrair_links(html_ano)

    arquivos_zip = [link for link in links_ano if link.lower().endswith(".zip")]

    for nome_arquivo in arquivos_zip:
        match = re.match(r"([1-4]T)(\d{4})\.zip", nome_arquivo)

        if match:
            trimestre = match.group(1)
            ano_arquivo = match.group(2)

            trimestres_encontrados.append({
                "ano": ano_arquivo,
                "trimestre": trimestre,
                "arquivo": nome_arquivo
            })

ordem_trimestre = {"1T": 1, "2T": 2, "3T": 3, "4T": 4}

trimestres_encontrados.sort(
    key=lambda x: (int(x["ano"]), ordem_trimestre[x["trimestre"]]),
    reverse=True
)

ultimos_trimestres = trimestres_encontrados[:3]

print("\nTrimestres selecionados:")

for item in ultimos_trimestres:
    print(f"- {item['trimestre']}{item['ano']} ({item['arquivo']})")

for item in ultimos_trimestres:
    url_arquivo = f"{url_base}{item['ano']}/{item['arquivo']}"
    caminho_arquivo = os.path.join(pasta_destino, item["arquivo"])
    baixar_arquivo(url_arquivo, caminho_arquivo)
