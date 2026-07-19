"""
混合检索器（Hybrid Retriever）—— 关键词召回 + 向量召回 + RRF 融合。

设计目标（面试可讲）：
- 关键词召回（TF-IDF / BM25 类稀疏特征）保证「词面精确命中」与可解释性；
- 向量召回（FAISS 稠密向量）负责「语义模糊匹配」，弥补关键词对同义/长尾表述的遗漏；
- 两路结果用 **RRF（Reciprocal Rank Fusion）** 融合，避免各路分数量纲不一无法直接相加；
- 向量后端 **可插拔**：默认 LocalEmbeddingProvider（离线、零依赖、子词哈希池化），
  生产可切换 SentenceTransformerProvider / 混元·千问 Embedding API（见 embedding 配置）。

依赖：faiss-cpu（已装）。无外部模型权重即可离线运行。
"""

import hashlib
import math
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Protocol

import faiss

# ----------------------------- 1. Embedding 后端（可插拔） -----------------------------


class EmbeddingProvider(Protocol):
    dim: int

    def encode(self, texts: List[str]) -> List[List[float]]:
        ...


class LocalEmbeddingProvider:
    """
    本地确定性稠密向量（无模型权重）。
    思路：字符 trigram 经哈希投影到固定维度并平均池化，近似 fastText 的 subword hashing，
    能在不下载模型的前提下提供「子词共现分布」层面的模糊语义，与 TF-IDF 形成互补。
    """

    def __init__(self, dim: int = 256, seed: int = 42):
        self.dim = dim
        self._rng = hashlib.md5(str(seed).encode()).digest()

    def _trigram_hashes(self, text: str) -> List[int]:
        text = (text or "").lower()
        cn = re.findall(r"[一-鿿]", text)
        en = re.findall(r"[a-z0-9]+", text)
        grams: List[str] = []
        # 中文：相邻两字 + 三字窗口
        for i in range(len(cn) - 1):
            grams.append(cn[i] + cn[i + 1])
        for w in en:
            grams.append(w)
            for i in range(len(w) - 2):
                grams.append(w[i : i + 3])
        return [int(hashlib.md5(g.encode()).hexdigest(), 16) for g in grams] or [
            int(hashlib.md5(text.encode()).hexdigest(), 16)
        ]

    def encode(self, texts: List[str]) -> List[List[float]]:
        vecs: List[List[float]] = []
        for t in texts:
            h = self._trigram_hashes(t)
            v = [0.0] * self.dim
            for x in h:
                idx = x % self.dim
                # 用哈希高位做符号，构造有正有负的投影
                sign = 1.0 if (x >> 8) & 1 else -1.0
                v[idx] += sign
            # L2 归一化
            norm = math.sqrt(sum(z * z for z in v)) or 1.0
            vecs.append([z / norm for z in v])
        return vecs


class SentenceTransformerProvider:
    """
    预留：真实语义向量。需 `pip install sentence-transformers` 且能下载模型权重。
    启用方式：settings.embedding_backend = "st"，settings.embedding_model = "paraphrase-multilingual-MiniLM-L12-v2"
    """

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "SentenceTransformerProvider 需要 sentence-transformers 与模型权重，"
                f"当前不可用：{e}。请改用 local 后端或部署时安装。"
            )
        self._model = SentenceTransformer(model_name)
        self.dim = self._model.get_sentence_embedding_dimension()

    def encode(self, texts: List[str]) -> List[List[float]]:
        return self._model.encode(texts, normalize_embeddings=True).tolist()


def build_embedding_provider(backend: str = "local", model_name: str = "") -> EmbeddingProvider:
    if backend == "st":
        return SentenceTransformerProvider(model_name or "paraphrase-multilingual-MiniLM-L12-v2")
    return LocalEmbeddingProvider()


# ----------------------------- 2. 关键词检索（复用既有 TF-IDF 思路） -----------------------------


def _tokenize(text: str) -> List[str]:
    text = (text or "").lower()
    tokens: List[str] = re.findall(r"[a-z0-9]+", text)
    cn = re.findall(r"[一-鿿]", text)
    for i in range(len(cn) - 1):
        tokens.append(cn[i] + cn[i + 1])
    if cn:
        tokens.append(cn[-1])
    return tokens


