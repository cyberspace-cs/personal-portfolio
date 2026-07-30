"""Agent 入口路由：统一对话入口 /api/agent/chat（经 Channel 接入层分发）。"""
from fastapi import APIRouter
from pydantic import BaseModel

from agent.channel import HUB
from agent.inference import run_infer_demo, LEDGER, QUANT_CONFIG

router = APIRouter()
_agent = HUB.agent


class AgentChatIn(BaseModel):
    user_id: int
    message: str
    session_id: str = "default"   # 支持多会话隔离（同一用户可开多个备考会话）
    history: list = []


@router.post("/api/agent/chat")
async def agent_chat(data: AgentChatIn):
    """自然语言驱动的统一备考 Agent 入口（经 Channel 接入层 ApiChannel 分发）。

    返回：{ intent, reply, cards?, source, source_detail?, session_id }
      - intent: diagnose / wrongbook / plan / chat
      - cards:  结构化卡片（诊断/错题/计划），前端可渲染为卡片
      - session_id: 回显会话标识，便于前端维护多会话上下文
    """
    out = await HUB.dispatch_api(data.user_id, data.message, data.session_id)
    return {
        "intent": out.intent,
        "session_id": out.session_id,
        "reply": out.content,
        "cards": out.cards,
        "source": out.source,
        **out.extra,
    }


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
    await mem.add_turn("user", data.message)
    await mem.add_turn("assistant", rag.get("reply", ""))
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


@router.post("/api/agent/anomaly")
async def agent_anomaly(data: AgentChatIn):
    """学习异常检测（AIOps 迁移）：扫描正确率骤降/连续断签/错题反复，主动预警。"""
    from agent.anomaly import LearningAnomalyDetector
    detector = LearningAnomalyDetector()
    result = detector.detect(data.user_id)
    result["alert_text"] = LearningAnomalyDetector.format_alert(result)
    return result


@router.post("/api/agent/eval")
async def agent_eval(data: AgentChatIn, run_self: bool = False):
    """评测闭环：聚合 RAG 调用样本，输出引用率/幻觉率/命中率等能力体检表。

    可选 ?run_self=true 先跑内置自评估样本再聚合（无需真实流量即可演示）。
    """
    from agent.eval import run_self_eval, evaluate
    metrics = run_self_eval() if run_self else evaluate()
    return {"eval": metrics, "ran_self_eval": run_self}


@router.post("/api/agent/infer/optimize")
async def agent_infer_optimize(data: AgentChatIn):
    """推理优化自演示（Phase F）：一次性把 7 项 LLM 推理优化跑出可量化结果。

    无需 API Key / GPU：KV 前缀缓存、上下文压缩、投机解码、知识蒸馏、
    连续批处理、工具替代生成、量化/AWQ 配置——全部返回实测指标。
    面试可直接调用该端点展示『研发深度』。
    """
    result = await run_infer_demo()
    return {"infer_optimization": result, "note": "全部优化均可在无 Key/无 GPU 环境本地量化演示"}


@router.get("/api/agent/infer/status")
async def agent_infer_status():
    """推理优化实时台账：累计的省 token / 接受率 / 工具替代 / 量化模式等。"""
    return {"ledger": LEDGER.to_dict(), "quant_config": QUANT_CONFIG}


@router.get("/api/agent/providers")
async def agent_providers():
    """列出所有可切换的大模型厂商（智谱/Kimi/混元/豆包/千问/DeepSeek/OpenAI）。

    返回每家是否已配置 Key、默认模型、当前激活厂商，便于前端做「模型选择器」。
    """
    from agent.llm import list_providers, active_provider
    return {"active": active_provider(), "providers": list_providers()}


class ProviderSwitchIn(BaseModel):
    provider: str


@router.post("/api/agent/providers/switch")
async def agent_providers_switch(data: ProviderSwitchIn):
    """运行期切换激活厂商（需该厂商已配置 Key）。"""
    from agent.llm import switch_provider
    try:
        return {"ok": True, "active": switch_provider(data.provider)}
    except ValueError as e:
        return {"ok": False, "error": str(e)}


@router.get("/api/agent/channels")
async def agent_channels():
    """列出已注册的接入渠道（api / cli / 未来飞书 / 微信 / Telegram …）。

    印证「一个 Agent core + 多 Channel」的 nanobot 式架构；新渠道注册到 AgentHub 即可，
    Agent 代码无需改动——这正是未来 Vibe-Trading / Deep Tutor 复用同一 core 的基础。
    """
    return {"active_channels": HUB.list_channels()}


class AgentHistoryIn(BaseModel):
    user_id: int
    session_id: str = "default"
    keyword: str = ""
    limit: int = 50


@router.post("/api/agent/history")
async def agent_history(data: AgentHistoryIn):
    """检索用户的中长期事件日志（nanobot HISTORY.md 同构，append-only 可 grep）。

    keyword 留空取最近 limit 条；填入关键词则按 payload 模糊匹配（可 grep）。
    """
    from agent.memory import MemoryStore
    mem = MemoryStore(data.user_id, data.session_id)
    return {"events": mem.search_history(data.keyword, data.limit),
            "session_id": data.session_id}


@router.get("/api/agent/mcp/tools")
async def agent_mcp_tools():
    """列出可用 MCP 工具（内置 + 配置了 MCP_SERVER_URL 时的远程工具）。"""
    tools = await _agent.tools.list_mcp_tools()
    return {"tools": tools}


class MCPCallIn(BaseModel):
    tool: str
    arguments: dict = {}


@router.post("/api/agent/mcp/call")
async def agent_mcp_call(data: MCPCallIn):
    """调用一个 MCP 工具（垂直能力：考纲检索 / 题库检索 / 远程行情…）。"""
    return await _agent.tools.mcp_call(data.tool, data.arguments)
