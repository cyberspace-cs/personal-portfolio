"""
RAG Knowledge Hub · 后端服务
================================
企业级检索增强问答（RAG）后端，纯 Python 实现真实检索链路，无需向量数据库 / API Key。

核心链路（与生产级 RAG 同构）：
  文档入库 → 分块(chunk) → 构建倒排 + TF-IDF 向量 →
  查询：混合召回(向量余弦 ⊕ 关键词 BM25 打分) → 重排 → 阈值门控 →
  抽取式生成答案 + 引用溯源(doc/chunk/score/置信度)

运行：
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8002
"""
from __future__ import annotations

import math
import re
import uuid
from collections import Counter, defaultdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="RAG Knowledge Hub API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

RELEVANCE_THRESHOLD = 0.12  # 低于该分数判定“无可靠依据”，拒绝硬答


# ----------------------------------------------------------------------------
# 分词：中英文混合（中文按字 bigram + 英文按词）
# ----------------------------------------------------------------------------
def tokenize(text: str) -> list[str]:
    text = text.lower()
    tokens: list[str] = []
    for seg in re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]+", text):
        if re.match(r"[a-z0-9]+", seg):
            tokens.append(seg)
        else:  # 中文：单字 + 相邻 bigram，兼顾召回与精度
            tokens.extend(list(seg))
            tokens.extend(seg[i:i + 2] for i in range(len(seg) - 1))
    return tokens


# ----------------------------------------------------------------------------
# 数据结构
# ----------------------------------------------------------------------------
class Chunk:
    def __init__(self, doc_id: str, doc_title: str, idx: int, text: str):
        self.id = f"{doc_id}#{idx}"
        self.doc_id = doc_id
        self.doc_title = doc_title
        self.idx = idx
        self.text = text
        self.tokens = tokenize(text)
        self.tf = Counter(self.tokens)
        self.len = len(self.tokens)


class Store:
    def __init__(self):
        self.docs: dict[str, dict] = {}
        self.chunks: list[Chunk] = []
        self.df: Counter = Counter()      # 文档频率（以 chunk 为单位）
        self.avg_len = 0.0

    def _rebuild_stats(self):
        self.df = Counter()
        for c in self.chunks:
            for tok in set(c.tokens):
                self.df[tok] += 1
        self.avg_len = sum(c.len for c in self.chunks) / len(self.chunks) if self.chunks else 0.0

    def idf(self, term: str) -> float:
        n = len(self.chunks)
        return math.log(1 + (n - self.df.get(term, 0) + 0.5) / (self.df.get(term, 0) + 0.5))

    def add_doc(self, title: str, text: str) -> dict:
        doc_id = uuid.uuid4().hex[:8]
        chunk_texts = chunk_text(text)
        for i, ct in enumerate(chunk_texts):
            self.chunks.append(Chunk(doc_id, title, i, ct))
        self.docs[doc_id] = {"id": doc_id, "title": title, "chunks": len(chunk_texts), "chars": len(text)}
        self._rebuild_stats()
        return self.docs[doc_id]

    def del_doc(self, doc_id: str):
        if doc_id not in self.docs:
            raise HTTPException(404, "文档不存在")
        self.chunks = [c for c in self.chunks if c.doc_id != doc_id]
        del self.docs[doc_id]
        self._rebuild_stats()


STORE = Store()


def chunk_text(text: str, target: int = 220, overlap: int = 40) -> list[str]:
    """按句切分后贪心合并到目标长度，块间保留 overlap 字符，兼顾语义完整与召回。"""
    sents = re.split(r"(?<=[。！？\.\!\?\n])", text)
    sents = [s.strip() for s in sents if s.strip()]
    chunks, cur = [], ""
    for s in sents:
        if len(cur) + len(s) <= target:
            cur += s
        else:
            if cur:
                chunks.append(cur)
            cur = (cur[-overlap:] if cur else "") + s
            if len(cur) > target * 1.6:
                chunks.append(cur)
                cur = ""
    if cur:
        chunks.append(cur)
    return chunks or [text]


# ----------------------------------------------------------------------------
# 混合检索：TF-IDF 余弦 ⊕ BM25 关键词
# ----------------------------------------------------------------------------
def cosine_tfidf(q_tf: Counter, chunk: Chunk) -> float:
    dot = 0.0
    for term, qf in q_tf.items():
        if term in chunk.tf:
            w = STORE.idf(term)
            dot += (qf * w) * (chunk.tf[term] * w)
    qn = math.sqrt(sum((qf * STORE.idf(t)) ** 2 for t, qf in q_tf.items())) or 1e-9
    cn = math.sqrt(sum((tf * STORE.idf(t)) ** 2 for t, tf in chunk.tf.items())) or 1e-9
    return dot / (qn * cn)


def bm25(q_terms: list[str], chunk: Chunk, k1: float = 1.5, b: float = 0.75) -> float:
    score = 0.0
    for term in set(q_terms):
        if term not in chunk.tf:
            continue
        idf = STORE.idf(term)
        tf = chunk.tf[term]
        denom = tf + k1 * (1 - b + b * chunk.len / (STORE.avg_len or 1))
        score += idf * (tf * (k1 + 1)) / (denom or 1e-9)
    return score


