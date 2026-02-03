# Tabelas esperadas (Teste 3):
# - operadoras
# - despesas_consolidadas  (histórico por ano/trimestre)
# - despesas_agregadas     (métricas agregadas)

OPERADORAS_LIST = """
SELECT
  o.cnpj,
  o.razao_social,
  o.uf,
  o.modalidade,
  o.registro_ans
FROM operadoras o
WHERE
  (%s IS NULL)
  OR (o.cnpj ILIKE %s)
  OR (o.razao_social ILIKE %s)
ORDER BY o.razao_social ASC
LIMIT %s OFFSET %s;
"""

OPERADORAS_COUNT = """
SELECT COUNT(*) AS total
FROM operadoras o
WHERE
  (%s IS NULL)
  OR (o.cnpj ILIKE %s)
  OR (o.razao_social ILIKE %s);
"""

OPERADORA_DETALHE = """
SELECT
  o.cnpj,
  o.razao_social,
  o.uf,
  o.modalidade,
  o.registro_ans
FROM operadoras o
WHERE o.cnpj = %s
LIMIT 1;
"""

# Histórico de despesas por operadora (cnpj)
# Espera colunas:
# - cnpj
# - ano
# - trimestre (ex.: '1T', '2T'...)
# - valor_despesas (ou equivalente)
DESPESAS_HISTORICO = """
SELECT
  d.ano,
  d.trimestre,
  d.valor_despesas
FROM despesas_consolidadas d
WHERE d.cnpj = %s
ORDER BY d.ano DESC, d.trimestre DESC;
"""

# Estatísticas agregadas:
# - total de despesas
# - média
# - top 5 operadoras
# - distribuição por UF
ESTAT_TOTAL_MEDIA = """
SELECT
  COALESCE(SUM(a.total_despesas), 0) AS total_despesas,
  COALESCE(AVG(a.total_despesas), 0) AS media_despesas
FROM despesas_agregadas a;
"""

ESTAT_TOP5 = """
SELECT
  a.cnpj,
  a.razao_social,
  a.total_despesas
FROM despesas_agregadas a
ORDER BY a.total_despesas DESC
LIMIT 5;
"""

ESTAT_POR_UF = """
SELECT
  o.uf,
  COALESCE(SUM(a.total_despesas), 0) AS total_despesas
FROM despesas_agregadas a
LEFT JOIN operadoras o ON o.cnpj = a.cnpj
GROUP BY o.uf
ORDER BY total_despesas DESC;
"""
