# README — Teste de Entrada Intuitive Care (v2.0)

**Projeto:** `teste-intuitive-care`  
**Autor:** **Josué Araújo Saraiva**

---

Olá! 👋  
Este repositório contém minha solução para o **Teste de Estágio** da **Intuitive Care**.

O desafio foi resolvido de forma **pragmática e orientada a decisões técnicas**, com **trade-offs explicitamente documentados** e um fluxo **executável de ponta a ponta**, desde o download e processamento dos dados até a interface web.

> **Nota:** Para entregar a melhor solução possível, investi em capacitação: **adquiri um curso na Udemy e estudei por 2 dias** as tecnologias envolvidas (Python, FastAPI, Vue 3, SQL e processamento de dados). Isso me permitiu tomar decisões mais conscientes e implementar o projeto com qualidade.

---

## 📌 Visão Geral do Projeto

O projeto é composto por quatro grandes partes:

- **Backend (Python + FastAPI)**  
  API para consulta de operadoras, histórico de despesas e estatísticas.
- **Pipeline de Dados (Python)**  
  Download, extração, limpeza, consolidação, validação e agregação.
- **Banco de Dados (PostgreSQL)**  
  Modelagem normalizada, scripts de carga e queries analíticas.
- **Frontend (Vue 3 + Vite)**  
  Listagem de operadoras, busca, paginação, gráficos e página de detalhes.

---

## 📁 Organização de Pastas

```text
TESTE_INTUITIVECARE/
├─ backend/
│  ├─ api/                 # FastAPI (rotas, schemas, queries, conexão)
│  ├─ data/                # dados brutos e processados (raw/extracted/processed/consolidated/final)
│  ├─ database/
│  │  ├─ sql/              # DDL, importação e queries analíticas
│  │  └─ script/           # scripts de carga no PostgreSQL
│  ├─ script/              # pipeline de dados (download → consolidação → agregação)
│  ├─ .env                 # variáveis de ambiente do banco
│  └─ requirements.txt     # dependências Python
├─ frontend/
│  ├─ src/                 # código Vue (pages, router, composables)
│  ├─ public/
│  ├─ .env                 # VITE_API_BASE_URL
│  ├─ package.json
│  └─ vite.config.js
└─ README.md


