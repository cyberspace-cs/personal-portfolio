from app.llm.client import LLMClient
from app.models import KnowledgeResponse
from app.services.retrieval import Retriever
from app.services.knowledge_base import KB

"""
知识库问答（RAG 入口）。
流程：检索（Retriever 召回 top-k） → 组装上下文 → 生成（LLMClient，可插拔基座）。
- 配置混元/千问后，生成阶段走真实大模型并强制「基于上下文、标注来源」。
- 未配置 Key（Mock）时，生成阶段直接拼接检索命中片段并标注来源，仍可演示完整检索链路。
"""

_llm = LLMClient()
_retriever = Retriever(KB.docs, top_k=3)

_SYSTEM = (
    "你是审计智能一体化运维平台的知识助手。只依据给定的【检索上下文】作答，"
    "关键结论必须标注来源标题；若上下文不足以回答问题，请如实说明并建议转人工。"
    "回答使用中文，简洁、专业。"
)


def _mock_answer(question: str, hits: list) -> str:
    if not hits:
        return "（演示）未在知识库中检索到相关内容。您可以描述更具体的诉求，或转人工协助。"
    top = hits[0]["doc"]
    lines = [f"根据知识库检索（命中 {len(hits)} 条），为您解答：", ""]
    lines.append(top["content"])
    if len(hits) > 1:
        lines.append("")
        lines.append("相关参考：" + "；".join(h["doc"]["title"] for h in hits[1:]) + "。")
    lines.append("")
    lines.append(f"📚 主要来源：《{top['title']}》")
    return "\n".join(lines)


def ask(question: str) -> KnowledgeResponse:
    """RAG 问答：检索增强生成。"""
    hits = _retriever.search(question, top_k=3)
    sources = [h["doc"]["title"] for h in hits]
    retrieved = [
        {
            "title": h["doc"]["title"],
            "snippet": h["doc"]["content"][:140],
            "score": round(h["score"], 3),
        }
        for h in hits
    ]
    ctx = "\n\n".join(f"【{h['doc']['title']}】\n{h['doc']['content']}" for h in hits)

    if _llm.provider == "mock":
        answer = _mock_answer(question, hits)
    else:
        answer = _llm._chat(
            _SYSTEM,
            f"检索上下文:\n{ctx}\n\n用户问题: {question}\n\n请基于上下文作答并标注来源。",
        )

    return KnowledgeResponse(answer=answer, sources=sources, retrieved=retrieved)
