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

def limpar_numbers(valor):
    if pd.isna(valor): return ""
    return re.sub(r'[^0-9]', '', str(valor))

def validar_cnpj(cnpj_input):
    cnpj = limpar_numbers(cnpj_input)
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


def baixar_e_salvar_cadastro(caminho_saida: Path):
    """
    Novo: Baixa o cadastro e persiste em disco para satisfazer o item 3.1 do teste.
    """
    base_url = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/"
    
    try:
        logging.info("Acessando diretório da ANS para localizar CSV...")
        html = obter_html(base_url)
        links_csv = extrair_links_csv(html)
        
        if not links_csv:
            arquivo_escolhido = "Relatorio_cadop.csv"
        else:
            candidatos = [l for l in links_csv if "cadop" in l.lower() or "operadora" in l.lower()]
            arquivo_escolhido = candidatos[0] if candidatos else links_csv[0]

        url_final = base_url + arquivo_escolhido
        logging.info(f"Baixando e salvando cadastro localmente: {arquivo_escolhido}")
        
        conteudo = baixar_arquivo(url_final)
        
        # Salvando o arquivo físico para o teste de SQL (Item 3)
        caminho_saida.parent.mkdir(parents=True, exist_ok=True)
        with open(caminho_saida, "wb") as f:
            f.write(conteudo)
            
        logging.info(f"✔ Arquivo de cadastro persistido em: {caminho_saida}")
        return True
            
    except Exception as e:
        logging.error(f"Erro ao processar download do cadastro: {e}")
        return False

def main():
    raiz = Path(__file__).resolve().parents[1]
    input_financeiro = raiz / "data" / "consolidated" / "consolidado_despesas.csv"
    input_cadastro = raiz / "data" / "processed" / "dados_cadastrais_operadoras.csv"
    output_dir = raiz / "data" / "final"
    
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_cadastro.exists():
        sucesso = baixar_e_salvar_cadastro(input_cadastro)
        if not sucesso: return

    logging.info("Lendo arquivos locais...")
    try:
        df_fin = pd.read_csv(input_financeiro, dtype=str, encoding='utf-8')
        df_cad = pd.read_csv(input_cadastro, sep=";", encoding="latin1", dtype=str, on_bad_lines="skip")
    except Exception as e:
        logging.error(f"Erro ao carregar arquivos: {e}")
        return

    cols_map = {}
    for col in df_cad.columns:
        c = col.upper()
        if 'CNPJ' in c: cols_map[col] = 'CNPJ_Cad'
        elif 'RAZAO' in c or 'RAZÃO' in c: cols_map[col] = 'RazaoSocial_Cad'
        elif 'REGISTRO' in c and 'DATA' not in c: cols_map[col] = 'RegistroANS_Cad'
        elif 'UF' in c: cols_map[col] = 'UF_Cad'
        elif 'MODALIDADE' in c: cols_map[col] = 'Modalidade_Cad'
    df_cad.rename(columns=cols_map, inplace=True)

    df_fin['RegistroANS_Clean'] = df_fin['RegistroANS'].apply(limpar_numbers)
    df_cad['RegistroANS_Clean'] = df_cad['RegistroANS_Cad'].apply(limpar_numbers)
    df_cad['CNPJ_Clean'] = df_cad['CNPJ_Cad'].apply(limpar_numbers)

   
    logging.info("Validando CNPJs...")
    df_cad['CNPJ_Valido'] = df_cad['CNPJ_Clean'].apply(validar_cnpj)

    mapa_ans_cnpj = dict(zip(df_cad['RegistroANS_Clean'], df_cad['CNPJ_Clean']))
    
    def resolver_cnpj_faltante(row):
        cnpj_atual = limpar_numbers(row.get('CNPJ', ''))
        reg_ans = str(row.get('RegistroANS_Clean', ''))
        if len(cnpj_atual) == 14: return cnpj_atual 
        return mapa_ans_cnpj.get(reg_ans, cnpj_atual)

    df_fin['CNPJ_Join'] = df_fin.apply(resolver_cnpj_faltante, axis=1)

    df_cad_unique = df_cad.drop_duplicates(subset=['CNPJ_Clean'])

    df_merged = pd.merge(
        df_fin,
        df_cad_unique[['CNPJ_Clean', 'RazaoSocial_Cad', 'UF_Cad', 'Modalidade_Cad', 'RegistroANS_Cad', 'CNPJ_Valido']],
        left_on='CNPJ_Join',
        right_on='CNPJ_Clean',
        how='left'
    )

    df_merged['RazaoSocial'] = df_merged['RazaoSocial_Cad'].fillna(df_merged['RazaoSocial']).fillna("DESCONHECIDO")
    df_merged['ValorDespesas'] = pd.to_numeric(df_merged['ValorDespesas'], errors='coerce').fillna(0.0)

    df_calculo = df_merged[df_merged['ValorDespesas'] > 0].copy()

    logging.info("Calculando métricas trimestrais...")
    
    df_final = df_calculo.groupby(['RegistroANS', 'CNPJ_Join', 'RazaoSocial', 'UF_Cad', 'Modalidade_Cad']).agg(
        Total_Despesas=('ValorDespesas', 'sum'),
        Media_Trimestral=('ValorDespesas', 'mean'),
        Desvio_Padrao=('ValorDespesas', 'std')
    ).reset_index().rename(columns={'CNPJ_Join': 'CNPJ', 'UF_Cad': 'UF', 'Modalidade_Cad': 'Modalidade'})

    df_final['Desvio_Padrao'] = df_final['Desvio_Padrao'].fillna(0.0)
    df_final = df_final.sort_values(by='Total_Despesas', ascending=False)

    arquivo_csv = output_dir / "despesas_agregadas.csv"
    df_final.to_csv(arquivo_csv, index=False, float_format="%.2f", encoding='utf-8-sig')

    logging.info(f"✔ Processo concluído. Arquivo gerado em: {arquivo_csv}")

if __name__ == "__main__":
    main()