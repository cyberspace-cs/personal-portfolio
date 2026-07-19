"""CoachAgent：基于 LangGraph 同构 StateGraph 的多智能体编排（Supervisor 路由 + 反思 Agent）。

流程对标 Step3「规划-执行 / 反思」范式与 LangGraph Supervisor：
  意图识别(Supervisor) → 路由子 Agent(diagnose/wrongbook/plan/rag_qa) → 反思 Agent 补建议
- 编排层用 agent.supervisor.StateGraph 实现，API 与 LangGraph 同构，生产可一键迁移。
- 上下文预算：五段式（身份/长期画像/诊断摘要/对话历史/当前）由 MemoryStore 统一限额拼接。
- 持久化：短期对话与长期画像存 SQLite，重启不丢（见 agent.memory）。
"""
import json

from agent.llm import call_llm, HAS_KEY
from agent.inference import optimized_call_llm
from agent.tools import CoachTools
from agent.memory import MemoryStore
from agent.supervisor import StateGraph, END
from agent.anomaly import LearningAnomalyDetector


class CoachAgent:
    def __init__(self):
        self.tools = CoachTools()
        self._graph = self._build_graph()

    def _memory(self, user_id: int, session_id: str) -> MemoryStore:
        return MemoryStore(user_id, session_id)

    # ---------- 节点：意图分类（Supervisor） ----------
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
                   "plan(制定学习计划), chat(自由答疑/RAG)。只输出 JSON {intent: 其一}。")
            text = await optimized_call_llm(sys, "用户学习概况：" + ctx_summary + "\n用户说：" + message, 200, json_mode=True)
            data = json.loads(text)
            return data.get("intent", "chat") if data.get("intent") in ("diagnose", "wrongbook", "plan", "chat") else "chat"
        except Exception:
            return "chat"

    # ---------- 节点：各子 Agent ----------
    async def _n_classify(self, state):
        intent = await self._classify(state["message"], state.get("ctx_summary", ""))
        return {"intent": intent}

    async def _n_diagnose(self, state):
        mem = state["mem"]
        diag = self.tools.diagnose(state["user_id"])
        mem.update_long("last_diagnose",
                        json.dumps([w["topic"] for w in diag["weak_topics"]], ensure_ascii=False))
        mem.record_event("diagnose",
                         f"诊断薄弱模块：{', '.join(w['topic'] for w in diag['weak_topics'])}")
        # 学习异常主动预警（AIOps 迁移）：诊断时一并扫描指标异常并主动推送
        detector = LearningAnomalyDetector()
        anomaly = detector.detect(state["user_id"])
        alert = LearningAnomalyDetector.format_alert(anomaly)
        return {"cards": {"weak": diag["weak_topics"], "anomaly": anomaly},
                "anomaly_alert": alert,
                "reply": ("已为你诊断出最薄弱的模块👇 建议优先吃透这些考点，再回来刷变式题巩固。\n\n"
                          + alert)}

    async def _n_wrongbook(self, state):
        mem = state["mem"]
        wb = self.tools.wrong_book(state["user_id"])
        mem.record_event("wrongbook", f"查看高频错题 {len(wb)} 道")
        return {"cards": {"wrong": wb},
                "reply": f"你共有 {len(wb)} 道高频错题（按错误次数排序），先把 error_count 最高的几道吃透。"}

    async def _n_plan(self, state):
        mem = state["mem"]
        diag = self.tools.diagnose(state["user_id"])
        plan = await self.tools.plan(state["user_id"], diag["all"])
        mem.update_long("last_plan", json.dumps(plan.get("focus", []), ensure_ascii=False))
        mem.record_event("plan", f"冲刺重点：{', '.join(plan.get('focus', []))}")
        return {"cards": {"plan": plan},
                "reply": "已基于你的真实掌握度生成冲刺计划👇 我会在后续对话里持续跟进你的进度。"}

    async def _n_rag_qa(self, state):
        mem = state["mem"]
        last_diagnose = mem.get_long("last_diagnose") or ""
        context = mem.build_context(state["message"], last_diagnose)
        rag = await self.tools.rag_qa(state["message"], context, state["user_id"])
        mem.record_event("rag",
                         f"RAG相关={rag.get('relevant')} 引用数={len(rag.get('citations', []))}")
        rag_out = {k: rag.get(k) for k in ("relevant", "citations", "top_score", "threshold", "source")}
        return {"reply": rag.get("reply", ""),
                "rag": rag_out,
                "source_detail": rag.get("source", "rag")}

    # ---------- 节点：反思 Agent（质量校验 + 主动建议） ----------
    async def _n_reflect(self, state):
        intent = state.get("intent")
        reply = state.get("reply", "")
        if intent == "diagnose":
            extra = " 需要我帮你排个冲刺计划吗？"
        elif intent == "plan":
            extra = " 记得每天打卡，我会持续跟进你的掌握度变化～"
        elif intent in ("rag_qa", "chat"):
            extra = " 如果还有不清楚的知识点，随时问我，我可以结合你的错题细讲。"
        else:
            extra = ""
        return {"reply": reply + extra, "reflect": extra}

    # ---------- 图构建（与 LangGraph StateGraph 同构） ----------
    def _build_graph(self):
        g = StateGraph()
        g.add_node("classify", self._n_classify)
        g.add_node("diagnose", self._n_diagnose)
        g.add_node("wrongbook", self._n_wrongbook)
        g.add_node("plan", self._n_plan)
        g.add_node("rag_qa", self._n_rag_qa)
        g.add_node("reflect", self._n_reflect)
        g.set_entry_point("classify")
        g.add_conditional_edges("classify", lambda s: s["intent"], {
            "diagnose": "diagnose", "wrongbook": "wrongbook",
            "plan": "plan", "chat": "rag_qa",
        })
        g.add_edge("diagnose", "reflect")
        g.add_edge("wrongbook", "reflect")
        g.add_edge("plan", "reflect")
        g.add_edge("rag_qa", "reflect")
        g.set_finish_point("reflect")
        return g.compile()

    # ---------- 统一入口 ----------
    async def handle(self, user_id: int, message: str, session_id: str = "default",
                     history=None) -> dict:
        mem = self._memory(user_id, session_id)
        last_diagnose = mem.get_long("last_diagnose") or "暂无诊断记录"
        state = {
            "user_id": user_id, "message": message, "session_id": session_id,
            "mem": mem, "ctx_summary": last_diagnose,
            "intent": None, "cards": {}, "reply": "", "rag": {}, "reflect": "",
            "source_detail": "agent",
        }
        final = await self._graph.invoke(state)
        result = {
            "intent": final["intent"],
            "session_id": session_id,
            "reply": final["reply"],
            "cards": final.get("cards", {}),
            "source": "agent",
            "source_detail": final.get("source_detail", "agent"),
        }
        if final.get("rag"):
            result["rag"] = final["rag"]
        if final.get("anomaly_alert"):
            result["anomaly_alert"] = final["anomaly_alert"]
        # 记忆落盘（短期多轮上下文，持久化）
        mem.add_turn("user", message)
        mem.add_turn("assistant", final.get("reply", ""))
        return result