def retrieve(question: str, top_k: int = 4) -> list[dict]:
    if not STORE.chunks:
        return []
    q_terms = tokenize(question)
    q_tf = Counter(q_terms)
    scored = []
    bm_max = 1e-9
    raw = []
    for c in STORE.chunks:
        cos = cosine_tfidf(q_tf, c)
        bm = bm25(q_terms, c)
        bm_max = max(bm_max, bm)
        raw.append((c, cos, bm))
    for c, cos, bm in raw:
        hybrid = 0.6 * cos + 0.4 * (bm / bm_max)   # 归一化后融合
        scored.append({"chunk": c, "cos": cos, "bm25": bm, "score": hybrid})
    scored.sort(key=lambda x: -x["score"])
    return scored[:top_k]


# ----------------------------------------------------------------------------
# 抽取式答案合成 + 高亮命中
# ----------------------------------------------------------------------------
def synthesize(question: str, hits: list[dict]) -> str:
    if not hits:
        return "知识库中暂无与该问题相关的内容。"
    top = hits[0]["chunk"]
    q_terms = set(tokenize(question))
    sents = re.split(r"(?<=[。！？\.\!\?])", top.text)
    best = max(sents, key=lambda s: sum(1 for t in set(tokenize(s)) if t in q_terms), default=top.text)
    parts = [best.strip()]
    for h in hits[1:2]:
        extra = h["chunk"].text[:80].strip()
        if extra and extra not in best:
            parts.append("补充：" + extra + "…")
    return "根据知识库检索结果：\n" + "\n".join(parts)


# ----------------------------------------------------------------------------
# 请求体 & 路由
# ----------------------------------------------------------------------------
class IngestReq(BaseModel):
    title: str
    text: str


class QueryReq(BaseModel):
    question: str
    top_k: int = 4


@app.post("/api/docs/ingest")
def ingest(req: IngestReq) -> dict:
    if not req.text.strip():
        raise HTTPException(400, "文档内容为空")
    doc = STORE.add_doc(req.title.strip() or "未命名文档", req.text)
    return {"doc": doc, "total_chunks": len(STORE.chunks)}


@app.get("/api/docs")
def list_docs() -> dict:
    return {"docs": list(STORE.docs.values()), "total_chunks": len(STORE.chunks)}


@app.delete("/api/docs/{doc_id}")
def del_doc(doc_id: str) -> dict:
    STORE.del_doc(doc_id)
    return {"ok": True, "total_chunks": len(STORE.chunks)}


@app.post("/api/query")
def query(req: QueryReq) -> dict:
    hits = retrieve(req.question, req.top_k)
    top_score = round(hits[0]["score"], 4) if hits else 0.0
    relevant = top_score >= RELEVANCE_THRESHOLD
    citations = [{
        "id": h["chunk"].id,
        "doc_title": h["chunk"].doc_title,
        "chunk_idx": h["chunk"].idx,
        "text": h["chunk"].text,
        "score": round(h["score"], 4),
        "cosine": round(h["cos"], 4),
        "bm25": round(h["bm25"], 4),
    } for h in hits]
    if relevant:
        answer = synthesize(req.question, hits)
    else:
        answer = ("未在知识库中检索到足够可靠的依据（最高相关度 "
                  f"{top_score} < 阈值 {RELEVANCE_THRESHOLD}）。为避免臆测，建议补充相关文档后再提问。")
    return {
        "answer": answer,
        "relevant": relevant,
        "top_score": top_score,
        "threshold": RELEVANCE_THRESHOLD,
        "confidence": round(min(1.0, top_score / (RELEVANCE_THRESHOLD * 3)), 3),
        "citations": citations,
    }


@app.post("/api/seed")
def seed() -> dict:
    """一键灌入示例知识库，便于开箱体验。"""
    samples = [
        ("RAG 检索增强生成简介",
         "RAG（Retrieval-Augmented Generation，检索增强生成）是一种将信息检索与大语言模型生成结合的架构。"
         "它先从外部知识库中检索与问题相关的文档片段，再把这些片段作为上下文交给大模型生成答案。"
         "RAG 的核心优势是缓解大模型幻觉、支持知识实时更新、并可提供答案的引用来源，实现可溯源问答。"
         "典型链路包括：文档分块、向量化、相似度检索、重排序、以及带上下文的生成。"),
        ("向量检索与混合检索",
         "向量检索通过将文本编码为稠密向量，用余弦相似度衡量语义相关性，擅长捕捉同义与语义匹配。"
         "关键词检索（如 BM25）基于词频与逆文档频率，擅长精确术语匹配。"
         "混合检索（Hybrid Search）将向量分数与关键词分数加权融合，兼顾语义泛化与精确匹配，是企业级 RAG 的主流方案。"
         "检索后通常再接一个重排序（rerank）模型进一步提升 Top-K 的精度。"),
        ("如何降低大模型幻觉",
         "降低幻觉的常见手段包括：引入 RAG 提供事实依据、设置相关度阈值门控拒绝硬答、要求模型引用来源、"
         "使用反思（self-reflection）机制二次校验答案、以及对关键结论做事实核查。"
         "当检索到的证据相关度低于阈值时，系统应主动回答“暂无可靠依据”，而非编造答案。"),
    ]
    added = [STORE.add_doc(t, x) for t, x in samples]
    return {"added": added, "total_chunks": len(STORE.chunks)}


@app.get("/api/meta")
def meta() -> dict:
    return {"threshold": RELEVANCE_THRESHOLD, "docs": len(STORE.docs), "chunks": len(STORE.chunks)}


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "rag-knowledge-hub", "docs": len(STORE.docs)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
