"""Agent 入口路由：统一对话入口 /api/agent/chat。"""
from fastapi import APIRouter
from pydantic import BaseModel

from agent.orchestrator import CoachAgent

router = APIRouter()
_agent = CoachAgent()


class AgentChatIn(BaseModel):
    user_id: int
    message: str
    session_id: str = "default"   # 支持多会话隔离（同一用户可开多个备考会话）
    history: list = []


@router.post("/api/agent/chat")
async def agent_chat(data: AgentChatIn):
    """自然语言驱动的统一备考 Agent 入口。

    返回：{ intent, reply, cards?, source, source_detail?, session_id }
      - intent: diagnose / wrongbook / plan / chat
      - cards:  结构化卡片（诊断/错题/计划），前端可渲染为卡片
      - session_id: 回显会话标识，便于前端维护多会话上下文
    """
    return await _agent.handle(data.user_id, data.message, data.session_id, data.history)


@router.post("/api/agent/session/clear")
async def agent_session_clear(data: AgentChatIn):
    """清空指定会话的短期记忆（长期画像保留）。"""
    from agent.memory import MemoryStore
    MemoryStore(data.user_id, data.session_id).clear_session()
    return {"ok": True, "session_id": data.session_id}


@router.post("/api/agent/rag")
async def agent_rag(data: AgentChatIn):
    """RAG 问答：检索知识点/考纲/用户错题后作答，标注引用来源，低相关拒答（防幻觉）。"""
    from agent.memory import MemoryStore
    mem = MemoryStore(data.user_id, data.session_id)
    last_diagnose = mem.get_long("last_diagnose") or ""
    context = mem.build_context(data.message, last_diagnose)
    rag = await _agent.tools.rag_qa(data.message, context, data.user_id)
    mem.add_turn("user", data.message)
    mem.add_turn("assistant", rag.get("reply", ""))
    return {
        "intent": "rag",
        "reply": rag.get("reply", ""),
        "relevant": rag.get("relevant"),
        "citations": rag.get("citations", []),
        "top_score": rag.get("top_score"),
        "threshold": rag.get("threshold"),
        "source": rag.get("source"),
        "session_id": data.session_id,
    }
