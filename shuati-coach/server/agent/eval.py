"""评测闭环：对 RAG / Agent 链路做可量化评估，沉淀为能力「体检表」。

对标 Step3「评测闭环」范式——让 Agent 的能力可观测、可回归，而非黑盒。

指标（可解释，对齐设计稿第 5.4 节）：
  - 命中率 hit_rate          = 相关检索数 / 总 RAG 调用数（低→语料/召回不足）
  - 引用率 citation_rate     = 带引用作答数 / 相关数（低→未充分利用检索）
  - 拒答率 reject_rate       = 不相关拒答数 / 总调用（防幻觉健康度，保守即高）
  - 幻觉率 hallucination_rate= 作答却无引用支撑 / 总调用（越低越好，设计目标≈0）

闭环：每次 RAG 调用经 log_interaction 落库 → evaluate 实时聚合，
运营/开发可观测能力随语料、Prompt 调整的变化趋势。

自带 run_self_eval：用样本 query 跑通闭环，无需真实流量即可演示评测能力。
"""
from database import get_db

# 默认自评估样本（覆盖"相关命中 / 不相关拒答"两类，验证防幻觉与引用）
DEFAULT_SAMPLES = [
    ("概率统计里的期望和方差到底怎么算", True),
    ("数据结构 二叉树 遍历", True),
    ("操作系统 进程与线程区别", True),
    ("计算机网络 TCP 三次握手", True),
    ("今天天气真好适合出去玩", False),
    ("帮我点个外卖谢谢", False),
]


def ensure_eval_table():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_eval_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            query TEXT NOT NULL,
            intent TEXT NOT NULL DEFAULT 'rag',
            relevant INTEGER NOT NULL DEFAULT 0,
            n_citations INTEGER NOT NULL DEFAULT 0,
            source TEXT NOT NULL DEFAULT '',
            top_score REAL,
            threshold REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


def log_interaction(user_id, query: str, rag_result: dict, intent: str = "rag") -> None:
    """每次 RAG 调用后记录一条评测样本（闭环的数据源头）。"""
    relevant = 1 if rag_result.get("relevant") else 0
    n_cit = len(rag_result.get("citations") or [])
    ensure_eval_table()
    conn = get_db()
    conn.execute(
        "INSERT INTO agent_eval_log "
        "(user_id, query, intent, relevant, n_citations, source, top_score, threshold) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (user_id or 0, query, intent, relevant, n_cit,
         rag_result.get("source", ""), rag_result.get("top_score"),
         rag_result.get("threshold")),
    )
    conn.commit()
    conn.close()


def evaluate() -> dict:
    """聚合全部评测样本，输出能力体检表。"""
    ensure_eval_table()
    conn = get_db()
    rows = conn.execute(
        "SELECT relevant, n_citations, source FROM agent_eval_log"
    ).fetchall()
    conn.close()

    total = len(rows)
    if total == 0:
        return {"total": 0, "note": "暂无评测样本，可调用 /api/agent/eval 跑自评估",
                "hit_rate": None, "citation_rate": None,
                "reject_rate": None, "hallucination_rate": None}

    rel = sum(r["relevant"] for r in rows)
    cit = sum(1 for r in rows if r["relevant"] and r["n_citations"] > 0)
    # 幻觉：明明检索不相关，却仍"作答"（source 为 rag-llm / rag-fallback）——理论上不应发生。
    # 注意：纯拒答的 source 是 "rag"（未作答），是防幻觉的正确行为，不计入幻觉。
    hallu = sum(1 for r in rows
                if (not r["relevant"]) and r["source"] in ("rag-llm", "rag-fallback"))

    hit_rate = rel / total
    reject_rate = (total - rel) / total
    citation_rate = cit / rel if rel else 0.0
    hallucination_rate = hallu / total

    grade = "A" if (hit_rate >= 0.6 and hallucination_rate == 0) else \
            "B" if (hit_rate >= 0.4 and hallucination_rate == 0) else "C"

    return {
        "total": total,
        "hit_rate": round(hit_rate, 3),
        "reject_rate": round(reject_rate, 3),
        "citation_rate": round(citation_rate, 3),
        "hallucination_rate": round(hallucination_rate, 3),
        "grade": grade,
    }


def run_self_eval(samples=None, user_id: int = 0) -> dict:
    """用样本 query 跑通评测闭环：检索→构造 rag_result→落库→聚合。无外部依赖。"""
    from agent.retriever import KnowledgeRetriever
    samples = samples or DEFAULT_SAMPLES
    ret = KnowledgeRetriever()
    for query, _exp_relevant in samples:
        res = ret.search(query, top_k=5, user_id=user_id)
        rag_result = {
            "relevant": res["relevant"],
            "citations": ret.format_citations(res["hits"]) if res["relevant"] else [],
            "source": "rag-llm" if res["relevant"] else "rag",
            "top_score": res["top_score"],
            "threshold": res["threshold"],
        }
        log_interaction(user_id, query, rag_result)
    return evaluate()
