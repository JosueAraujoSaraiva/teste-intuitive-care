# README — Teste Intuitive Care

**Projeto:** teste-intuitive-care  
**Autor:** Josué Araújo Saraiva

---

Olá! 👋  
Este repositório contém minha solução para o **Teste de Estágio** da **Intuitive Care**.

Busquei resolver o desafio de forma **pragmática**, justificando **trade-offs técnicos** e organizando um fluxo **executável de ponta a ponta**, do download de dados à interface web.

> **Nota:** Para entregar a melhor solução possível, adquiri um curso na Udemy e estudei por 2 dias as tecnologias envolvidas (Python, FastAPI, Vue 3, SQL e processamento de dados).

---

## ✅ Visão Geral do Projeto

O projeto está dividido em:

- **Backend (Python + FastAPI)**: API para consulta das operadoras, histórico e estatísticas  
- **Pipeline de Dados (Python)**: download, extração, limpeza, consolidação e agregação  
- **Banco de Dados (PostgreSQL)**: modelagem normalizada, scripts de carga e queries analíticas  
- **Frontend (Vue 3 + Vite)**: listagem, busca, paginação, gráficos e detalhes  

---

## 📁 Organização de Pastas

```text
TESTE_INTUITIVECARE/
├─ backend/
│  ├─ api/                 # FastAPI (rotas, schemas, queries)
│  ├─ data/                # dados brutos e processados
│  ├─ database/
│  │  ├─ sql/              # DDL, importação e analytics
│  │  └─ script/           # scripts de carga
│  ├─ script/              # pipeline de dados
│  ├─ .env
│  └─ requirements.txt
├─ frontend/
│  ├─ src/
│  ├─ public/
│  ├─ .env
│  ├─ package.json
│  └─ vite.config.js
└─ README.md
```
## ✅ Requisitos do teste e como foram atendidos

### 1) Integração com API pública (ANS)

**Como foi feito:**
- Download automático dos **3 últimos trimestres** via `backend/script/download_data.py`.
- Extração dos ZIPs com `backend/script/extract_data.py`.
- Identificação de arquivos com “Despesas com Eventos/Sinistros” e normalização com `backend/script/identify_files.py`.

**Trade-off técnico (processamento incremental vs memória):**
Escolhi **processamento incremental por arquivo**, porque os dados da ANS podem ser grandes e variados em formato. Isso reduz consumo de memória e torna o pipeline mais resiliente a arquivos quebrados ou inconsistentes.

---

### 2) Consolidação, validação e enriquecimento

**Como foi feito:**
- Consolidação dos 3 trimestres com `backend/script/consolidar_despesas.py`.
- Validação de CNPJ e enriquecimento de dados cadastrais em `backend/script/transform_data.py`.

**Trade-offs técnicos:**
1. **CNPJ inválido:**  
   Optei por **marcar CNPJs inválidos** (flag) e manter o registro, ao invés de descartar.  
   *Prós:* preserva dados para auditoria e análise posterior.  
   *Contras:* exige cuidado no consumo posterior.  

2. **Valores negativos ou zerados:**  
   Valores zerados/negativos são tratados como ruído ou inconsistência e não entram nos cálculos agregados.

3. **Razão social ausente:**  
   Preenchida com "DESCONHECIDO" para evitar registros incompletos.

4. **Join com cadastro de operadoras:**  
   Escolhi **join via CNPJ normalizado**, e para múltiplas ocorrências no cadastro, privilegiei a primeira ocorrência válida (via deduplicação).  
   *Justificativa:* evita explosão de registros e mantém o pipeline simples para um projeto de teste.

---

### 3) Banco de dados e análise

**Escolhas técnicas principais:**

- **Banco:** PostgreSQL >10.0  
  *Por quê:* oferece boa performance, suporte a tipos numéricos precisos (NUMERIC), e recursos maduros para análise.

- **Normalização (Trade-off):**  
  Escolhi **tabelas normalizadas** (operadoras, despesas_consolidadas e despesas_agregadas).  
  *Justificativa:* reduz redundância em milhões de registros e facilita manutenção.

