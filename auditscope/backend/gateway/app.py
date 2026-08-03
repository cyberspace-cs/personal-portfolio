"""网关：对外唯一入口 /api/v1。聚合五大检索 + RAG，带缓存与降级。

deep module 思路：路由极薄，复杂逻辑在 core/services 内部。
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

# 允许 `python -m gateway.app` 从 backend 目录运行
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.cache import get, set
from core.query_understanding import parse_query
from core.rag import answer as rag_answer
from data.seed import seed
from data.models import Base, _engine
from services.search import (search_companies, search_bosses, search_persons,
                             search_flows, search_social, detect_anomalies)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(_engine)
    seed()
    yield


app = FastAPI(title="AuditScope Gateway", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
async def health():
    return {"ok": True, "mode": "demo" if not settings.deepseek_api_key else "llm"}


@app.post("/api/v1/search")
async def api_search(payload: dict):
    """统一搜索：q -> 五类结果 + 查询理解。带缓存。"""
    q = (payload.get("q") or "").strip()
    cache_key = f"search:{q}"
    cached = get(cache_key)
    if cached:
        return cached

    sq = await parse_query(q)
    companies = search_companies(q)
    bosses = search_bosses(q)
    persons = search_persons(q)
    flows = search_flows(q)
    socials = search_social(q)

    hits = []
    for c in companies:
        hits.append({"kind": "company", "id": f"C{c['id']}", "title": c["name"],
                     "sub": c["industry"], "risk": c["risk"], "detail": c})
    for b in bosses:
        hits.append({"kind": "boss", "id": f"B{b['id']}", "title": b["name"],
                     "sub": f"控股 {b['heldCount']} 家", "risk": b["risk"], "detail": b})
    for p in persons:
        hits.append({"kind": "person", "id": f"P{p['id']}", "title": p["name"],
                     "sub": p["title"], "risk": p["risk"], "detail": p})
    for f in flows:
        hits.append({"kind": "flow", "id": f"F{f['id']}", "title": f["counterparty"],
                     "sub": f"{f['date']} · {'流入' if f['direction']=='in' else '流出'}",
                     "risk": "high" if f["abnormal"] else "normal", "detail": f})
    for s in socials:
        hits.append({"kind": "social", "id": f"S{s['id']}", "title": s["name"],
                     "sub": s["company"], "risk": s["risk"], "detail": s})

    result = {"query": sq.__dict__, "hits": hits,
              "counts": {"company": len(companies), "boss": len(bosses),
                         "person": len(persons), "flow": len(flows), "social": len(socials)}}
    set(cache_key, result, ttl=120)
    return result


@app.post("/api/v1/rag/ask")
async def api_ask(payload: dict):
    question = payload.get("question", "")
    return await rag_answer(question)


@app.get("/api/v1/anomalies")
async def api_anomalies(company_id: int | None = None):
    return detect_anomalies(company_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
