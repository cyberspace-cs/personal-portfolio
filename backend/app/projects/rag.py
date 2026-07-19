"""企业级 RAG 系统：混合检索 + 多文档理解 + 引用溯源。

复用内核 HybridRetriever（BM25 + 哈希向量）与 ContextHarness（上下文预算），
无 embedding 模型也能跑；配置 LLM Key 后自动升级为生成式回答。
"""
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.rag import HybridRetriever, chunk_text
from app.core.context import ContextHarness, estimate_tokens
from app.core.llm import LLMClient
from app.core.prompt import registry

router = APIRouter(prefix="/api/rag", tags=["rag"])

llm = LLMClient()
_store = HybridRetriever(dims=512)

registry.register(
    "rag_answer",
    "你是基于企业知识库的问答助手。请仅根据下面的「参考资料」回答问题，"
    "并在句末用 [n] 标注引用编号。若资料中没有答案，明确说明不知道。\n\n"
    "参考资料:\n{context}\n\n问题: {question}",
)


class DocIn(BaseModel):
    id: Optional[str] = None
    title: str
    text: str


class IngestRequest(BaseModel):
    docs: list[DocIn]


class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    use_llm: bool = True


@router.post("/ingest")
def ingest(req: IngestRequest):
    total_chunks = 0
    for i, d in enumerate(req.docs):
        did = d.id or f"doc_{int(time.time())}_{i}"
        total_chunks += _store.ingest(did, d.title, d.text)
    return {"ingested_docs": len(req.docs), "total_chunks": total_chunks}


@router.get("/docs")
def list_docs():
    return {"docs": _store.docs, "total_chunks": len(_store.store.items)}


@router.post("/ask")
def ask(req: AskRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空。")
    chunks = _store.search(req.question, top_k=req.top_k)
    # 构造引用上下文（带预算裁剪）
    harness = ContextHarness(budget=3000)
    ctx_lines = []
    citations = []
    for idx, c in enumerate(chunks, 1):
        ctx_lines.append(f"[{idx}] ({c.doc_title}) {c.text}")
        citations.append({"ref": idx, "doc": c.doc_title, "score": c.score, "text": c.text})
    ctx = "\n".join(ctx_lines)
    ctx_tokens = estimate_tokens(ctx)

    answer = ""
    if req.use_llm and llm.enabled:
        prompt = registry.render("rag_answer", context=ctx, question=req.question)
        answer = llm.chat(system="你是严谨的企业知识库问答助手。", user=prompt)
    else:
        # 抽取式降级：返回命中查询词最多的片段 + 引用
        hit = chunks[0] if chunks else None
        if hit:
            answer = f"根据资料 [{citations[0]['ref']}]《{hit.doc_title}》：{hit.text[:300]}"
            if len(chunks) > 1:
                answer += f"\n另可参考 [{citations[1]['ref']}]《{chunks[1].doc_title}》。"
        else:
            answer = "未在知识库中检索到相关内容（规则降级模式：请配置 LLM Key 获得生成式回答）。"
    return {
        "answer": answer,
        "citations": citations,
        "context_tokens": ctx_tokens,
        "retrieval_mode": "hybrid(bm25+vector)",
        "llm_enabled": llm.enabled,
    }


@router.get("/health")
def health():
    return {"status": "ok", "project": "rag", "chunks": len(_store.store.items), "llm_enabled": llm.enabled}
