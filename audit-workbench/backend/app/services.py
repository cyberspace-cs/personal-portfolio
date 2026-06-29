from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import ActivityLog, ApprovalStep, SyncHealth, Ticket, WatchRelation
from app.schemas import (
    ActivityOut,
    ApprovalStepOut,
    AssistantCardOut,
    AssistantMessageOut,
    OverviewOut,
    SyncHealthOut,
    TicketDetailOut,
    TicketListOut,
    TicketSummaryOut,
)


def get_overview(db: Session, user_id: str) -> OverviewOut:
    todo_count = db.scalar(select(func.count()).select_from(Ticket).where(Ticket.assignee_id == user_id)) or 0
    initiated_count = db.scalar(select(func.count()).select_from(Ticket).where(Ticket.creator_id == user_id)) or 0
    watching_count = db.scalar(select(func.count()).select_from(WatchRelation).where(WatchRelation.user_id == user_id)) or 0
    sync = db.scalar(select(SyncHealth).order_by(SyncHealth.last_synced_at.desc()))

    return OverviewOut(
        todoCount=todo_count,
        initiatedCount=initiated_count,
        watchingCount=watching_count,
        syncHealth=SyncHealthOut(
            status=sync.status if sync else "unknown",
            sourceName=sync.source_name if sync else "approval-center",
            errorCount=sync.error_count if sync else 0,
            message=sync.message if sync else "暂无同步信息",
        ),
    )


def list_tickets(db: Session, user_id: str, view: str, status: str | None, keyword: str | None) -> TicketListOut:
    stmt = (
        select(Ticket)
        .options(selectinload(Ticket.steps))
        .order_by(Ticket.updated_at.desc())
    )

    if view == "todo":
        stmt = stmt.where(Ticket.assignee_id == user_id)
    elif view == "initiated":
        stmt = stmt.where(Ticket.creator_id == user_id)
    elif view == "watching":
        stmt = stmt.where(Ticket.id.in_(select(WatchRelation.ticket_id).where(WatchRelation.user_id == user_id)))

    if status:
        stmt = stmt.where(Ticket.status == status)
    if keyword:
        stmt = stmt.where(Ticket.title.contains(keyword))

    tickets = db.scalars(stmt).all()
    return TicketListOut(items=[_ticket_summary(ticket) for ticket in tickets])


def get_ticket_detail(db: Session, ticket_id: int) -> TicketDetailOut:
    ticket = _load_ticket(db, ticket_id)
    current_step = _current_step(ticket)
    blocker_reason = _blocker_reason(ticket)
    recommended_actions = _recommended_actions(ticket)

    return TicketDetailOut(
        id=ticket.id,
        code=ticket.code,
        title=ticket.title,
        category=ticket.category,
        status=ticket.status,
        priority=ticket.priority,
        currentStep=current_step.step_name if current_step else "无",
        blockerReason=blocker_reason,
        recommendedActions=recommended_actions,
        steps=[
            ApprovalStepOut(
                id=step.id,
                stepName=step.step_name,
                approverName=step.approver_name,
                status=step.status,
                comment=step.comment,
            )
            for step in sorted(ticket.steps, key=lambda item: item.sort_order)
        ],
        activities=[
            ActivityOut(
                id=activity.id,
                action=activity.action,
                operatorName=activity.operator_name,
                content=activity.content,
                createdAt=activity.created_at,
            )
            for activity in ticket.activities
        ],
    )


def approve_ticket(db: Session, ticket_id: int, operator_name: str, comment: str) -> TicketDetailOut:
    ticket = _load_ticket(db, ticket_id)
    current_step = _current_step(ticket)
    if current_step is None or current_step.status != "pending":
        raise HTTPException(status_code=400, detail="ticket is not approvable")

    current_step.status = "approved"
    current_step.comment = comment
    current_step.acted_at = datetime.utcnow()
    ticket.status = "approved"
    ticket.updated_at = datetime.utcnow()
    db.add(
        ActivityLog(
            ticket_id=ticket.id,
            action="approved",
            operator_name=operator_name,
            content=f"{operator_name} 审批通过：{comment}",
            created_at=datetime.utcnow(),
        )
    )
    db.commit()
    return get_ticket_detail(db, ticket_id)


