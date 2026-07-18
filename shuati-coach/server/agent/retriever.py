"""RAG 检索器：知识点 / 考纲 / 用户错题 的本地可运行检索 + 引用溯源 + 防幻觉。

设计对标 Step3 提取的 RAG 技术点（向量 + BM25 + RRF 重排 + 引用溯源 + 低相关拒答）：
- 无嵌入 API 依赖时，用纯 Python 的 TF-IDF 做语义召回 + 关键词 2-gram 重叠做 BM25 式召回，
  再以 **RRF（Reciprocal Rank Fusion）** 融合两路排名（生产替换为向量库 + BM25 + RRF 同构）。
- 引用溯源：每个召回 chunk 带 topic / cat / 来源题目 qids，上层格式化为 [1][2] 引用。
- 防幻觉：相关性不足（无 2-gram 关键词重叠且语义相似度低）时，上层明确拒答，绝不编造。

语料来源（复用业务库，无需额外维护）：
  - knowledge：按 questions.topic 聚合「知识点 → 多题解析」文档；
  - syllabus：考研 / 考公 / 大厂 三套考纲概述；
  - user_wrong（动态）：某用户 wrong_book 中高频错题解析，检索时实时叠加（错题优先）。
"""
import math
import re
from collections import Counter, defaultdict

from database import get_db


class TfidfIndex:
    """轻量 TF-IDF 索引 + RRF 融合重排（API 极简，无第三方依赖）。

    相关/不相关判定的「关键词重叠」只用中文 2-gram（bigram），因为单字（如「写」「学」）
    过于常见会引入噪声，导致无关 query 被误判为相关。bigram 才有区分度。
    """

    K = 60  # RRF 常数

    def __init__(self):
        self.docs = []
        self._idf = {}
        self._tfidf = []
        self._doc_norm = []
        self._doc_bigrams = []   # 每个 doc 的 2-gram 集合（用于重叠信号）

    @staticmethod
    def _tokenize(text: str):
        text = (text or "").lower()
        tokens = list(re.findall(r"[a-z0-9]+", text))
        cjk = re.findall(r"[一-鿿]", text)
        for i, ch in enumerate(cjk):
            tokens.append("c:" + ch)
            if i + 1 < len(cjk):
                tokens.append("b:" + ch + cjk[i + 1])
        return tokens

    def fit(self, docs: list):
        self.docs = docs
        n = len(docs)
        df = Counter()
        raw = []
        self._doc_bigrams = []
        for d in docs:
            toks = self._tokenize(d.get("content", ""))
            bigrams = {t for t in toks if t.startswith("b:")}
            self._doc_bigrams.append(bigrams)
            cnt = Counter(toks)
            raw.append(cnt)
            for t in cnt:
                df[t] += 1
        # 平滑 idf
        self._idf = {t: math.log((n + 1) / (c + 1)) + 1 for t, c in df.items()}
        self._tfidf = []
        self._doc_norm = []
        for cnt in raw:
            vec = {t: (1 + math.log(c)) * self._idf.get(t, 1)
                   for t, c in cnt.items() if c > 0}
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1
            self._tfidf.append(vec)
            self._doc_norm.append(norm)
        return self

    def search(self, query: str, top_k: int = 5) -> list:
        q = Counter(self._tokenize(query))
        if not q:
            return []
        qvec = {}
        for t, c in q.items():
            idf = self._idf.get(t)
            if idf is None:
                continue
            qvec[t] = (1 + math.log(c)) * idf
        qn = math.sqrt(sum(v * v for v in qvec.values())) or 1
        q_bigrams = {t for t in qvec if t.startswith("b:")}

        sims = [0.0] * len(self.docs)
        bg_overlaps = [0] * len(self.docs)
        for i, dvec in enumerate(self._tfidf):
            dot = sum(w * dvec.get(t, 0) for t, w in qvec.items())
            sims[i] = dot / (qn * self._doc_norm[i]) if self._doc_norm[i] else 0.0
            bg_overlaps[i] = len(q_bigrams & self._doc_bigrams[i])

        # RRF 融合：语义相似度排名 + 2-gram 关键词重叠排名
        rrf = [0.0] * len(self.docs)
        for r, i in enumerate(sorted(range(len(self.docs)), key=lambda x: -sims[x])):
            rrf[i] += 1.0 / (self.K + r + 1)
        ov_idx = [i for i in range(len(self.docs)) if bg_overlaps[i] > 0]
        ov_idx.sort(key=lambda x: -bg_overlaps[x])
        for r, i in enumerate(ov_idx):
            rrf[i] += 1.0 / (self.K + r + 1)

        packed = []
        for i in range(len(self.docs)):
            if rrf[i] <= 0:
                continue
            d = self.docs[i]
            packed.append({
                "score": round(rrf[i], 4), "sim": round(sims[i], 4),
                "bg_overlap": bg_overlaps[i], "id": d.get("id"),
                "title": d.get("title"), "topic": d.get("topic"),
                "cat": d.get("cat"), "content": d.get("content"),
                "qids": d.get("qids", []), "kind": d.get("kind", "knowledge"),
            })
        packed.sort(key=lambda x: -x["score"])
        return packed[:top_k]


