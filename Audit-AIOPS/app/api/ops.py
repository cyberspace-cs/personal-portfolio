"""
审计运维控制台 · API 路由（蓝鲸经验落地）

端点（全部挂载于 /api/ops，端口 8001）：
- GET  /summary      工作台总览：ITSM + 运维 + 变更 KPI、多用户智能体、痛点洞察
- GET  /tickets      审计技术支持工单（可按 service/status/priority/auto 过滤）
- GET  /alerts       日常运维告警（可按 service/severity/status/auto 过滤）
- GET  /changes      变更记录（双人审批留痕）
- GET  /agents       多用户运维智能体画像
- GET  /pain-points  痛点洞察（由真实数据推导）
- POST /seed         重新生成真实数据（演示用）

设计哲学与既有平台一致：可插拔、纯 CPU、零外部依赖；数据驱动、可回溯、不编造。
"""

from typing import Optional

from fastapi import APIRouter

from app.services.ops_data import get_ops_store
from app.config import settings
from app.llm.client import LLMClient

ops_router = APIRouter()
_store = get_ops_store()
_llm = LLMClient()


@ops_router.get("/api/ops/summary")
def summary():
    """工作台总览：全部 KPI + 多用户智能体 + 痛点洞察。"""
    return _store.summary()


@ops_router.get("/api/ops/tickets")
def tickets(service: Optional[str] = None, status: Optional[str] = None,
            priority: Optional[str] = None, auto: Optional[bool] = None):
    """审计技术支持工单列表（可过滤）。"""
    return {"total": _store.summary()["ticket_metrics"]["total"],
            "returned": len(_store.tickets(service, status, priority, auto)),
            "items": _store.tickets(service, status, priority, auto)}


@ops_router.get("/api/ops/alerts")
def alerts(service: Optional[str] = None, severity: Optional[str] = None,
           status: Optional[str] = None, auto: Optional[bool] = None):
    """日常运维告警列表（可过滤）。"""
    return {"total": _store.summary()["ops_metrics"]["alerts_total"],
            "returned": len(_store.alerts(service, severity, status, auto)),
            "items": _store.alerts(service, severity, status, auto)}


@ops_router.get("/api/ops/changes")
def changes():
    """变更记录（双人审批留痕）。"""
    return {"total": _store.summary()["change_metrics"]["total"],
            "items": _store.changes()}


@ops_router.get("/api/ops/agents")
def agents():
    """多用户运维智能体画像。"""
    return {"total": len(_store.agents()), "items": _store.agents()}


@ops_router.get("/api/ops/pain-points")
def pain_points():
    """痛点洞察。"""
    return {"items": _store.pain_points()}


@ops_router.post("/api/ops/seed")
def seed():
    """重新生成真实数据（演示用）。"""
    m = _store.reseed()
    return {"status": "ok", "metrics": m}


@ops_router.post("/api/ops/analyze")
def analyze():
    """用（可插拔）LLM 基座对真实运维 KPI 做「对话式智能分析」。

    - 始终基于 /api/ops/summary 的真实数据生成接地分析（不编造）。
    - 若配置了真实 LLM（HUNYUAN/QWEN + 密钥），额外调用基座做自然语言解读；
      当前为 Mock 时优雅降级为结构化模板分析，演示逻辑照样跑通。
    呼应黄超「成本控制·自负盈亏」：分析本身也走缓存与低成本基座。
    """
    s = _store.summary()
    t = s["ticket_metrics"]
    o = s["ops_metrics"]
    c = s["change_metrics"]
    pains = s["pain_points"]

    grounded = (
        f"【审计运维智能体 · 数据驱动分析】\n"
        f"· 工单：总量 {t['total']}，已闭环 {t['resolved_rate']}%，自动化处置 {t['automation_rate']}%，"
        f"SLA 达标 {t['sla_compliance']}%，MTTR {t['mttr_h']}h，CSAT {t['csat']}，重开率 {t['reopen_rate']}%。\n"
        f"· 日常运维：主机在线率 {o['online_rate']}%（{o['online']}/{o['hosts_total']}），"
        f"告警 {o['alerts_total']} 条、收敛降噪 {o['convergence_rate']}%、自愈 {o['self_heal_rate']}%、平均恢复 {o['avg_recovery_min']}min。\n"
        f"· 变更：{c['total']} 笔，双人审批率 {c['dual_approval_rate']}%（审计留痕）。\n"
        f"· 多用户智能体：{len(s['agents'])} 个角色协同，承接工单/告警并自动处置。\n"
        f"· 头号痛点：{pains[0]['title']}（{pains[0]['value']}）—— {pains[0]['reco']}"
    )

    llm_analysis = None
    if settings.llm_provider != "mock":
        prompt = (
            "你是审计运维平台的资深 SRE 分析师。基于以下真实指标，用 3-4 句中文给出洞察与下一步建议，"
            "结论要可操作、不空泛：\n" + grounded
        )
        try:
            out = _llm._chat(
                "你是审计运维平台 KPI 分析师，基于真实指标做简洁、可操作的洞察。",
                prompt,
            )
            if out and out.strip():
                llm_analysis = out.strip()
        except Exception:  # noqa: BLE001
            llm_analysis = None

    return {
        "provider": settings.llm_provider,
        "grounded_analysis": grounded,
        "llm_analysis": llm_analysis,
        "metrics_summary": {
            "tickets_total": t["total"],
            "automation_rate": t["automation_rate"],
            "sla_compliance": t["sla_compliance"],
            "mttr_h": t["mttr_h"],
            "csat": t["csat"],
            "online_rate": o["online_rate"],
            "self_heal_rate": o["self_heal_rate"],
            "dual_approval_rate": c["dual_approval_rate"],
        },
    }