class KeywordRetriever:
    def __init__(self, docs: List[Dict], top_k: int = 10):
        self.docs = docs
        self.top_k = top_k
        self._build()

    def _build(self):
        tokenized = [_tokenize(f"{d['title']} {d['content']}") for d in self.docs]
        df: Dict[str, int] = {}
        for toks in tokenized:
            for t in set(toks):
                df[t] = df.get(t, 0) + 1
        n = len(tokenized)
        self._vecs = []
        for toks in tokenized:
            tf = {}
            for t in toks:
                tf[t] = tf.get(t, 0) + 1
            vec = {}
            for t, c in tf.items():
                idf = math.log(n / (df.get(t, 0) + 1) + 1)
                vec[t] = (1 + math.log(c)) * idf
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
            self._vecs.append((vec, norm))

    def search(self, query: str, top_k: int = None) -> List[Dict]:
        top_k = top_k or self.top_k
        qtok = _tokenize(query)
        qtf = {}
        for t in qtok:
            qtf[t] = qtf.get(t, 0) + 1
        qvec = {t: (1 + math.log(c)) for t, c in qtf.items()}
        qnorm = math.sqrt(sum(v * v for v in qvec.values())) or 1.0
        scored = []
        for i, (vec, norm) in enumerate(self._vecs):
            if qnorm == 0 or norm == 0:
                continue
            dot = sum(w * qvec[t] for t, w in vec.items() if t in qvec)
            s = dot / (qnorm * norm)
            if s > 0:
                scored.append((s, i))
        scored.sort(reverse=True, key=lambda x: x[0])
        return [{"doc_index": i, "score": s} for s, i in scored[:top_k]]


# ----------------------------- 3. 向量检索（FAISS） -----------------------------


class VectorRetriever:
    def __init__(self, docs: List[Dict], provider: EmbeddingProvider, top_k: int = 10):
        self.docs = docs
        self.provider = provider
        self.top_k = top_k
        self._build()

    def _build(self):
        texts = [f"{d['title']} {d['content']}" for d in self.docs]
        vecs = self.provider.encode(texts)
        import numpy as np

        arr = np.asarray(vecs, dtype="float32")
        self._index = faiss.IndexFlatIP(arr.shape[1])  # 内积（向量已归一化 → 等价余弦）
        self._index.add(arr)

    def search(self, query: str, top_k: int = None) -> List[Dict]:
        top_k = top_k or self.top_k
        import numpy as np

        q = np.asarray(self.provider.encode([query]), dtype="float32")
        scores, idxs = self._index.search(q, top_k)
        out = []
        for s, i in zip(scores[0], idxs[0]):
            if i < 0:
                continue
            out.append({"doc_index": int(i), "score": float(s)})
        return out


# ----------------------------- 4. 混合检索 + RRF 融合 -----------------------------


def _rrf(ranked: List[Dict], k: int = 60) -> Dict[int, float]:
    """Reciprocal Rank Fusion：把多路「排名」融合为单一分数，规避分数量纲不一。"""
    fused: Dict[int, float] = {}
    for r in ranked:
        fused[r["doc_index"]] = fused.get(r["doc_index"], 0.0) + 1.0 / (k + r["rank"])
    return fused


def _rrf_fuse(ranked_lists: List[List[Dict]], k: int = 60) -> Dict[int, float]:
    """多路 Reciprocal Rank Fusion：融合任意路「排名」为单一分数（关键词/向量/图均可并入）。"""
    fused: Dict[int, float] = {}
    for rl in ranked_lists:
        for rank, r in enumerate(rl):
            fused[r["doc_index"]] = fused.get(r["doc_index"], 0.0) + 1.0 / (k + rank)
    return fused


