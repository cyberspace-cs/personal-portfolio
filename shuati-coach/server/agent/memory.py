"""分层记忆：短期（会话滑窗）+ 长期（用户画像/错题沉淀），均持久化到 SQLite。

设计对标 Step3 提取的 pico「分层上下文预算 / 结构化记忆」：
- 短期记忆 = 单 session 对话上下文（按 token 预算截断的滑窗），支撑多轮；
- 长期记忆 = 用户稳定事实（最近一次诊断、偏好），跨会话保留，避免每次"失忆"。

持久化：
- 长期画像存于 agent_profile 表（user_id 主键，profile JSON）；
- 短期对话存于 agent_short_term 表（user_id + session_id + 序号）。
- 与业务库 coach.db 共用连接（database.get_db），启动时由 ensure_tables 建表。

六段式上下文预算（build_context）：把喂给 LLM 的上下文切分为六段并分别限额，
[1] 系统身份 [2] 长期画像 [3] 诊断/工具摘要 [4] 短期对话滑窗 [5] 近期事件 [6] 当前消息+工具结果。
总预算默认 ~4100 字符（约 1.3k token），超出则按"远段优先丢弃"回退。

上下文感知压缩（滚动摘要，context-aware compression）：
- 问题：长期多轮对话会让 [4] 短期滑窗无限膨胀，若直接"删最旧轮"（早期实现）会丢关键信息；
- 方案：滑窗溢出时，把溢出的旧对话交给 LLM 滚动压成"对话要点摘要"（running summary），
  存入 agent_conv_summary 表，再删原文。近窗保留原文、远窗保留摘要 —— 与 LangChain
  ConversationSummaryBufferMemory 同构，但摘要按 session 持久化（可跨重启恢复）。
- 降级：无 API Key 时退化为"要点截断拼接"，仍是上下文感知（保留关键句而非整段删除）。
"""
import json
import re

from database import get_db
from agent.llm import call_llm, HAS_KEY
try:
    from agent.inference import token_estimate, LEDGER
except Exception:  # inference 不可用时退化为纯字符启发式，避免跨模块依赖脆弱
    def token_estimate(text: str) -> int:
        return len(text or "") // 4 + 1
    class _StubLedger:
        compressed_saved = 0
    LEDGER = _StubLedger()

SHORT_LIMIT = 12          # 短期滑窗保留的最大轮数（user+assistant 计一轮）
PROFILE_KEYS = ("last_diagnose", "last_plan", "preferred_cat", "preferred_name", "notes")

# 六段式预算（字符数，约 3 字符/token 估算）
BUDGET = {
    "identity": 240,
    "profile": 420,
    "summary": 520,
    "short": 1500,
    "history": 380,   # 中长期事件日志（append-only，可 grep），nanobot HISTORY.md 同构
    "current": 1100,
}


