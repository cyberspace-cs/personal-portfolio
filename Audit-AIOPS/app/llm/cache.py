"""
LLM 推理加速 · 应用层缓存（Prompt Cache / Semantic Cache）
==========================================================
面试与研发亮点：把「KV Cache / Prompt Cache」的思想落地到应用层，
避免对**相同/近似**的提示重复发起大模型推理，从而显著降低首字延迟（TTFT）
与调用成本。对应大模型推理优化技术栈中的「缓存复用」方向。

两类缓存：
1. PromptCache（精确命中）：对 (provider, system, user) 做归一化哈希，
   完全相同提示直接复用上一次推理结果——等价于把 KV 留在「提示前缀」上。
2. SemanticCache（语义命中）：用稠密向量表示提示，近似语义（cos 相似度 ≥ 阈值）
   也复用结果——进一步放大缓存命中率，适合问答/意图识别这类高重复场景。

两者都离线可跑：语义缓存复用 retrieval_hybrid 的 LocalEmbeddingProvider（确定性、无需联网）。
"""

from __future__ import annotations

import hashlib
import math
import re
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Optional


# —— 离线确定性稠密向量（内联，避免与 app.services 形成循环导入）——
# 与 retrieval_hybrid.LocalEmbeddingProvider 同思路：字符级哈希词袋，无需联网/模型权重。
# 语义缓存只比较「提示 vs 提示」，内部自洽即可。对中文采用「逐字 + 拉丁词」切分，
# 使近义改写的共享字更高（如「Ukey 怎么申请」≈「如何申请制作一个 Ukey」），从而被语义命中。
_LOCAL_DIM = 256
_TOKEN_RE = re.compile(r"[\u4e00-\u9fff]|[a-z0-9]+", re.U)


def _local_embed(text: str) -> list[float]:
    vec = [0.0] * _LOCAL_DIM
    toks = _TOKEN_RE.findall(text.lower())
    if not toks:
        toks = [text.lower()]
    for t in toks:
        h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16) % _LOCAL_DIM
        vec[h] += 1.0
    # L2 归一化（TF 向量）
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


@dataclass
class _Entry:
    text: str
    created_at: float = field(default_factory=time.time)
    hits: int = 0


class PromptCache:
    """精确命中缓存（LRU）。模拟推理服务端的 prefix/KV cache 复用。"""

    def __init__(self, max_size: int = 1024):
        self.max_size = max_size
        self._store: "OrderedDict[str, _Entry]" = OrderedDict()
        self.stats = {"hits": 0, "misses": 0}

    @staticmethod
    def _key(provider: str, system: str, user: str) -> str:
        norm = f"{provider}|||{system.strip()}|||{user.strip()}".encode("utf-8")
        return hashlib.sha256(norm).hexdigest()

    def get(self, provider: str, system: str, user: str) -> Optional[str]:
        k = self._key(provider, system, user)
        e = self._store.get(k)
        if e is None:
            self.stats["misses"] += 1
            return None
        self._store.move_to_end(k)
        e.hits += 1
        self.stats["hits"] += 1
        return e.text

    def put(self, provider: str, system: str, user: str, text: str) -> None:
        if not text:
            return
        k = self._key(provider, system, user)
        self._store[k] = _Entry(text=text)
        self._store.move_to_end(k)
        while len(self._store) > self.max_size:
            self._store.popitem(last=False)

    @property
    def size(self) -> int:
        return len(self._store)

    def reset_stats(self) -> None:
        self.stats = {"hits": 0, "misses": 0}


class SemanticCache:
    """语义命中缓存：近似问题复用结果，进一步放大命中率。"""

    def __init__(self, threshold: float = 0.92, max_size: int = 1024):
        self.threshold = threshold
        self.max_size = max_size
        self._keys: list[str] = []
        self._vecs: list[list[float]] = []
        self._texts: list[str] = []
        self.stats = {"hits": 0, "misses": 0}

    def _cos(self, a: list[float], b: list[float]) -> float:
        na = sum(x * x for x in a) ** 0.5
        nb = sum(x * x for x in b) ** 0.5
        if na == 0 or nb == 0:
            return 0.0
        return sum(x * y for x, y in zip(a, b)) / (na * nb)

    def get(self, user: str) -> Optional[str]:
        v = _local_embed(user)
        best, bi = -1.0, -1
        for i, vec in enumerate(self._vecs):
            s = self._cos(v, vec)
            if s > best:
                best, bi = s, i
        if best >= self.threshold and bi >= 0:
            self.stats["hits"] += 1
            return self._texts[bi]
        self.stats["misses"] += 1
        return None

    def put(self, user: str, text: str) -> None:
        if not text:
            return
        self._keys.append(user)
        self._vecs.append(_local_embed(user))
        self._texts.append(text)
        if len(self._texts) > self.max_size:
            self._keys.pop(0)
            self._vecs.pop(0)
            self._texts.pop(0)

    @property
    def size(self) -> int:
        return len(self._texts)

    def reset_stats(self) -> None:
        self.stats = {"hits": 0, "misses": 0}


class LLMCache:
    """组合缓存：先精确、后语义。对外暴露统一 get/put。"""

    def __init__(self, semantic: bool = True, semantic_threshold: float = 0.50):
        self.prompt = PromptCache()
        self.semantic = SemanticCache(threshold=semantic_threshold) if semantic else None
        self.saved_ms_total = 0  # 命中缓存累计节省的推理耗时（ms）

    def add_saved(self, ms: int) -> None:
        """记录一次命中所节省的推理耗时（供加速收益统计）。"""
        try:
            self.saved_ms_total += int(ms)
        except Exception:
            pass

    def get(self, provider: str, system: str, user: str) -> Optional[str]:
        exact = self.prompt.get(provider, system, user)
        if exact is not None:
            return exact
        if self.semantic is not None:
            return self.semantic.get(user)
        return None

    def put(self, provider: str, system: str, user: str, text: str) -> None:
        self.prompt.put(provider, system, user, text)
        if self.semantic is not None:
            self.semantic.put(user, text)

    def stats(self) -> dict:  # type: ignore[return]
        s = dict(self.prompt.stats)
        s["prompt_size"] = self.prompt.size
        if self.semantic is not None:
            s["semantic_hits"] = self.semantic.stats["hits"]
            s["semantic_misses"] = self.semantic.stats["misses"]
            s["semantic_size"] = self.semantic.size
        total = s.get("hits", 0) + s.get("misses", 0)
        s["hit_rate"] = round(s["hits"] / total, 4) if total else 0.0
        s["size"] = s.get("prompt_size", 0) + s.get("semantic_size", 0)
        s["saved_ms_total"] = self.saved_ms_total
        return s

    def reset_stats(self) -> None:
        self.prompt.reset_stats()
        if self.semantic is not None:
            self.semantic.reset_stats()


# 模块级单例，进程内共享（与 retrieval_hybrid / asr / oa 一致）
llm_cache = LLMCache()
