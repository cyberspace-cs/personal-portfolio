"""TDD：RAG 检索召回评估（基于演示语料，独立断言）。"""
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.rag import retrieve, answer


def test_retrieve_returns_topk():
    ev = retrieve("公转私 资金流水 异常", top_k=3)
    assert 1 <= len(ev) <= 3


def test_retrieve_relevant_source():
    ev = retrieve("社保 缴费 缺口")
    sources = [e.source for e in ev]
    assert any("社保" in s for s in sources)


def test_answer_has_refs_and_text():
    res = asyncio.run(answer("星河智能 有哪些资金异常？"))
    assert "answer" in res and "refs" in res
    assert isinstance(res["refs"], list) and len(res["refs"]) >= 1
