import uuid
from fastapi import APIRouter, HTTPException

from app.models import ChatRequest, KnowledgeRequest
from app.llm.client import LLMClient
from app.agent.orchestrator import AgentOrchestrator
from app.services.catalog import CATALOG
from app.services.workorder import list_work_orders, get_work_order, approve_step
from app.services.monitor import get_metrics
from app.services.knowledge import ask as kb_ask

router = APIRouter(prefix="/api")

llm = LLMClient()
orchestrator = AgentOrchestrator(llm)


@router.get("/health")
def health():
    return {"status": "ok", "llm_provider": llm.provider.value, "catalog_total": len(CATALOG)}


@router.get("/catalog")
def catalog():
    return {"total": len(CATALOG), "items": CATALOG}


@router.post("/chat")
def chat(req: ChatRequest):
    """对话直达服务单入口：意图识别 -> 拆单 -> 审批路由 -> 记忆。"""
    sid = req.session_id or str(uuid.uuid4())
    resp = orchestrator.handle(req.message, sid)
    resp.session_id = sid
    return resp


@router.get("/workorders")
def workorders():
    return list_work_orders()


@router.get("/workorders/{wo_id}")
def workorder(wo_id: str):
    wo = get_work_order(wo_id)
    if not wo:
        raise HTTPException(status_code=404, detail="工单不存在")
    return wo


@router.post("/workorders/{wo_id}/approve")
def approve(wo_id: str):
    wo = approve_step(wo_id)
    if not wo:
        raise HTTPException(status_code=404, detail="工单不存在")
    return wo


@router.get("/monitor")
def monitor():
    return get_metrics()


@router.post("/knowledge/ask")
def knowledge(req: KnowledgeRequest):
    return kb_ask(req.question)