class HybridRetriever:
    def __init__(
        self,
        docs: List[Dict],
        embedding_backend: str = "local",
        top_k: int = 3,
        vector_top_k: int = 8,
        keyword_top_k: int = 8,
        rrf_k: int = 60,
        enable_graph: bool = False,
        graph_top_k: int = 8,
    ):
        self.docs = docs
        self.top_k = top_k
        self._kw = KeywordRetriever(docs, top_k=keyword_top_k)
        self._vec = VectorRetriever(docs, build_embedding_provider(embedding_backend), top_k=vector_top_k)
        self._rrf_k = rrf_k
        self._enable_graph = enable_graph
        # 图 RAG 作为可选第三路（LightRAG 思路），默认关闭以保向后兼容
        self._graph = GraphRAGRetriever(docs, top_k=graph_top_k) if enable_graph else None

    def search(self, query: str, top_k: int = None) -> List[Dict]:
        top_k = top_k or self.top_k
        kw = self._kw.search(query, self._kw.top_k)
        vec = self._vec.search(query, self._vec.top_k)
        ranked_lists = [kw, vec]
        if self._graph is not None:
            g = self._graph.search(query, self._graph.top_k)
            for rank, r in enumerate(g):
                r["rank"] = rank
            ranked_lists.append(g)
        fused = _rrf_fuse(ranked_lists, self._rrf_k)
        ordered = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]
        out = []
        for i, score in ordered:
            d = self.docs[i]
            out.append(
                {
                    "doc": d,
                    "doc_index": i,
                    "score": round(score, 4),
                    "title": d["title"],
                    "content": d["content"],
                }
            )
        return out


# ----------------------------- 5. 图 RAG（LightRAG 思路：图索引 + 双层检索） -----------------------------

# 审计领域实体词典：归一名 -> 命中别名（同义归一）。确定性抽取、离线、无模型权重、CJK 友好。
# 这是把 LightRAG「实体-关系抽取」在工业界落地的「轻量领域版」：用领域词典替代 LLM 抽取，
# 在纯 CPU / 零依赖下复现「图索引 + 具体实体 + 抽象关系双层检索」的核心思想。
AUDIT_ENTITIES: Dict[str, List[str]] = {
    "审批": ["审批", "审批流", "审批流程", "审批节点"],
    "拆单": ["拆单", "自动拆分", "拆分", "自动拆单"],
    "权限": ["权限", "角色权限", "权限变更", "最小权限"],
    "Ukey": ["ukey", "u-key", "u key", "ukey回收", "ukey制作"],
    "工单": ["工单", "服务单", "工单进度", "进度卡片"],
    "留痕": ["留痕", "审计留痕", "可追溯", "可回溯"],
    "合规": ["合规", "强监管", "审计合规", "合规审计"],
    "资产": ["资产", "资产台账", "资产签收", "资产回写"],
    "巡检": ["巡检", "自动化巡检", "健康巡检", "智能巡检"],
    "监控": ["监控", "智能监控", "异常检测", "异常事件"],
    "服务目录": ["服务目录", "统一入口", "目录化", "点选式"],
    "对话直达": ["对话直达", "对话入口", "直达服务单", "自然语言"],
    "数据飞轮": ["数据飞轮", "领域语料", "算法优化", "sft"],
    "双人审批": ["双人审批", "双重审批", "强制双人", "强审批"],
    "催办": ["催办", "一键联系", "一键直达", "一键催办"],
    "视频会议": ["视频会议", "会议预约", "视频", "会议终端"],
    "回收": ["回收", "到期回收", "ukey回收", "权限回收"],
}


def extract_entities(text: str) -> List[str]:
    """从文本抽取审计领域实体（归一名列表）。确定性子串匹配，无需模型。"""
    text = (text or "").lower()
    found = []
    for name, aliases in AUDIT_ENTITIES.items():
        for a in aliases:
            if a.lower() in text:
                found.append(name)
                break
    return found


