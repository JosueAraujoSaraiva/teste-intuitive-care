from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class Operadora(BaseModel):
    cnpj: str
    razao_social: Optional[str] = None
    uf: Optional[str] = None
    modalidade: Optional[str] = None
    registro_ans: Optional[str] = None

class PageMeta(BaseModel):
    page: int
    limit: int
    total: int

class PaginatedResponse(BaseModel):
    data: List[Operadora]
    meta: PageMeta

class DespesaItem(BaseModel):
    ano: int
    trimestre: str
    valor_despesas: float

class EstatTopItem(BaseModel):
    cnpj: str
    razao_social: Optional[str] = None
    total_despesas: float

class EstatPorUFItem(BaseModel):
    uf: Optional[str] = None
    total_despesas: float

class EstatisticasResponse(BaseModel):
    total_despesas: float
    media_despesas: float
    top5_operadoras: List[EstatTopItem]
    despesas_por_uf: List[EstatPorUFItem]
    cache_ttl_seconds: int