def ensure_tables():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS agent_profile (
            user_id INTEGER PRIMARY KEY,
            profile TEXT NOT NULL DEFAULT '{}',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS agent_short_term (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT NOT NULL DEFAULT 'default',
            seq INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_agent_st_user_session
            ON agent_short_term(user_id, session_id, seq);
        CREATE TABLE IF NOT EXISTS agent_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT NOT NULL DEFAULT 'default',
            kind TEXT NOT NULL,      -- diagnose/plan/rag/wrongbook/milestone/anomaly ...
            payload TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_agent_hist_user
            ON agent_history(user_id, created_at);
        CREATE TABLE IF NOT EXISTS agent_conv_summary (
            user_id INTEGER NOT NULL,
            session_id TEXT NOT NULL DEFAULT 'default',
            summary TEXT NOT NULL DEFAULT '',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, session_id)
        );
    """)
    conn.commit()
    conn.close()


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 12)] + " …(已截断)"


class MemoryStore:
    """SQLite 持久化的分层记忆。单进程内按 user_id 缓存实例。"""

    _instances: dict = {}

    def __new__(cls, user_id: int, session_id: str = "default"):
        key = (user_id, session_id)
        inst = cls._instances.get(key)
        if inst is None:
            inst = super().__new__(cls)
            inst.user_id = user_id
            inst.session_id = session_id
            inst._cache = None  # 短期对话内存缓存（启动后首次加载）
            cls._instances[key] = inst
        return inst

    # ---------- 长期记忆 ----------
    def get_long(self, key=None):
        conn = get_db()
        row = conn.execute(
            "SELECT profile FROM agent_profile WHERE user_id=?", (self.user_id,)
        ).fetchone()
        conn.close()
        prof = json.loads(row["profile"]) if row else {}
        return prof.get(key) if key else prof

    def update_long(self, key, value) -> None:
        if key not in PROFILE_KEYS:
            key = "notes"  # 未知键归入自由备注，避免无界膨胀
        prof = dict(self.get_long() or {})
        prof[key] = value
        conn = get_db()
        conn.execute(
            "INSERT INTO agent_profile (user_id, profile, updated_at) VALUES (?,?,CURRENT_TIMESTAMP) "
            "ON CONFLICT(user_id) DO UPDATE SET profile=excluded.profile, updated_at=CURRENT_TIMESTAMP",
            (self.user_id, json.dumps(prof, ensure_ascii=False)),
        )
        conn.commit()
        conn.close()

    # ---------- 短期记忆 ----------
    def _load_short(self) -> list:
        conn = get_db()
        rows = conn.execute(
            "SELECT role, content FROM agent_short_term "
            "WHERE user_id=? AND session_id=? ORDER BY seq",
            (self.user_id, self.session_id),
        ).fetchall()
        conn.close()
        return [{"role": r["role"], "content": r["content"]} for r in rows]

    async def add_turn(self, role: str, content: str) -> None:
        conn = get_db()
        cur = conn.execute(
            "SELECT COALESCE(MAX(seq),0) AS m FROM agent_short_term "
            "WHERE user_id=? AND session_id=?",
            (self.user_id, self.session_id),
        ).fetchone()
        seq = (cur["m"] or 0) + 1
        conn.execute(
            "INSERT INTO agent_short_term (user_id, session_id, seq, role, content) "
            "VALUES (?,?,?,?,?)",
            (self.user_id, self.session_id, seq, role, content),
        )
        # 滑窗 + 上下文感知压缩：超出 SHORT_LIMIT 轮时，把溢出的【旧对话】压缩成
        # 滚动摘要（而非直接删除），近窗保留原文、远窗保留要点 —— 防止信息丢失。
        cutoff = seq - SHORT_LIMIT
        if cutoff > 0:
            old_rows = conn.execute(
                "SELECT role, content FROM agent_short_term "
                "WHERE user_id=? AND session_id=? AND seq<=? ORDER BY seq",
                (self.user_id, self.session_id, cutoff),
            ).fetchall()
            if old_rows:
                old_text = "\n".join(
                    f"{'用户' if r['role']=='user' else '教练'}：{r['content']}"
                    for r in old_rows
                )
                # 把旧对话滚动并入现有摘要（同一连接内写，避免并发锁）
                prev_summary = self.get_summary()
                new_summary = await self._summarize(old_text, prev_summary)
                conn.execute(
                    "INSERT INTO agent_conv_summary (user_id, session_id, summary, updated_at) "
                    "VALUES (?,?,?,CURRENT_TIMESTAMP) "
                    "ON CONFLICT(user_id, session_id) DO UPDATE SET summary=excluded.summary, updated_at=CURRENT_TIMESTAMP",
                    (self.user_id, self.session_id, new_summary),
                )
                conn.execute(
                    "DELETE FROM agent_short_term WHERE user_id=? AND session_id=? AND seq<=?",
                    (self.user_id, self.session_id, cutoff),
                )
        conn.commit()
        conn.close()

    # ---------- 上下文感知压缩：滚动摘要 ----------
    def get_summary(self) -> str:
        """读取当前会话的滚动对话摘要（无则空串）。"""
        conn = get_db()
        row = conn.execute(
            "SELECT summary FROM agent_conv_summary WHERE user_id=? AND session_id=?",
            (self.user_id, self.session_id),
        ).fetchone()
        conn.close()
        return row["summary"] if row else ""

    async def _summarize(self, new_dialogue: str, prev_summary: str) -> str:
        """滚动摘要：把一段新对话合并进既有摘要。

        - 有 Key：调 LLM 做"增量压缩"（保留关键决策/结论/用户偏好，丢弃寒暄冗余）；
        - 无 Key：退化抽取式要点拼接（按句子重要度截断），仍是上下文感知而非无脑删除。
        返回压缩后的新摘要文本。
        """
        if prev_summary and not new_dialogue.strip():
            return prev_summary
        if HAS_KEY:
            sys = ("你是对话压缩器。把『已有摘要』与『新增对话』合并为一段不超过 "
                   "300 字的要点摘要，保留：用户的学习诉求、已做的诊断/计划结论、"
                   "未解决的问题、关键偏好。丢弃寒暄、重复、无关内容。只输出摘要文本。")
            user = f"已有摘要：\n{prev_summary or '（无）'}\n\n新增对话：\n{new_dialogue}"
            try:
                out = await call_llm(sys, user, 360) or ""
                if out.strip():
                    saved = token_estimate(new_dialogue) - token_estimate(out)
                    LEDGER.compressed_saved += max(0, saved)
                    return out.strip()
            except Exception:
                pass
        # 降级：抽取式要点（取每轮首句，截断到预算）
        sents = [s for s in re.split(r"(?<=[。！？\n])", new_dialogue) if s.strip()]
        merged = (prev_summary + "\n" if prev_summary else "") + "\n".join(sents)
        if len(merged) > 900:
            merged = merged[:888] + " …(压缩截断)"
        saved = token_estimate(new_dialogue) - token_estimate(merged)
        LEDGER.compressed_saved += max(0, saved)
        return merged

    def short_context(self) -> list:
        return self._load_short()

    def clear_session(self) -> None:
        conn = get_db()
        conn.execute(
            "DELETE FROM agent_short_term WHERE user_id=? AND session_id=?",
            (self.user_id, self.session_id),
        )
        conn.execute(
            "DELETE FROM agent_conv_summary WHERE user_id=? AND session_id=?",
            (self.user_id, self.session_id),
        )
        conn.commit()
        conn.close()

    # ---------- 中长期事件日志（nanobot HISTORY.md 同构，append-only 可 grep） ----------
    def record_event(self, kind: str, payload: str) -> None:
        """记录一条中长期事件（诊断/计划/RAG/里程碑…），append-only，供后续 grep 检索。"""
        conn = get_db()
        conn.execute(
            "INSERT INTO agent_history (user_id, session_id, kind, payload) VALUES (?,?,?,?)",
            (self.user_id, self.session_id, kind, payload),
        )
        conn.commit()
        conn.close()

    def search_history(self, keyword: str = "", limit: int = 50) -> list:
        """检索中长期事件：无 keyword 取最近 limit 条；有 keyword 按 payload LIKE 模糊匹配。"""
        conn = get_db()
        if keyword:
            rows = conn.execute(
                "SELECT kind, payload, created_at FROM agent_history "
                "WHERE user_id=? AND payload LIKE ? ORDER BY created_at DESC LIMIT ?",
                (self.user_id, f"%{keyword}%", limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT kind, payload, created_at FROM agent_history "
                "WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                (self.user_id, limit),
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _recent_events(self, limit: int = 6) -> str:
        """取最近 limit 条事件，拼成可注入上下文的中长期摘要。"""
        rows = self.search_history("", limit)
        if not rows:
            return "（暂无中长期事件）"
        return "\n".join(f"- [{r['kind']}] {r['payload']}" for r in rows)

    # ---------- 六段式上下文预算拼接 ----------
    def build_context(self, message: str, tool_summary: str = "") -> str:
        """把五段上下文按预算拼成一段文本，供 LLM 使用。"""
        identity = ("你是「专属刷题教练」AI：一位永远在线、永不嫌烦的备考教练。"
                    "基于用户真实学习数据作答，不编造未提供的数据；不确定时诚实说明。")
        profile = self.get_long()
        prof_parts = []
        if profile.get("preferred_name"):
            prof_parts.append(f"用户昵称：{profile['preferred_name']}")
        if profile.get("preferred_cat"):
            prof_parts.append(f"备考方向：{profile['preferred_cat']}")
        if profile.get("last_diagnose"):
            prof_parts.append(f"最近诊断薄弱模块：{profile['last_diagnose']}")
        if profile.get("last_plan"):
            prof_parts.append(f"最近计划重点：{profile['last_plan']}")
        if profile.get("notes"):
            prof_parts.append(f"备注：{profile['notes']}")
        profile_txt = "；".join(prof_parts) if prof_parts else "暂无长期画像"

        short = self.short_context()
        short_txt = "\n".join(f"{'用户' if t['role']=='user' else '教练'}：{t['content']}"
                              for t in short[-SHORT_LIMIT:]) or "（无近期对话）"
        # 上下文感知压缩产物：滑窗溢出被压缩掉的旧对话要点（远窗摘要）
        conv_summary = self.get_summary()

        history_txt = self._recent_events()
        seg = {
            "identity": _truncate(identity, BUDGET["identity"]),
            "profile": _truncate(profile_txt, BUDGET["profile"]),
            "summary": _truncate(tool_summary or "无", BUDGET["summary"]),
            "short": _truncate(
                # 远窗摘要（被压缩的旧对话）+ 近窗原文（最近 SHORT_LIMIT 轮）
                (f"[更早对话压缩摘要] {conv_summary}\n" if conv_summary else "")
                + f"[最近对话] {short_txt}",
                BUDGET["short"],
            ),
            "history": _truncate(history_txt, BUDGET["history"]),
            "current": _truncate(
                ("用户当前说：" + message) + (("\n诊断/工具摘要：" + tool_summary) if tool_summary else ""),
                BUDGET["current"],
            ),
        }
        return (
            f"[身份] {seg['identity']}\n"
            f"[长期画像] {seg['profile']}\n"
            f"[诊断摘要] {seg['summary']}\n"
            f"[对话历史(含压缩)] {seg['short']}\n"
            f"[近期事件] {seg['history']}\n"
            f"[当前] {seg['current']}"
        )