class GraphIndex:
    """实体共现图：节点=审计实体，边=同一文档共现（权=共现文档数）。

    对应 LightRAG 的 Graph Index 阶段——只是把 LLM 抽取替换为领域词典抽取，
    换取纯 CPU / 零依赖 / 可复现，面试可现场讲清「图索引 + 关系」的设计取舍。
    """

    def __init__(self, docs: List[Dict]):
        self.docs = docs
        self.entity_docs: Dict[str, set] = defaultdict(set)
        self.adj: Dict[str, Dict[str, int]] = defaultdict(dict)
        self.entity_titles: Dict[str, List[str]] = defaultdict(list)
        for i, d in enumerate(docs):
            ents = extract_entities(f"{d.get('title', '')} {d.get('content', '')}")
            for e in ents:
                self.entity_docs[e].add(i)
                self.entity_titles[e].append(d.get("title", ""))
            for a in ents:
                for b in ents:
                    if a != b:
                        self.adj[a][b] = self.adj[a].get(b, 0) + 1

    def low_level(self, entities: List[str]) -> Dict[int, float]:
        """具体实体检索：查询实体直接命中的文档（强相关）。"""
        doc_score: Dict[int, float] = defaultdict(float)
        for e in entities:
            for di in self.entity_docs.get(e, []):
                doc_score[di] += 1.0
        return doc_score

    def high_level(self, entities: List[str], hops: int = 2):
        """抽象/主题检索：沿图做 BFS 邻居扩散，召回关联实体与文档。

        返回 (doc_score, expanded_entities)。直接实体权重 1.0，扩散邻居 0.5（衰减）。
        """
        visited = set(entities)
        frontier = list(entities)
        for _ in range(hops):
            nxt = []
            for e in frontier:
                for nb in self.adj.get(e, {}):
                    if nb not in visited:
                        visited.add(nb)
                        nxt.append(nb)
            frontier = nxt
        doc_score: Dict[int, float] = defaultdict(float)
        for e in visited:
            w = 1.0 if e in entities else 0.5
            for di in self.entity_docs.get(e, []):
                doc_score[di] += w
        return doc_score, visited

    def high_level_edges(self, entities: List[str], hops: int = 2):
        """返回 BFS 扩散经过的实体与边（供前端可视化图结构）。"""
        visited = set(entities)
        frontier = list(entities)
        edges: List[List] = []
        for _ in range(hops):
            nxt = []
            for e in frontier:
                for nb, w in self.adj.get(e, {}).items():
                    edges.append([e, nb, w])
                    if nb not in visited:
                        visited.add(nb)
                        nxt.append(nb)
            frontier = nxt
        return visited, edges


class GraphRAGRetriever:
    """图 RAG 检索器（LightRAG 双层检索思想）：

    - Low-level（具体）：查询实体直接命中的文档；
    - High-level（抽象）：查询实体沿图扩散召回的关联文档；
    两层融合为 ranked docs，并标注每条命中的「直接实体」与「经图扩散关联实体」。
    """

    def __init__(self, docs: List[Dict], top_k: int = 8, hops: int = 2):
        self.docs = docs
        self.top_k = top_k
        self.hops = hops
        self.graph = GraphIndex(docs)

    def search(self, query: str, top_k: int = None) -> List[Dict]:
        top_k = top_k or self.top_k
        q_entities = extract_entities(query)
        low = self.graph.low_level(q_entities)
        high, expanded = self.graph.high_level(q_entities, self.hops)
        # 融合：high 已含直接实体(1.0)与邻居(0.5)；直接命中再叠加强化
        merged: Dict[int, float] = defaultdict(float, high)
        for di, s in low.items():
            merged[di] += s
        ordered = sorted(merged.items(), key=lambda x: x[1], reverse=True)[:top_k]
        out = []
        for i, score in ordered:
            doc_entities = set(extract_entities(f"{self.docs[i].get('title', '')} {self.docs[i].get('content', '')}"))
            direct = [e for e in doc_entities if e in q_entities]
            via = [e for e in doc_entities if e in expanded and e not in q_entities]
            out.append(
                {
                    "doc_index": i,
                    "score": round(float(score), 4),
                    "entities": direct,
                    "via": via,
                    "layer": "low" if direct else "high",
                }
            )
        return out

    def explain(self, query: str) -> Dict:
        """返回图检索的可解释素材（实体、扩散边、实体文档数），供前端可视化。"""
        q_entities = extract_entities(query)
        expanded, edges = self.graph.high_level_edges(q_entities, self.hops)
        return {
            "query_entities": sorted(q_entities),
            "expanded_entities": sorted(expanded - set(q_entities)),
            "edges": edges,
            "entity_doc_counts": {e: len(self.graph.entity_docs.get(e, [])) for e in (set(q_entities) | expanded)},
        }