class KnowledgeRetriever:
    """知识点 / 考纲 / 用户错题 的统一检索入口（带引用溯源与防幻觉判定）。"""

    def __init__(self):
        self._base_docs = None       # 缓存：知识点 + 考纲 文档
        self._base_index = None      # 缓存：基础 TF-IDF 索引
        self.RELEVANCE_THRESHOLD = 0.006  # RRF 分数阈值（低于则视为不相关）

    # ---------- 语料构建 ----------
    def _build_base_docs(self) -> list:
        if self._base_docs is not None:
            return self._base_docs
        conn = get_db()
        rows = conn.execute(
            "SELECT id, cat, topic, stem, explain FROM questions"
        ).fetchall()
        conn.close()
        by_topic = defaultdict(list)
        for r in rows:
            by_topic[r["topic"]].append(dict(r))

        docs = []
        cid = 0
        for topic, items in by_topic.items():
            content = topic + "。" + " ".join((it["explain"] or "") for it in items)
            docs.append({
                "id": cid, "title": f"知识点：{topic}", "topic": topic,
                "cat": items[0]["cat"], "content": content,
                "qids": [it["id"] for it in items], "kind": "knowledge",
            })
            cid += 1

        syllabus = {
            "考研": "考研考纲：政治（马哲、近代史、思修、毛中特、当代）、英语（词汇、语法、阅读、写作）、"
                    "数学（高数、线代、概率统计）、计算机专业课。",
            "考公": "考公考纲：行测（常识判断、言语理解、数量关系、判断推理、资料分析）、"
                    "申论（归纳概括、对策建议、公文写作、大作文）、公共基础（法律、公文、时政）。",
            "大厂": "大厂技术岗考纲：数据结构与算法、操作系统、计算机网络、数据库、系统设计、"
                    "编程语言（Python/Java）、前端基础。",
        }
        for cat, text in syllabus.items():
            docs.append({
                "id": cid, "title": f"考纲：{cat}", "topic": "考纲", "cat": cat,
                "content": text, "qids": [], "kind": "syllabus",
            })
            cid += 1
        self._base_docs = docs
        return docs

    def _ensure_index(self) -> TfidfIndex:
        if self._base_index is None:
            self._base_index = TfidfIndex().fit(self._build_base_docs())
        return self._base_index

    def _user_wrong_doc(self, user_id: int) -> dict | None:
        conn = get_db()
        rows = conn.execute(
            """SELECT wb.question_id, wb.error_count, q.topic, q.cat, q.explain
               FROM wrong_book wb JOIN questions q ON wb.question_id = q.id
               WHERE wb.user_id=? ORDER BY wb.error_count DESC LIMIT 15""",
            (user_id,),
        ).fetchall()
        conn.close()
        if not rows:
            return None
        parts = []
        qids = []
        for r in rows:
            parts.append(f"{r['topic']}：{r['explain'] or ''}")
            qids.append(r["question_id"])
        content = "我的高频错题解析汇总：" + " ".join(parts)
        return {
            "id": -1, "title": "我的错题本（优先参考）", "topic": "我的错题",
            "cat": "", "content": content, "qids": qids, "kind": "user_wrong",
        }

    # ---------- 检索 ----------
    def search(self, query: str, top_k: int = 5, user_id: int = None) -> dict:
        """返回 {query, relevant, threshold, top_score, hits[]}。hits 每项含引用信息。"""
        if user_id:
            wdoc = self._user_wrong_doc(user_id)
            if wdoc:
                docs = self._build_base_docs() + [wdoc]
                idx = TfidfIndex().fit(docs)
            else:
                idx = self._ensure_index()
        else:
            idx = self._ensure_index()

        hits = idx.search(query, top_k=top_k)
        if not hits:
            return {"query": query, "relevant": False,
                    "threshold": self.RELEVANCE_THRESHOLD, "top_score": 0.0, "hits": []}
        top = hits[0]
        # 防幻觉判定：以 2-gram 关键词真实命中为唯一相关判据（sim 仅用于排序融合）。
        # 无关键词重叠一律视为不相关并拒答，杜绝常见字导致的高相似度虚高误判。
        relevant = top.get("bg_overlap", 0) >= 1
        return {"query": query, "relevant": relevant,
                "threshold": self.RELEVANCE_THRESHOLD, "top_score": top["score"],
                "hits": hits}

    @staticmethod
    def format_citations(hits: list) -> list:
        cites = []
        for i, h in enumerate(hits[:5], 1):
            if h.get("qids"):
                qs = ", ".join(f"#{q}" for q in h["qids"][:3])
                cites.append(f"[{i}] {h['title']}（来源题 {qs}）")
            else:
                cites.append(f"[{i}] {h['title']}")
        return cites

    def get_corpus_stats(self) -> dict:
        docs = self._build_base_docs()
        return {
            "knowledge": sum(1 for d in docs if d["kind"] == "knowledge"),
            "syllabus": sum(1 for d in docs if d["kind"] == "syllabus"),
            "total": len(docs),
        }
