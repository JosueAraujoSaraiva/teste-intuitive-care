-- =========================================================
-- 3.4 QUERIES ANALÍTICAS
-- =========================================================

-- Helper: cria uma chave de período ordenável (ano*10 + trimestre_num)
-- Ex.: 2025 1T -> 20251

-- ---------------------------------------------------------
-- Query 1:
-- 5 operadoras com maior crescimento percentual entre o
-- primeiro e o último trimestre analisado.
--
-- Tratamento do desafio (operadoras sem dados em todos trimestres):
-- - Se não tiver valor no primeiro OU no último período, não calcula crescimento (NULL)
-- - Justificativa: tratar ausência como 0 distorce a métrica e inflaria crescimentos.
-- ---------------------------------------------------------
WITH periodos AS (
  SELECT DISTINCT
    (ano * 10 + CAST(LEFT(trimestre, 1) AS INT)) AS periodo_key
  FROM despesas_consolidadas
),
bounds AS (
  SELECT MIN(periodo_key) AS p_ini, MAX(periodo_key) AS p_fim FROM periodos
),
valores AS (
  SELECT
    d.registro_ans,
    SUM(CASE WHEN (d.ano * 10 + CAST(LEFT(d.trimestre, 1) AS INT)) = b.p_ini THEN d.valor_despesas END) AS v_ini,
    SUM(CASE WHEN (d.ano * 10 + CAST(LEFT(d.trimestre, 1) AS INT)) = b.p_fim THEN d.valor_despesas END) AS v_fim
  FROM despesas_consolidadas d
  CROSS JOIN bounds b
  GROUP BY d.registro_ans
),
crescimento AS (
  SELECT
    registro_ans,
    v_ini,
    v_fim,
    CASE
      WHEN v_ini IS NULL OR v_ini = 0 OR v_fim IS NULL THEN NULL
      ELSE ((v_fim - v_ini) / v_ini) * 100
    END AS crescimento_pct
  FROM valores
)
SELECT
  o.razao_social,
  c.registro_ans,
  ROUND(c.crescimento_pct, 2) AS crescimento_pct
FROM crescimento c
JOIN operadoras o ON o.registro_ans = c.registro_ans
WHERE c.crescimento_pct IS NOT NULL
ORDER BY c.crescimento_pct DESC
LIMIT 5;


-- ---------------------------------------------------------
-- Query 2:
-- Distribuição de despesas por UF:
-- Top 5 UFs por total e média por operadora em cada UF.
-- ---------------------------------------------------------
WITH por_uf AS (
  SELECT
    o.uf,
    SUM(d.valor_despesas) AS total_despesas,
    COUNT(DISTINCT d.registro_ans) AS qtd_operadoras,
    SUM(d.valor_despesas) / NULLIF(COUNT(DISTINCT d.registro_ans), 0) AS media_por_operadora
  FROM despesas_consolidadas d
  JOIN operadoras o ON o.registro_ans = d.registro_ans
  WHERE o.uf IS NOT NULL AND TRIM(o.uf) <> ''
  GROUP BY o.uf
)
SELECT
  uf,
  total_despesas,
  media_por_operadora
FROM por_uf
ORDER BY total_despesas DESC
LIMIT 5;


-- ---------------------------------------------------------
-- Query 3:
-- Quantas operadoras tiveram despesas acima da média geral
-- em pelo menos 2 dos 3 trimestres analisados?
--
-- Abordagem escolhida:
-- - Calcula média por período (ano+trimestre)
-- - Marca acima/abaixo por operadora em cada período
-- - Conta períodos acima por operadora
-- Trade-off: boa legibilidade e fácil de manter; índices em (ano,trimestre) e registro_ans ajudam.
-- ---------------------------------------------------------
WITH periodos_ordenados AS (
  SELECT DISTINCT
    ano,
    trimestre,
    (ano * 10 + CAST(LEFT(trimestre, 1) AS INT)) AS periodo_key
  FROM despesas_consolidadas
  ORDER BY periodo_key DESC
  LIMIT 3
),
media_periodo AS (
  SELECT
    d.ano,
    d.trimestre,
    AVG(d.valor_despesas) AS media
  FROM despesas_consolidadas d
  JOIN periodos_ordenados p
    ON p.ano = d.ano AND p.trimestre = d.trimestre
  GROUP BY d.ano, d.trimestre
),
flags AS (
  SELECT
    d.registro_ans,
    d.ano,
    d.trimestre,
    CASE WHEN d.valor_despesas > mp.media THEN 1 ELSE 0 END AS acima
  FROM despesas_consolidadas d
  JOIN media_periodo mp
    ON mp.ano = d.ano AND mp.trimestre = d.trimestre
),
contagem AS (
  SELECT
    registro_ans,
    SUM(acima) AS trimestres_acima
  FROM flags
  GROUP BY registro_ans
)
SELECT COUNT(*) AS qtd_operadoras
FROM contagem
WHERE trimestres_acima >= 2;