def build_graph_rag(docs: List[Dict], embedding_backend: str = "local", top_k: int = 3, hops: int = 2):
    """工厂：返回启用图 RAG 的混合检索器（关键词 + 向量 + 图，三路 RRF 融合）。"""
    return HybridRetriever(
        docs,
        embedding_backend=embedding_backend,
        top_k=top_k,
        enable_graph=True,
        graph_top_k=8,
    )


# ----------------------------- 6. 多模态 RAG（RAG-Anything 思路：文本 + 表格 + 图像统一进检索） -----------------------------

# 审计领域多模态元数据样本：标题 -> {images:[截图描述], tables:[表格结构化文本]}。
# 真实生产应由多模态大模型（如腾讯混元多模态 / 千问-VL）对图像/表格做跨模态编码；
# 本环境无视觉模型，故以「描述文本 + 结构化文本」作为多模态元数据代理，
# 复用既有关键词/实体检索完成跨模态召回，复现 RAG-Anything「any modality 统一进 RAG」的核心思想。
AUDIT_MULTIMODAL: Dict[str, Dict[str, List[str]]] = {
    "Ukey 制作、调整与回收": {
        "images": [
            "Ukey 制作界面截图：左侧填写领用人与权限等级，右侧显示审批流节点（制作人 → 组长审批 → 管理员下发），底部为「提交制作」按钮。",
            "Ukey 回收登记截图：列表展示领用人、Ukey 编号、到期时间，操作列含「到期回收」与「强制注销」。",
        ],
    },
    "人员角色权限变更": {
        "tables": [
            "权限变更审批表：字段=申请人|所属部门|目标角色|权限项|双人审批人|生效时间（张三|运维部|管理员|资产只读|李四+王五|2026-03-15）。",
        ],
    },
    "资产自动签收与自动化巡检": {
        "tables": [
            "资产台账表：资产编号|责任人|部门|状态|签收时间（A-001|张三|运维部|在用|2026-03-12；A-002|李四|财务部|待回收|—）。",
            "巡检结果表：设备|健康分|异常项|巡检时间（核心交换机|96|CPU 峰值|2026-03-18）。",
        ],
    },
    "数据安全与审计留痕": {
        "images": [
            "审计系统留痕截图：顶部显示操作人/审批人/操作时间三栏，中部为工单号与变更详情，底部为「通过/驳回」按钮。",
        ],
        "tables": [
            "审计留痕字段表：字段名|类型|说明（操作人|string|执行者工号；操作时间|datetime|ISO8601；工单号|string|关联服务单；结果|enum|通过/驳回）。",
        ],
    },
    "审批流自动拆分": {
        "images": [
            "审批流编排截图：画布中「意图识别」节点后接「自动拆分」与「并行审批」两个分支，每个分支标注审批角色与 SLA。",
        ],
    },
    "工单进度卡片与一键联系": {
        "tables": [
            "工单字段表：工单号|标题|状态|处理人|进度%|催办次数（WO-1001|Ukey 制作|处理中|张三|60|1）。",
        ],
    },
    "终端领用与维修": {
        "images": [
            "终端领用登记截图：表单含领用人、设备类型、用途、预计归还日，提交后自动推送至资产管理员审批。",
        ],
    },
    "计算存储资源发放": {
        "tables": [
            "资源规格表：资源类型|规格|用途|审批人（云主机|4C8G|测试环境|运维主管；对象存储|5TB|归档|数据管理员）。",
        ],
    },
}


