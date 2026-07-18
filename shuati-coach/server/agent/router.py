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
