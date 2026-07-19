import math
import re
from typing import List, Dict

"""
本地轻量检索器（零外部依赖）。
- 中文按「字 bigram」切词，英文/数字按词切分，避免引入分词模型依赖。
- 采用 TF-IDF 权重 + 余弦相似度做关键词召回（keyword recall）。
- 架构上预留「语义召回（vector recall）」扩展位，可与混元/千问 embedding
  接口或本地向量库（如 Chroma/FAISS）组成「混合检索」，提升长尾语义命中。
"""


def tokenize(text: str) -> List[str]:
    text = (text or "").lower()
    tokens: List[str] = re.findall(r"[a-z0-9]+", text)
    cn = re.findall(r"[一-鿿]", text)
    for i in range(len(cn) - 1):
        tokens.append(cn[i] + cn[i + 1])
    if cn:
        tokens.append(cn[-1])
    return tokens


def _tfidf_vec(tokens: List[str], df: Dict[str, int], n: int) -> Dict[str, float]:
    tf = {}
    for t in tokens:
        tf[t] = tf.get(t, 0) + 1
    vec = {}
    for t, c in tf.items():
        idf = math.log(n / (df.get(t, 0) + 1) + 1)
        vec[t] = (1 + math.log(c)) * idf
    return vec


class Retriever:
    def __init__(self, docs: List[Dict], top_k: int = 3, backend: str = "local"):
        self.docs = docs
        self.top_k = top_k
        self.backend = backend
        self._build()

    def _build(self):
        tokenized = [tokenize(f"{d['title']} {d['content']}") for d in self.docs]
        df: Dict[str, int] = {}
        for toks in tokenized:
            for t in set(toks):
                df[t] = df.get(t, 0) + 1
        n = len(tokenized)
        self.doc_vecs = []
        for toks in tokenized:
            vec = _tfidf_vec(toks, df, n)
            norm = math.sqrt(sum(v * v for v in vec.values()))
            self.doc_vecs.append((vec, norm))

    def search(self, query: str, top_k: int = None) -> List[Dict]:
        top_k = top_k or self.top_k
        qtok = tokenize(query)
        qtf = {}
        for t in qtok:
            qtf[t] = qtf.get(t, 0) + 1
        qvec = {t: (1 + math.log(c)) for t, c in qtf.items()}
        qnorm = math.sqrt(sum(v * v for v in qvec.values()))
        scored = []
        for i, (vec, norm) in enumerate(self.doc_vecs):
            if qnorm == 0 or norm == 0:
                continue
            dot = sum(w * qvec[t] for t, w in vec.items() if t in qvec)
            score = dot / (qnorm * norm)
            if score > 0:
                scored.append((score, i))
        scored.sort(reverse=True, key=lambda x: x[0])
        return [{"doc": self.docs[i], "score": s} for s, i in scored[:top_k]]
