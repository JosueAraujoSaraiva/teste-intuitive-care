import time
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api.db import fetch_all, fetch_one
import api.queries as q
from api.schemas import (
    PaginatedResponse, Operadora, PageMeta,
    DespesaItem, EstatisticasResponse
)

app = FastAPI(
    title="Teste IntuitiveCare",
    version="1.0.0",
    description="API para consumo do banco de dados."
)

# CORS para o Vue 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache simples em memória para /api/estatisticas
_CACHE = {"value": None, "expires_at": 0}
CACHE_TTL_SECONDS = 300 

@app.get("/api/operadoras", response_model=PaginatedResponse)
def listar_operadoras(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = Query(None, description="Busca por CNPJ ou Razão Social")
):
    offset = (page - 1) * limit

    search_norm = search.strip() if search else None
    like = f"%{search_norm}%" if search_norm else None

    total_row = fetch_one(q.OPERADORAS_COUNT, (search_norm, like, like))
    total = int(total_row["total"]) if total_row else 0

    rows = fetch_all(q.OPERADORAS_LIST, (search_norm, like, like, limit, offset))
    data = [Operadora(**r) for r in rows]

    return {
        "data": data,
        "meta": {"page": page, "limit": limit, "total": total}
    }

@app.get("/api/operadoras/{cnpj}", response_model=Operadora)
def detalhes_operadora(cnpj: str):
    row = fetch_one(q.OPERADORA_DETALHE, (cnpj,))
    if not row:
        raise HTTPException(status_code=404, detail="Operadora não encontrada")
    return Operadora(**row)

@app.get("/api/operadoras/{cnpj}/despesas", response_model=list[DespesaItem])
def historico_despesas(cnpj: str):
    
    exists = fetch_one(q.OPERADORA_DETALHE, (cnpj,))
    if not exists:
        raise HTTPException(status_code=404, detail="Operadora não encontrada")

    rows = fetch_all(q.DESPESAS_HISTORICO, (cnpj,))
    
    out = []
    for r in rows:
        out.append({
            "ano": int(r["ano"]),
            "trimestre": str(r["trimestre"]),
            "valor_despesas": float(r["valor_despesas"]),
        })
    return out

@app.get("/api/estatisticas", response_model=EstatisticasResponse)
def estatisticas():
    now = int(time.time())
    if _CACHE["value"] is not None and now < _CACHE["expires_at"]:
        cached = dict(_CACHE["value"])
        cached["cache_ttl_seconds"] = CACHE_TTL_SECONDS
        return cached

    total_media = fetch_one(q.ESTAT_TOTAL_MEDIA)
    top5 = fetch_all(q.ESTAT_TOP5)
    por_uf = fetch_all(q.ESTAT_POR_UF)

    result = {
        "total_despesas": float(total_media["total_despesas"]) if total_media else 0.0,
        "media_despesas": float(total_media["media_despesas"]) if total_media else 0.0,
        "top5_operadoras": [
            {
                "cnpj": t["cnpj"],
                "razao_social": t.get("razao_social"),
                "total_despesas": float(t["total_despesas"]),
            } for t in top5
        ],
        "despesas_por_uf": [
            {
                "uf": u.get("uf"),
                "total_despesas": float(u["total_despesas"]),
            } for u in por_uf
        ],
        "cache_ttl_seconds": CACHE_TTL_SECONDS
    }

    _CACHE["value"] = result
    _CACHE["expires_at"] = now + CACHE_TTL_SECONDS
    return result

@app.get("/health")
def health():
    return {"status": "ok"}