class MultimodalRetriever:
    """多模态 RAG（RAG-Anything 思路）：把文档附带的「表格 / 截图」纳入统一检索。

    视觉编码（可插拔，吸收 RAG-Anything「多模态 → 文本」路径）：
    - 默认 ProxyVisualEncoder：零依赖，复用 AUDIT_MULTIMODAL 预撰写描述（= VLM 预期输出代理）；
    - 真实模式（VISION_PROVIDER=hunyuan/qwen 且有密钥）：调用真实多模态大模型对
      `assets/screenshots/<标题>.png` 做视觉理解，产出实时 caption 替换代理描述，做到真·视觉嵌入。
    无论哪种模式，截图/表格最终都转为文本，进入既有关键词/实体检索完成跨模态召回，
    响应统一携带 encoder_mode 标识当前编码模式，诚实可讲。
    """

    def __init__(
        self,
        docs: List[Dict],
        meta: Dict[int, Dict[str, List[str]]] = None,
        top_k: int = 4,
        encoder=None,
        assets_dir: str = None,
    ):
        from app.services.multimodal_encoder import build_visual_encoder

        self.docs = docs
        self.top_k = top_k
        self.meta = meta if meta is not None else self._build_default_meta(docs)
        self.encoder = encoder or build_visual_encoder()
        self.encoder_mode = self.encoder.mode
        # 真实截图目录（缺省指向项目 assets/screenshots）；无图时编码器自动回退代理描述
        if assets_dir is None:
            root = Path(__file__).resolve().parents[2]
            assets_dir = str(root / "assets" / "screenshots")
        self.assets_dir = assets_dir

    @staticmethod
    def _build_default_meta(docs: List[Dict]) -> Dict[int, Dict[str, List[str]]]:
        meta: Dict[int, Dict[str, List[str]]] = {}
        for i, d in enumerate(docs):
            title = d.get("title", "")
            if title in AUDIT_MULTIMODAL:
                meta[i] = AUDIT_MULTIMODAL[title]
        return meta

    def _image_path(self, title: str) -> Optional[str]:
        """按文档标题查找真实截图（png/jpg），不存在返回 None → 编码器回退代理描述。"""
        if not self.assets_dir:
            return None
        base = os.path.join(self.assets_dir, title)
        for ext in (".png", ".jpg", ".jpeg", ".webp"):
            p = base + ext
            if os.path.exists(p):
                return p
        return None

    def search_multimodal(self, query: str, top_k: int = None) -> List[Dict]:
        top_k = top_k or self.top_k
        q_tokens = set(_tokenize(query))
        q_ents = set(extract_entities(query))
        scored = []
        for i, d in enumerate(self.docs):
            title = d.get("title", "")
            body = f"{title} {d.get('content', '')}"
            text_hit = len(set(_tokenize(body)) & q_tokens)
            ent_hit = len(set(extract_entities(body)) & q_ents)
            mm_hits = []
            for cap in self.meta.get(i, {}).get("images", []):
                # 经视觉编码器取得描述（proxy=预撰写；real=VLM 实时），再对其做跨模态打分
                caption = self.encoder.encode_image(self._image_path(title), cap)
                if set(_tokenize(caption)) & q_tokens or set(extract_entities(caption)) & q_ents:
                    mm_hits.append({"modality": "image", "text": caption, "encoder_mode": self.encoder_mode})
            for tb in self.meta.get(i, {}).get("tables", []):
                # 表格经视觉/结构化编码（proxy 直接结构化文本；真实模式可接表格理解模型）
                caption = self.encoder.encode_image(None, tb)
                if set(_tokenize(caption)) & q_tokens or set(extract_entities(caption)) & q_ents:
                    mm_hits.append({"modality": "table", "text": caption, "encoder_mode": self.encoder_mode})
            score = text_hit * 1.0 + ent_hit * 2.0 + len(mm_hits) * 1.5
            if score > 0:
                scored.append((score, i, mm_hits))
        scored.sort(reverse=True, key=lambda x: x[0])
        out = []
        for score, i, mm_hits in scored[:top_k]:
            d = self.docs[i]
            modalities = sorted({m["modality"] for m in mm_hits})
            out.append(
                {
                    "doc_index": i,
                    "title": d.get("title", ""),
                    "score": round(score, 3),
                    "modalities": modalities,
                    "encoder_mode": self.encoder_mode,
                    "multimodal_hits": mm_hits,
                    "text": d.get("content", "")[:140],
                }
            )
        return out


def build_multimodal(docs: List[Dict], top_k: int = 4, encoder=None) -> MultimodalRetriever:
    """工厂：返回多模态 RAG 检索器（内置审计领域多模态元数据样本）。"""
    return MultimodalRetriever(docs, top_k=top_k, encoder=encoder)
