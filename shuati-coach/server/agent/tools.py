"""教练工具集：把既有后端能力封装为 Agent 可调用的 Tool（Function Calling 思路）。

每个方法对应一个可被 Agent 调度的"工具"：
  diagnose   -> 薄弱度诊断（复用 mastery 计算）
  wrong_book -> 查高频错题
  plan       -> 基于真实掌握度生成学习计划（LLM）
  chat       -> 自由答疑（LLM，注入用户上下文）
"""
import json

from database import get_db
from agent.llm import call_llm, HAS_KEY


class CoachTools:
    # ① 薄弱度诊断：聚合错题，按知识点计算掌握度，输出最弱 Top3
    def diagnose(self, user_id: int) -> dict:
        conn = get_db()
        rows = conn.execute(
            """
            SELECT q.topic,
                   COUNT(DISTINCT wb.question_id) as wrong_count,
                   (SELECT COUNT(*) FROM questions WHERE topic=q.topic) as total_count
            FROM wrong_book wb JOIN questions q ON wb.question_id = q.id
            WHERE wb.user_id=? GROUP BY q.topic
            """,
            (user_id,),
        ).fetchall()
        all_topics = [r["topic"] for r in conn.execute("SELECT DISTINCT topic FROM questions").fetchall()]
        conn.close()

        weak_map = {r["topic"]: r["wrong_count"] for r in rows}
        full = []
        for t in all_topics:
            wrong = weak_map.get(t, 0)
            mastery = max(0, 100 - wrong * 15)
            full.append({"topic": t, "wrong": wrong, "mastery": mastery})
        full.sort(key=lambda x: x["mastery"])
        return {"weak_topics": full[:3], "all": full}

    # ② 高频错题本：按错误次数降序
    def wrong_book(self, user_id: int, limit: int = 10) -> list:
        conn = get_db()
        rows = conn.execute(
            """
            SELECT wb.question_id, wb.error_count, q.stem, q.topic
            FROM wrong_book wb JOIN questions q ON wb.question_id = q.id
            WHERE wb.user_id=? ORDER BY wb.error_count DESC LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ③ 学习计划：基于真实掌握度，LLM 生成；无 Key 走模板降级
    async def plan(self, user_id: int, mastery_all: list) -> dict:
        weak = [m for m in mastery_all if m["mastery"] < 70]
        if not HAS_KEY:
            return {
                "source": "fallback",
                "focus": [w["topic"] for w in weak],
                "plan": [
                    "每天优先完成系统推送的薄弱点题目。",
                    "对错误≥3次的题目进行深度复盘。",
                    "每周做一次模拟考场，检验掌握度变化。",
                ],
            }
        try:
            sys = "你是备考规划师，基于掌握度输出紧凑 JSON：{focus:[薄弱模块], plan:[3条冲刺建议]}，中文。"
            user = "当前掌握度：" + json.dumps(weak, ensure_ascii=False)
            text = await call_llm(sys, user, 600, json_mode=True)
            data = json.loads(text)
            data["source"] = "llm"
            return data
        except Exception:
            return {"source": "fallback", "focus": [w["topic"] for w in weak],
                    "plan": ["每天优先刷系统推送的薄弱点题", "深度复盘高频错题", "每周模拟考"]}

    # ④ 自由答疑：注入用户学习概况，LLM 回答；无 Key 降级
    async def chat(self, message: str, context: str) -> dict:
        if not HAS_KEY:
            return {"source": "fallback", "reply": "智能教练暂未接入大模型，先去刷几道题热热身吧～"}
        sys = ("你是「专属刷题教练」AI，基于用户学习数据用中文回答备考问题，"
               "不编造未提供的数据，不确定时诚实说明。")
        text = await call_llm(sys, context + "\n用户：" + message, 700)
        return {"source": "llm", "reply": text or "教练开小差了，请稍后再问～"}

    # ⑤ RAG 问答：检索知识点/考纲/用户错题 → 引用溯源 → 低相关拒答（防幻觉）
    async def rag_qa(self, message: str, context: str = "", user_id=None) -> dict:
        if not hasattr(self, "retriever"):
            from agent.retriever import KnowledgeRetriever
            self.retriever = KnowledgeRetriever()
        res = self.retriever.search(message, top_k=5, user_id=user_id)
        hits = res["hits"]
        citations = self.retriever.format_citations(hits)
        if not res["relevant"]:
            # 防幻觉：检索相关性不足时明确拒答，绝不编造
            return {
                "source": "rag", "relevant": False,
                "reply": ("抱歉，我在知识点库和你的错题里没找到足够相关的资料，"
                          "无法保证回答准确，先不瞎编啦～你可以换个更具体的问法，"
                          "或先去刷几道相关题再来问。"),
                "citations": [],
                "top_score": res["top_score"], "threshold": res["threshold"],
            }
        if not HAS_KEY:
            reply = self._fallback_rag_answer(message, hits, citations)
            return {"source": "rag-fallback", "relevant": True, "reply": reply,
                    "citations": citations, "top_score": res["top_score"],
                    "threshold": res["threshold"]}
        sys = ("你是「专属刷题教练」AI。下面是你检索到的知识点与用户错题（带编号引用）。"
               "请仅基于这些引用内容回答用户问题，在相关论断后标注 [n] 引用编号；"
               "若引用内容不足以回答，请明确说明，不要编造。语言通俗、面向备考学生。")
        knowledge = "\n\n".join(
            f"[{i+1}] {h['title']}\n{h['content']}" for i, h in enumerate(hits)
        )
        user = f"【检索到的参考知识】\n{knowledge}\n\n【上下文】\n{context}\n\n用户问题：{message}"
        text = await call_llm(sys, user, 800)
        return {"source": "rag-llm", "relevant": True,
                "reply": text or "教练开小差了，请稍后再问～",
                "citations": citations, "top_score": res["top_score"],
                "threshold": res["threshold"]}

    def _fallback_rag_answer(self, message: str, hits: list, citations: list) -> str:
        top = hits[0]
        snippet = top["content"]
        if len(snippet) > 220:
            snippet = snippet[:220] + "…"
        head = (f"根据检索到的资料，关于「{top['topic']}」（{top['cat']}）"
                f"可以这样理解：\n{snippet}\n")
        tail = ("建议结合你的错题进一步练习，遇到具体题目可以让我帮你讲透。"
                if top.get("kind") == "user_wrong" else
                "建议把相关错题加入错题本，按遗忘曲线复习巩固。")
        cite_block = "\n".join(citations)
        return f"{head}\n{tail}\n\n📚 参考来源：\n{cite_block}"