def reject_ticket(db: Session, ticket_id: int, operator_name: str, comment: str) -> TicketDetailOut:
    ticket = _load_ticket(db, ticket_id)
    current_step = _current_step(ticket)
    if current_step is None or current_step.status != "pending":
        raise HTTPException(status_code=400, detail="ticket is not rejectable")

    current_step.status = "rejected"
    current_step.comment = comment
    current_step.acted_at = datetime.utcnow()
    ticket.status = "rejected"
    ticket.updated_at = datetime.utcnow()
    db.add(
        ActivityLog(
            ticket_id=ticket.id,
            action="rejected",
            operator_name=operator_name,
            content=f"{operator_name} 驳回：{comment}",
            created_at=datetime.utcnow(),
        )
    )
    db.commit()
    return get_ticket_detail(db, ticket_id)


def ask_assistant(db: Session, message: str, ticket_id: int | None) -> AssistantMessageOut:
    if ticket_id is None:
        return AssistantMessageOut(
            text="请先选择一张工单，我再帮你分析当前进度、阻塞原因和下一步动作。",
            cards=[],
            suggestions=["查看待我处理", "查看我发起", "哪些工单快超时了"],
        )

    detail = get_ticket_detail(db, ticket_id)
    next_step = _next_step_name(db, ticket_id, detail.currentStep)

    if "为什么" in message or "卡" in message:
        text = f"当前工单在{detail.currentStep}节点，{detail.blockerReason}。建议先执行：{'、'.join(detail.recommendedActions)}。"
    else:
        text = f"当前工单处于{detail.currentStep}节点，状态为{detail.status}。下一步预计进入{next_step}。"

    return AssistantMessageOut(
        text=text,
        cards=[
            AssistantCardOut(
                type="ticket_progress",
                ticketCode=detail.code,
                currentStep=detail.currentStep,
                nextStep=next_step,
                status=detail.status,
                blockerReason=detail.blockerReason,
                recommendedActions=detail.recommendedActions,
            )
        ],
        suggestions=["查看审批链路", "查看退回原因", "下一步该谁处理"],
    )


def _ticket_summary(ticket: Ticket) -> TicketSummaryOut:
    current = _current_step(ticket)
    return TicketSummaryOut(
        id=ticket.id,
        code=ticket.code,
        title=ticket.title,
        status=ticket.status,
        priority=ticket.priority,
        currentStep=current.step_name if current else "无",
        updatedAt=ticket.updated_at,
    )


def _load_ticket(db: Session, ticket_id: int) -> Ticket:
    ticket = db.scalar(
        select(Ticket)
        .where(Ticket.id == ticket_id)
        .options(selectinload(Ticket.steps), selectinload(Ticket.activities))
    )
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    return ticket


def _current_step(ticket: Ticket) -> ApprovalStep | None:
    for step in ticket.steps:
        if step.id == ticket.current_step_id:
            return step
    return None


def _next_step_name(db: Session, ticket_id: int, current_step_name: str) -> str:
    ticket = _load_ticket(db, ticket_id)
    ordered = sorted(ticket.steps, key=lambda item: item.sort_order)
    for index, step in enumerate(ordered):
        if step.step_name == current_step_name:
            return ordered[index + 1].step_name if index + 1 < len(ordered) else "已完成"
    return "已完成"


def _blocker_reason(ticket: Ticket) -> str:
    if ticket.status == "approved":
        return "当前工单已完成审批，无阻塞。"
    if ticket.status == "rejected":
        return "工单已被驳回，需要根据驳回意见补充信息后重新提交。"
    current = _current_step(ticket)
    if current and current.comment:
        return current.comment
    return "等待当前审批人处理。"


def _recommended_actions(ticket: Ticket) -> list[str]:
    if ticket.status == "approved":
        return ["查看审批结果"]
    if ticket.status == "rejected":
        return ["查看退回意见", "补充材料后重新提交"]
    current = _current_step(ticket)
    if current and current.step_name == "资产管理员确认":
        return ["联系资产管理员", "查看审批链路"]
    return ["提醒当前审批人", "查看审批链路"]
