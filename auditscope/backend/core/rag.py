"""RAG 证据问答（Deepseek + Milvus + Redis）。

Seam:
- retrieve(query) -> List[Evidence]   # Milvus 向量检索（无 Milvus 时走内存语料）
- answer(query) -> {answer, refs}      # 拼 evidence -> Deepseek 生成

deep module：调用方只拿回答与引用，不关心向量库/缓存/模型细节。
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from typing import Optional

import httpx

from core.config import settings
from core.cache import get, set

# 演示语料（真实部署替换为 Milvus 检索结果）
CORPUS = [
    ("星河智能科技有限公司 资金流水：2025-11-03 向陈嘉禾个人账户转出 480 万，标注'无合同支撑'，异常。",
     "星河智能-2025-11 资金流水"),
    ("云栖数据服务股份有限公司：社保缴费仅 12 个月，缺口 9 个月，未连续缴纳，风险高。",
     "云栖数据-社保缴费记录"),
    ("通汇供应链管理有限公司：涉诉 2 起，存在股权质押，关注级。", "通汇供应链-风险摘要"),
    ("李文博 控股 11 家公司，合计资本 5.8 亿，其中云栖数据被列为失信被执行人。",
     "李文博-控股关系"),
]


@dataclass
class Evidence:
    text: str
    source: str
    score: float = 1.0


def _embed(text: str) -> list[float]:
    """极简句向量（演示用，真实部署用 embedding 模型 / Milvus）。"""
    h = hashlib.md5(text.encode("utf-8")).digest()
    return [float((h[i] % 100) / 100) for i in range(8)]


def retrieve(query: str, top_k: int = 4) -> list[Evidence]:
    q = _embed(query)
    scored = []
    for text, src in CORPUS:
        v = _embed(text)
        sim = sum(a * b for a, b in zip(q, v)) / (sum(a * a for a in q) ** 0.5 + 1e-9)
        scored.append(Evidence(text=text, source=src, score=sim))
    scored.sort(key=lambda e: e.score, reverse=True)
    return scored[:top_k]


async def answer(query: str) -> dict:
    cache_key = f"rag:{hashlib.md5(query.encode()).hexdigest()}"
    cached = get(cache_key)
    if cached:
        return cached

    evidences = retrieve(query)
    ctx = "\n".join(f"[{e.source}] {e.text}" for e in evidences)
    refs = [e.source for e in evidences]

    if not settings.deepseek_api_key:
        # 降级：规则拼接（可演示、可测）
        ans = ("（演示模式·未连接 Deepseek）基于检索到的证据给出审计关注要点：\n"
               + "\n".join(f"· {e.text}" for e in evidences)
               + "\n建议对异常流水追加银行函证与合同穿透，对社保缺口核实劳动关系真实性。")
        result = {"answer": ans, "refs": refs}
        set(cache_key, result)
        return result

    try:
        prompt = (f"你是审计证据分析助手。仅依据下列证据回答问题，并注明引用来源。\n"
                  f"证据：\n{ctx}\n\n问题：{query}")
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                f"{settings.deepseek_base}/chat/completions",
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
                json={"model": "deepseek-chat", "messages": [
                    {"role": "system", "content": "你是严谨的审计助手，引用必须来自给定证据。"},
                    {"role": "user", "content": prompt},
                ]},
            )
            r.raise_for_status()
            ans = r.json()["choices"][0]["message"]["content"]
        result = {"answer": ans, "refs": refs}
        set(cache_key, result)
        return result
    except Exception:
        ans = "（Deepseek 调用失败，已降级）" + "\n".join(f"· {e.text}" for e in evidences)
        return {"answer": ans, "refs": refs}
