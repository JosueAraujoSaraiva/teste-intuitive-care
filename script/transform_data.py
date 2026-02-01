import pandas as pd
import numpy as np
import logging
import requests
import io
import zipfile
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def obter_html(url):
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logging.error(f"Erro ao acessar diretório {url}: {e}")
        return ""

def extrair_links_csv(html):
    return re.findall(r'href=["\']([^"\']+\.csv)["\']', html, re.IGNORECASE)

def baixar_arquivo(url):
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.content

def limpar_numeros(valor):
    if pd.isna(valor): return ""
    return re.sub(r'[^0-9]', '', str(valor))

def validar_cnpj(cnpj_input):
    cnpj = limpar_numeros(cnpj_input)
    if len(cnpj) != 14 or len(set(cnpj)) == 1: return False

    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    def calc_digito(parte, pesos):
        soma = sum(int(a) * b for a, b in zip(parte, pesos))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    d1 = calc_digito(cnpj[:12], pesos1)
    d2 = calc_digito(cnpj[:13], pesos2)
    return str(d1) == cnpj[12] and str(d2) == cnpj[13]

def baixar_cadastro_operadoras():
    
    base_url = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/"
    
    try:
        logging.info("Acessando diretório da ANS para localizar CSV...")
        html = obter_html(base_url)
        
        links_csv = extrair_links_csv(html)
        
        if not links_csv:
            logging.warning("Nenhum CSV encontrado na listagem. Tentando nome padrão...")
            arquivo_escolhido = "Relatorio_cadop.csv"
        else:
            candidatos = [l for l in links_csv if "cadop" in l.lower() or "operadora" in l.lower()]
            
            if candidatos:
                arquivo_escolhido = candidatos[0] 
            else:
                arquivo_escolhido = links_csv[0] # Se não tiver nome padrão, pega o primeiro CSV que vir

        url_final = base_url + arquivo_escolhido
        logging.info(f"Baixando arquivo CSV identificado: {arquivo_escolhido}")
        
        conteudo = baixar_arquivo(url_final)
        
        # Leitura estritamente como CSV
        return pd.read_csv(
            io.BytesIO(conteudo),
            sep=";",
            encoding="latin1",
            dtype=str,
            on_bad_lines="skip"
        )
            
    except Exception as e:
        logging.error(f"Erro ao baixar cadastro: {e}")
        return None

def main():
    raiz = Path(__file__).resolve().parents[1]
    input_file = raiz / "data" / "consolidated" / "consolidado_despesas.csv"
    output_dir = raiz / "data" / "final"
    output_dir.mkdir(parents=True, exist_ok=True)

    logging.info("Iniciando processamento...")
    try:
        df_fin = pd.read_csv(input_file, dtype=str, encoding='utf-8')
    except UnicodeDecodeError:
        df_fin = pd.read_csv(input_file, dtype=str, encoding='latin1')
    except FileNotFoundError:
        logging.error("Arquivo consolidado_despesas.csv não encontrado!")
        return
        
    df_cad = baixar_cadastro_operadoras()
    if df_cad is None: return

    cols_map = {}
    for col in df_cad.columns:
        c = col.upper()
        if 'CNPJ' in c: cols_map[col] = 'CNPJ_Cad'
        elif 'RAZAO' in c or 'RAZÃO' in c: cols_map[col] = 'RazaoSocial_Cad'
        elif 'REGISTRO' in c and 'DATA' not in c: cols_map[col] = 'RegistroANS_Cad'
        elif 'UF' in c: cols_map[col] = 'UF_Cad'
        elif 'MODALIDADE' in c: cols_map[col] = 'Modalidade_Cad'
    df_cad.rename(columns=cols_map, inplace=True)

    df_fin['RegistroANS_Clean'] = df_fin['RegistroANS'].apply(limpar_numeros)
    df_cad['RegistroANS_Clean'] = df_cad['RegistroANS_Cad'].apply(limpar_numeros)
    df_cad['CNPJ_Clean'] = df_cad['CNPJ_Cad'].apply(limpar_numeros)

    mapa_ans_cnpj = dict(zip(df_cad['RegistroANS_Clean'], df_cad['CNPJ_Clean']))
    
    def resolver_cnpj_faltante(row):
        cnpj_atual = limpar_numeros(row.get('CNPJ', ''))
        reg_ans = str(row.get('RegistroANS_Clean', ''))
        if len(cnpj_atual) == 14: return cnpj_atual 
        return mapa_ans_cnpj.get(reg_ans, cnpj_atual)

    df_fin['CNPJ_Join'] = df_fin.apply(resolver_cnpj_faltante, axis=1)

    df_cad_unique = df_cad.drop_duplicates(subset=['CNPJ_Clean'])

    logging.info("Executando Join via CNPJ...")
    df_merged = pd.merge(
        df_fin,
        df_cad_unique[['CNPJ_Clean', 'RazaoSocial_Cad', 'UF_Cad', 'Modalidade_Cad', 'RegistroANS_Cad']],
        left_on='CNPJ_Join',
        right_on='CNPJ_Clean',
        how='left'
    )

    df_merged['RegistroANS'] = df_merged['RegistroANS_Cad'].fillna(df_merged['RegistroANS'])
    df_merged['RazaoSocial'] = df_merged['RazaoSocial_Cad'].fillna(df_merged['RazaoSocial']).fillna("DESCONHECIDO")
    df_merged['UF'] = df_merged['UF_Cad'].fillna("ND")
    df_merged['Modalidade'] = df_merged['Modalidade_Cad'].fillna("Não Informada")
    df_merged['CNPJ'] = df_merged['CNPJ_Join']

    df_merged['ValorDespesas'] = pd.to_numeric(df_merged['ValorDespesas'], errors='coerce').fillna(0.0)
    df_calculo = df_merged[df_merged['ValorDespesas'] > 0].copy()

    logging.info("Calculando métricas...")
    
    df_trimestral = df_calculo.groupby(
        ['RegistroANS', 'CNPJ', 'RazaoSocial', 'UF', 'Modalidade', 'Trimestre']
    )['ValorDespesas'].sum().reset_index()

    df_final = df_trimestral.groupby(['RegistroANS', 'CNPJ', 'RazaoSocial', 'UF', 'Modalidade']).agg(
        Total_Despesas=('ValorDespesas', 'sum'),
        Media_Trimestral=('ValorDespesas', 'mean'),
        Desvio_Padrao=('ValorDespesas', 'std')
    ).reset_index()

    df_final['Desvio_Padrao'] = df_final['Desvio_Padrao'].fillna(0.0)
    df_final = df_final.sort_values(by='Total_Despesas', ascending=False)

    arquivo_csv = output_dir / "despesas_agregadas.csv"
    df_final.to_csv(arquivo_csv, index=False, float_format="%.2f", encoding='utf-8-sig')

    arquivo_zip = output_dir / "Teste_Josué_Araújo.zip"
    with zipfile.ZipFile(arquivo_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(arquivo_csv, arcname="despesas_agregadas.csv")

    logging.info(f"Sucesso! Arquivo gerado em: {arquivo_zip}")

if __name__ == "__main__":
    main()