import datetime
import random
from typing import List, Optional

from app.models import WorkOrder, WorkOrderStep
from app.services.catalog import CATALOG


_DB: dict[str, WorkOrder] = {}


def _now() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def create_work_order(items: List) -> WorkOrder:
    """规划/拆单 Agent：按选中服务项生成工单，并依各服务 approval_chain 路由审批。"""
    seq = random.randint(1000, 9999)
    wo_id = f"WO-{datetime.date.today().strftime('%Y%m%d')}-{seq}"
    titles = "、".join(i.name for i in items)

    chain: List[str] = []
    for i in items:
        for a in i.approval_chain:
            if a not in chain:
                chain.append(a)

    steps = [
        WorkOrderStep(name="需求提交", status="done", time=_now()),
        WorkOrderStep(name="AI 智能拆单", status="done", time=_now()),
    ]
    if chain:
        steps.append(WorkOrderStep(name="审批中", status="doing", owner=chain[0], time="进行中"))
        for a in chain[1:]:
            steps.append(WorkOrderStep(name=f"审批({a})", status="wait"))
    steps.append(WorkOrderStep(name="执行交付", status="wait"))

    category = "审计支持" if items[0].category.value == "audit_support" else "运维"
    wo = WorkOrder(id=wo_id, title=titles, category=category, steps=steps,
                   status="processing", created_at=_now())
    _DB[wo_id] = wo
    return wo


def get_work_order(wo_id: str) -> Optional[WorkOrder]:
    return _DB.get(wo_id)


def list_work_orders() -> List[WorkOrder]:
    return list(_DB.values())


def approve_step(wo_id: str) -> Optional[WorkOrder]:
    """审批路由 Agent 的执行结果：推进当前 doing 步骤并激活下一节点。"""
    wo = _DB.get(wo_id)
    if not wo:
        return None
    idx = next((i for i, s in enumerate(wo.steps) if s.status != "done"), None)
    if idx is None:
        wo.status = "completed"
        return wo
    wo.steps[idx].status = "done"
    wo.steps[idx].time = _now()
    for j in range(idx + 1, len(wo.steps)):
        if wo.steps[j].status != "done":
            wo.steps[j].status = "doing"
            break
    if all(s.status == "done" for s in wo.steps):
        wo.status = "completed"
    return wo


def _seed() -> None:
    """预置一个与高保真原型一致的示例工单，便于首屏展示进度卡片。"""
    sample = create_work_order([i for i in CATALOG if i.id in ("terminal", "mail")])
    old = sample.id
    sample.id = "WO-2026-0718-0392"
    sample.created_at = "2026-07-18 09:20"
    sample.steps[0].time = "07-18 09:20"
    sample.steps[1].time = "07-18 09:21"
    sample.steps[2].owner = "运维主管 王磊"
    sample.steps[2].time = "已停留 1.5h"
    _DB.pop(old, None)
    _DB[sample.id] = sample


_seed()
