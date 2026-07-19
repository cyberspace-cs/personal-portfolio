"""智能客服：意图路由(Skill) + 工具调用(MCP) + 知识库(RAG) + 上下文闭环(Context)。

流程：用户消息 → Skill 识别意图 → 必要时 MCP 调用外部系统（查订单/退款/转人工）
      → 无工具命中则用 HybridRetriever 在 FAQ 知识库检索 → LLM/规则生成回复 → 写回上下文。
完整体现「Skill + MCP + RAG + Context Harness Loop」的组合用法。
"""
import time
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.llm import LLMClient
from app.core.skill import SkillRegistry
from app.core.mcp import MCPConnector
from app.core.rag import HybridRetriever
from app.core.context import ContextHarness

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])

llm = LLMClient()
skills = SkillRegistry()
mcp = MCPConnector()
faq = HybridRetriever(dims=512)
_sessions: dict[str, ContextHarness] = []

# ---------- FAQ 知识库（内置示例，可 ingest 扩充） ----------
_FAQ = [
    ("如何使用产品", "登录后进入控制台，点击「新建任务」即可创建。新手建议先阅读快速开始指南，3 分钟完成首次配置。"),
    ("支持哪些模型", "平台支持 Qwen、DeepSeek、GLM 等主流开源模型，以及通过 API 接入的闭源模型，满足微调与推理需求。"),
    ("如何申请退款", "在「订单中心」选择对应订单，点击「申请退款」，审核通过后 1-3 个工作日原路退回。"),
    ("订单物流查询", "进入「我的订单」可查看实时物流状态；也可凭订单号联系客服查询。"),
    ("计费方式", "按调用量与训练时长计费，新用户赠送免费额度，详见计费说明页。"),
]
for i, (t, c) in enumerate(_FAQ):
    faq.ingest(f"faq_{i}", t, c)


# ---------- MCP 工具（模拟外部系统） ----------
def _query_order(args: dict) -> str:
    oid = args.get("order_id", "未知")
    return f"订单 {oid}：已发货，预计 2 天内送达（模拟数据）。"

def _check_refund(args: dict) -> str:
    oid = args.get("order_id", "未知")
    return f"订单 {oid} 的退款已审核通过，1-3 个工作日原路退回（模拟数据）。"

def _transfer_human(args: dict) -> str:
    return "已为您转接人工客服，当前排队 2 人，预计等待 1 分钟（模拟）。"

mcp.register_fn("query_order", "查询订单物流状态", {"type": "object", "properties": {"order_id": {"type": "string"}}}, _query_order)
mcp.register_fn("check_refund", "查询退款进度", {"type": "object", "properties": {"order_id": {"type": "string"}}}, _check_refund)
mcp.register_fn("transfer_human", "转接人工客服", {"type": "object", "properties": {}}, _transfer_human)


# ---------- 意图 Skill：run 返回 (tool_name|None, 回复模板) ----------
def _intent_order(text, meta):
    m = re.search(r"[A-Za-z0-9\-]{6,}", text)
    return ("query_order", f"正在为您查询订单 {m.group(0) if m else ''} 的物流…") if False else (None, "")

import re
def intent_order(text, meta):
    oid = re.search(r"(?:订单|order)[号 ]*[:#]?\s*([A-Za-z0-9\-]{4,})", text, re.I)
    oid = oid.group(1) if oid else (re.search(r"\b[A-Za-z0-9\-]{6,}\b", text).group(0) if re.search(r"\b[A-Za-z0-9\-]{6,}\b", text) else "示例订单")
    return {"tool": "query_order", "args": {"order_id": oid}, "tmpl": f"已为您查询订单 {oid} 的物流信息。"}

def intent_refund(text, meta):
    oid = re.search(r"(?:订单|order)[号 ]*[:#]?\s*([A-Za-z0-9\-]{4,})", text, re.I)
    oid = oid.group(1) if oid else "示例订单"
    return {"tool": "check_refund", "args": {"order_id": oid}, "tmpl": f"正在查询订单 {oid} 的退款进度。"}

def intent_human(text, meta):
    return {"tool": "transfer_human", "args": {}, "tmpl": "正在为您转接人工客服。"}

def intent_product(text, meta):
    return {"tool": None, "args": {}, "tmpl": ""}  # 走 FAQ RAG

# 注意注册顺序：更具体的意图（退款/人工）先于通用意图（查订单），
# 关键词重叠时优先匹配更具体的技能，避免「我要退款订单X」被误判为查订单。
skills.register_fn("退款", "识别退款/退货意图", ["退款", "退货", "退钱", "refund"], intent_refund)
skills.register_fn("转人工", "识别转人工意图", ["人工", "客服", "真人", "human"], intent_human)
skills.register_fn("产品咨询", "识别产品咨询意图", ["怎么用", "功能", "支持", "如何", "产品", "how", "use"], intent_product)
skills.register_fn("查订单", "识别查订单/物流意图", ["物流", "发货", "快递", "运单", "查订单", "tracking"], intent_order)


def get_harness(sid: str) -> ContextHarness:
    for h in _sessions:
        if getattr(h, "sid", None) == sid:
            return h
    h = ContextHarness(budget=1500, system="你是电商智能客服。")
    h.sid = sid  # type: ignore
    _sessions.append(h)
    return h


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


@router.post("/chat")
def chat(req: ChatRequest):
    if not req.message.strip():
        return {"reply": "您好，请问有什么可以帮您？", "intent": None}
    harness = get_harness(req.session_id)
    harness.add("user", req.message)
    skill = skills.route(req.message)
    intent = skill.name if skill else None
    tool_calls = []
    reply = ""

    if skill:
        plan = skill.run(req.message, {})
        if isinstance(plan, dict) and plan.get("tool"):
            res = mcp.invoke(plan["tool"], plan.get("args", {}))
            tool_calls.append({"tool": plan["tool"], "result": res["content"][0]["text"]})
            reply = plan.get("tmpl", "") + "\n" + res["content"][0]["text"]
        else:
            # 产品咨询：走 FAQ RAG
            chunks = faq.search(req.message, top_k=2)
            if chunks:
                reply = "关于您的问题：" + "；".join(c.text for c in chunks)
                tool_calls.append({"tool": "faq_retrieval", "result": f"命中 {len(chunks)} 条知识"})
            else:
                reply = "抱歉，我暂时没有找到相关答案，已为您转接人工。" if not llm.enabled else llm.chat(
                    system="你是客服", user=req.message)
    else:
        chunks = faq.search(req.message, top_k=2)
        if chunks:
            reply = "关于您的问题：" + "；".join(c.text for c in chunks)
        else:
            reply = "您好，我暂时没理解您的问题，可以换个说法吗？或回复「人工」转接客服。"

    harness.add("assistant", reply)
    return {
        "reply": reply.strip(),
        "intent": intent,
        "tool_calls": tool_calls,
        "available_intents": [s.name for s in skills],
        "available_tools": [t["name"] for t in mcp.list_tools()],
        "context_tokens": harness.snapshot()["tokens"],
    }


@router.get("/health")
def health():
    return {"status": "ok", "project": "chatbot", "faq_chunks": len(faq.store.items), "llm_enabled": llm.enabled}
