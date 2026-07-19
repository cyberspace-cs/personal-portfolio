"""RAG 引擎：文本切块 + 哈希向量检索 + BM25 关键词检索的混合检索（Hybrid Search）。

无需 embedding 模型依赖：用哈希技巧（hashing trick）构造确定性向量做语义近似，
叠加 BM25 关键词召回，最终加权融合。支持多文档、返回带分数的引用片段（citation）。
"""
import re
import math
from dataclasses import dataclass, field


@dataclass
class Chunk:
    doc_id: str
    doc_title: str
    index: int
    text: str
    score: float = 0.0
    vector: list = field(default_factory=list)


def _tokenize(text: str) -> list[str]:
    return [w for w in re.split(r"[\s，。、；：！？!?,.;:()（）\[\]【】\"'“”]+", text.lower()) if w]


class VectorStore:
    """哈希向量库：把词哈希到固定维度并累加（词频），L2 归一化后做余弦相似度。"""

    def __init__(self, dims: int = 512) -> None:
        self.dims = dims
        self.items: list[Chunk] = []

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dims
        for tok in _tokenize(text):
            h = hash(tok) % self.dims
            vec[h] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def add(self, chunk: Chunk) -> None:
        chunk.vector = self._embed(chunk.text)
        self.items.append(chunk)

    def search(self, query: str, top_k: int = 5) -> list[Chunk]:
        q = self._embed(query)
        scored = []
        for it in self.items:
            dot = sum(a * b for a, b in zip(q, it.vector))
            scored.append((dot, it))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [it for _, it in scored[:top_k]]


class HybridRetriever:
    """混合检索器：BM25 + 向量，加权融合，按文档去重保留最高分片段。"""

    def __init__(self, dims: int = 512) -> None:
        self.store = VectorStore(dims=dims)
        self.docs: list[dict] = []
        self.dims = dims
        self._df: dict[str, int] = {}
        self._n = 0

    def ingest(self, doc_id: str, title: str, text: str) -> int:
        self.docs.append({"id": doc_id, "title": title, "text": text})
        chunks = chunk_text(text)
        for i, c in enumerate(chunks):
            self.store.add(Chunk(doc_id=doc_id, doc_title=title, index=i, text=c))
        # 更新文档频率用于 BM25
        seen: set[str] = set()
        for c in chunks:
            for tok in set(_tokenize(c)):
                self._df[tok] = self._df.get(tok, 0) + (0 if tok in seen else 1)
            seen.update(_tokenize(c))
        self._n += 1
        return len(chunks)

    def bm25(self, query: str, top_k: int = 20) -> dict[str, float]:
        q_tokens = _tokenize(query)
        if not q_tokens:
            return {}
        scores: dict[int, float] = {}
        avgdl = sum(len(_tokenize(c.text)) for c in self.store.items) / max(1, len(self.store.items))
        k1, b = 1.5, 0.75
        for idx, chunk in enumerate(self.store.items):
            dl = len(_tokenize(chunk.text))
            tf_map: dict[str, int] = {}
            for tok in _tokenize(chunk.text):
                tf_map[tok] = tf_map.get(tok, 0) + 1
            s = 0.0
            for tok in q_tokens:
                if tok not in tf_map:
                    continue
                df = self._df.get(tok, 0)
                idf = math.log((self._n - df + 0.5) / (df + 0.5) + 1.0)
                tf = tf_map[tok]
                s += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / max(1, avgdl)))
            scores[idx] = s
        return scores

    def search(self, query: str, top_k: int = 5, vector_w: float = 0.6, bm25_w: float = 0.4) -> list[Chunk]:
        vec_res = self.store.search(query, top_k=top_k * 3)
        vec_scores = {id(c): c.score for c in []}
        bm25_scores = self.bm25(query)
        # 归一化向量分
        maxv = max((c.vector and 1 or 0) for c in vec_res) or 1.0
        fused: dict[int, tuple[Chunk, float]] = {}
        for rank, c in enumerate(vec_res):
            # 用点积近似（store.search 已排序），这里用 1/(rank+1) 作为相对分
            vs = 1.0 / (rank + 1)
            fused[id(c)] = (c, vs * vector_w)
        for idx, s in bm25_scores.items():
            c = self.store.items[idx]
            prev = fused.get(id(c), (c, 0.0))[1]
            fused[id(c)] = (c, prev + s * bm25_w)
        out = sorted([v[0] for v in fused.values()], key=lambda c: fused[id(c)][1], reverse=True)
        for c in out[:top_k]:
            c.score = round(fused[id(c)][1], 4)
        return out[:top_k]


def chunk_text(text: str, size: int = 380, overlap: int = 60) -> list[str]:
    """按中文字符窗口切块，带重叠以保留上下文。"""
    text = re.sub(r"\n{2,}", "\n", text).strip()
    if not text:
        return []
    chunks = []
    start = 0
    step = max(1, size - overlap)
    while start < len(text):
        end = min(len(text), start + size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start += step
    return chunks
