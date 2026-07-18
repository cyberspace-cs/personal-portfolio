"""CoachAgent：轻量编排器（生产环境以 LangGraph StateGraph 实现同构逻辑）。

流程对标 Step3「规划-执行 / 反思」范式：
  意图识别 → 工具调度 → 反思格式化 → 记忆更新
- Supervisor 角色：意图分类后派发到具体工具（diagnose/wrongbook/plan/chat）。
- 反思角色：诊断后主动补一句建议；规划后回带 focus 模块。
- 上下文预算：五段式（身份/长期画像/诊断摘要/对话历史/当前）由 MemoryStore 统一限额拼接。
- 持久化：短期对话与长期画像存 SQLite，重启不丢（见 agent.memory）。
"""
import json

from agent.llm import call_llm, HAS_KEY
from agent.tools import CoachTools
from agent.memory import MemoryStore

INTENTS = ["diagnose", "wrongbook", "plan", "chat"]


class CoachAgent:
    def __init__(self):
        self.tools = CoachTools()

    def _memory(self, user_id: int, session_id: str) -> MemoryStore:
        return MemoryStore(user_id, session_id)

    async def _classify(self, message: str, ctx_summary: str) -> str:
        # 规则兜底意图识别（无 Key 或 LLM 失败时使用）
        if not HAS_KEY:
            m = message
            if any(k in m for k in ["薄弱", "弱项", "掌握度", "哪里差", "不会", "差在哪"]):
                return "diagnose"
            if any(k in m for k in ["错题", "错在哪", "易错"]):
                return "wrongbook"
            if any(k in m for k in ["计划", "怎么学", "怎么安排", "冲刺", "押题", "安排"]):
                return "plan"
            return "chat"
        try:
            sys = ("你是意图分类器。可选意图：diagnose(薄弱度诊断), wrongbook(查错题本), "
                   "plan(制定学习计划), chat(自由答疑)。只输出 JSON {intent: 其一}。")
            text = await call_llm(sys, "用户学习概况：" + ctx_summary + "\n用户说：" + message, 200, json_mode=True)
            data = json.loads(text)
            return data.get("intent", "chat") if data.get("intent") in INTENTS else "chat"
        except Exception:
            return "chat"

    async def handle(self, user_id: int, message: str, session_id: str = "default",
                     history=None) -> dict:
        mem = self._memory(user_id, session_id)
        last_diagnose = mem.get_long("last_diagnose") or "暂无诊断记录"
        ctx_summary = last_diagnose

        intent = await self._classify(message, ctx_summary)
        result: dict = {"intent": intent, "session_id": session_id}

        if intent == "diagnose":
            diag = self.tools.diagnose(user_id)
            mem.update_long("last_diagnose",
                            json.dumps([w["topic"] for w in diag["weak_topics"]], ensure_ascii=False))
            result["cards"] = {"weak": diag["weak_topics"]}
            # 反思 Agent：主动补建议
            result["reply"] = ("已为你诊断出最薄弱的模块👇 建议优先吃透这些考点，"
                               "再回来刷变式题巩固。需要我帮你排个冲刺计划吗？")

        elif intent == "wrongbook":
            wb = self.tools.wrong_book(user_id)
            result["cards"] = {"wrong": wb}
            result["reply"] = f"你共有 {len(wb)} 道高频错题（按错误次数排序），先把 error_count 最高的几道吃透。"

        elif intent == "plan":
            diag = self.tools.diagnose(user_id)
            plan = await self.tools.plan(user_id, diag["all"])
            mem.update_long("last_plan",
                            json.dumps(plan.get("focus", []), ensure_ascii=False))
            result["cards"] = {"plan": plan}
            result["reply"] = "已基于你的真实掌握度生成冲刺计划👇 我会在后续对话里持续跟进你的进度。"

        else:  # chat → RAG 问答（检索知识点/考纲/错题 + 引用溯源 + 防幻觉）
            context = mem.build_context(message, last_diagnose)
            rag = await self.tools.rag_qa(message, context, user_id)
            result["reply"] = rag.get("reply", "")
            result["rag"] = {
                "relevant": rag.get("relevant"),
                "citations": rag.get("citations", []),
                "top_score": rag.get("top_score"),
                "threshold": rag.get("threshold"),
                "source": rag.get("source"),
            }
            result["source_detail"] = rag.get("source", "rag")

        # 记忆更新（短期多轮上下文，持久化）
        mem.add_turn("user", message)
        mem.add_turn("assistant", result.get("reply", ""))
        result["source"] = "agent"
        return result
