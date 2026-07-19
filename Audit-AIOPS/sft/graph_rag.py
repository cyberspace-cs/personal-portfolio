"""
图 RAG 检索演示（LightRAG 思路：图索引 + 双层检索）。

与本项目「纯 numpy/CPU、可当场复现」的套路一致：
- 实体抽取用审计领域词典（确定性、离线、无模型权重），替代 LightRAG 的 LLM 抽取；
- 构建实体共现图（GraphIndex），做 Low-level（具体实体）+ High-level（图扩散）双层检索；
- 与 TF-IDF 关键词召回对比，量化「图扩散多召回」增益——这正是图 RAG 相对向量 RAG 的核心优势
  （尤其像审计这种强领域、实体密集、同义表述多的场景）。

运行：python sft/graph_rag.py  -> 写 sft/data/graph_rag_report.json
"""
import json
import sys
from pathlib import Path

# 允许从项目根 import（app 包）
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.retrieval_hybrid import (  # noqa: E402
    KeywordRetriever,
    HybridRetriever,
    GraphRAGRetriever,
)
from app.services.knowledge_base import KB_DOCS  # noqa: E402


def _titles(docs, hits):
    return [docs[h["doc_index"]]["title"] for h in hits]


def main():
    docs = KB_DOCS
    kw = KeywordRetriever(docs, top_k=6)
    graph_ret = GraphRAGRetriever(docs, top_k=6, hops=2)
    hybrid = HybridRetriever(docs, embedding_backend="local", top_k=3, enable_graph=False)
    graph_hybrid = HybridRetriever(docs, embedding_backend="local", top_k=3, enable_graph=True)

    queries = [
        "Ukey 制作后怎么回收？需要哪些审批",
        "资产领用后如何巡检和签收",
        "审批流怎么自动拆单并路由责任人",
        "怎么监控异常并自动生成工单",
        "数据飞轮怎么驱动 SFT 优化模型",
        "权限变更为什么需要双人审批和留痕合规",
    ]

    sample = []
    extra_counts = []
    for q in queries:
        kw_hits = _titles(docs, kw.search(q, 6))
        g = graph_ret.search(q, 6)
        g_hits = _titles(docs, g)
        gh_hits = _titles(docs, graph_hybrid.search(q, 3))
        hy_hits = _titles(docs, hybrid.search(q, 3))
        exp = graph_ret.explain(q)
        extra = sorted(set(g_hits) - set(kw_hits))
        extra_counts.append(len(extra))
        sample.append(
            {
                "query": q,
                "kw_hits": kw_hits,
                "graph_hits": g_hits,
                "hybrid_top3": hy_hits,
                "graph_hybrid_top3": gh_hits,
                "graph_extra_via_expansion": extra,
                "query_entities": exp["query_entities"],
                "expanded_entities": exp["expanded_entities"],
                "edges": exp["edges"],
            }
        )

    # 图统计
    gi = graph_ret.graph
    degrees = {e: sum(gi.adj[e].values()) for e in gi.adj}
    avg_deg = (sum(degrees.values()) / len(degrees)) if degrees else 0
    top_entity = max(degrees.items(), key=lambda x: x[1]) if degrees else ("-", 0)

    report = {
        "method": "graph_rag_lightrag_style",
        "note": (
            "LightRAG 思路的轻量领域版：图索引(实体共现图)+双层检索(具体实体+图扩散)。"
            "实体抽取用审计领域词典替代 LLM，纯 CPU/零依赖可复现；与关键词/向量 RRF 融合为三路混合检索。"
        ),
        "graph_stats": {
            "docs": len(docs),
            "entities": len(gi.entity_docs),
            "edges": sum(len(v) for v in gi.adj.values()),
            "avg_degree": round(avg_deg, 2),
            "max_degree_entity": top_entity[0],
            "max_degree": top_entity[1],
        },
        "sample_queries": sample,
        "summary": {
            "queries_total": len(queries),
            "queries_with_graph_expansion": sum(1 for c in extra_counts if c > 0),
            "avg_graph_extra_recall": round(sum(extra_counts) / len(extra_counts), 2),
            "max_graph_extra_recall": max(extra_counts),
        },
        "repro": "python sft/graph_rag.py",
    }

    out = ROOT / "sft" / "data" / "graph_rag_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 图 RAG 报告已写: {out}")
    print(
        f"   实体数={report['graph_stats']['entities']} 边数={report['graph_stats']['edges']} "
        f"平均度={avg_deg:.2f} 中枢实体={top_entity[0]}"
    )
    print(
        f"   含图扩散增益的查询={report['summary']['queries_with_graph_expansion']}/{len(queries)} "
        f"平均多召回={report['summary']['avg_graph_extra_recall']}"
    )


if __name__ == "__main__":
    main()