- **Tipos de dados (Trade-off):**  
  Valores monetários em **NUMERIC(18,2)** para evitar imprecisão de float.  
  Períodos em **INTEGER/CHAR** para simplificar filtros e comparações.

**Scripts SQL:**
- DDL: `backend/database/sql/create_tables.sql`
- Importação: `backend/database/sql/import_data.sql`
- Analytics: `backend/database/sql/analytics.sql`

---

### 4) API e Interface Web

**Backend (FastAPI)**
- Rotas implementadas:
  - `GET /api/operadoras` (paginação + busca)
  - `GET /api/operadoras/{cnpj}`
  - `GET /api/operadoras/{cnpj}/despesas`
  - `GET /api/estatisticas`

**Trade-offs técnicos:**
- **Framework:** FastAPI  
  *Motivo:* rapidez na implementação, validação automática via Pydantic, documentação integrada.
- **Paginação:** Offset-based (`page`, `limit`)  
  *Motivo:* simples de implementar e adequado para o volume esperado.
- **Cache de estatísticas:** cache em memória por 5 minutos  
  *Motivo:* evita recalcular dados agregados com frequência.
- **Resposta da API:** dados + metadados  
  *Motivo:* facilita paginação no frontend.

**Frontend (Vue 3)**
- Página principal: tabela paginada + filtro por razão social ou CNPJ.
- Gráfico de distribuição de despesas por UF (Chart.js).
- Página de detalhes com histórico de despesas.

**Trade-offs técnicos no Frontend:**
- **Busca no servidor:** evita carregar volume grande no cliente.
- **Estado com composables:** mais simples que Vuex/Pinia para o escopo do projeto.
- **Tratamento de erros e loading:** mensagens específicas de erro + estados visuais de carregamento.

---

## ✅ Como executar (passo a passo)

> **Pré-requisitos:**  
> - Python 3.10+  
> - Node.js 18+  
> - PostgreSQL 10+  
> - Git (opcional, se o projeto já estiver baixado)

> **Importante:** abaixo está um passo a passo **bem detalhado**, para que consiga rodar tudo do zero.

### 0) (Opcional) Criar ambiente virtual do Python

Recomendado para isolar as dependências:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```

### 1) Instalar dependências do Backend

```bash
cd backend
pip install -r requirements.txt
```

### 1. Pipeline de dados

Esta etapa baixa os dados da ANS, extrai, filtra e gera os CSVs finais.

**Ordem exata dos scripts (execute um por vez):**

```bash
cd backend/script
python download_data.py
python extract_data.py
python identify_files.py
python consolidar_despesas.py
python transform_data.py
```

### 2. Banco de dados

Crie um banco vazio no PostgreSQL (exemplo: `intuitive_care`) e depois configure o arquivo `.env`.

1) Configure um arquivo `.env` em `backend/` com:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=seu_banco
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
```

2) Execute:

```bash
cd backend/database/script
python load_staging_and_run.py
```

---

### 3. Backend (API)

Com o banco pronto, suba a API:

```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload
```

**Testar rapidamente:**
- Abra no navegador: `http://127.0.0.1:8000/health`
- Documentação automática: `http://127.0.0.1:8000/docs`

- **Teste via Postman:**  
  Você pode testar as rotas da API no Postman usando, por exemplo:  
  - `GET http://127.0.0.1:8000/api/operadoras?page=1&limit=10`  
  - `GET http://127.0.0.1:8000/api/operadoras/{cnpj}`  
  - `GET http://127.0.0.1:8000/api/operadoras/{cnpj}/despesas`  
  - `GET http://127.0.0.1:8000/api/estatisticas`

---

### 4. Frontend (Vue)

Agora suba o front:

```bash
cd frontend
npm install
npm run dev
```

**Acesso:**
- Normalmente em: `http://localhost:5173`

> Se a API estiver em outra porta/host, ajuste a variável `VITE_API_BASE_URL` no `.env` do front.

---

## ✅ Considerações finais

O objetivo foi atender todos os itens do teste com soluções justificadas, mantendo organização e clareza no fluxo de execução.  
Estou aberto a melhorias e discussões técnicas.
