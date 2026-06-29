from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ActivityLog, ApprovalStep, SyncHealth, Ticket, WatchRelation


def seed_demo_data(db: Session) -> None:
    if db.scalar(select(Ticket.id).limit(1)):
        return

    now = datetime(2026, 6, 29, 9, 30, 0)

    tickets = [
        Ticket(
            code="WK-20260629-001",
            title="审计项目访问权限变更",
            category="权限变更",
            status="pending",
            priority="high",
            creator_id="u001",
            assignee_id="u002",
            created_at=now - timedelta(hours=5),
            updated_at=now - timedelta(minutes=25),
        ),
        Ticket(
            code="WK-20260629-002",
            title="新入职审计员办公电脑领用",
            category="资产领用",
            status="pending",
            priority="medium",
            creator_id="u001",
            assignee_id="u003",
            created_at=now - timedelta(days=1),
            updated_at=now - timedelta(minutes=12),
        ),
        Ticket(
            code="WK-20260629-003",
            title="日志查询权限申请",
            category="日志查询",
            status="approved",
            priority="low",
            creator_id="u004",
            assignee_id=None,
            created_at=now - timedelta(days=2),
            updated_at=now - timedelta(days=1, minutes=15),
        ),
    ]
    db.add_all(tickets)
    db.flush()

    steps = [
        ApprovalStep(ticket_id=tickets[0].id, step_name="组长审批", approver_name="张组长", status="pending", comment=None, acted_at=None, sort_order=1),
        ApprovalStep(ticket_id=tickets[0].id, step_name="部门负责人审批", approver_name="李主任", status="waiting", comment=None, acted_at=None, sort_order=2),
        ApprovalStep(ticket_id=tickets[1].id, step_name="资产管理员确认", approver_name="王管理员", status="pending", comment="等待确认库存", acted_at=None, sort_order=1),
        ApprovalStep(ticket_id=tickets[1].id, step_name="仓库出库", approver_name="库管员", status="waiting", comment=None, acted_at=None, sort_order=2),
        ApprovalStep(ticket_id=tickets[2].id, step_name="系统管理员审批", approver_name="周管理员", status="approved", comment="已开通 7 天权限", acted_at=now - timedelta(days=1, hours=1), sort_order=1),
    ]
    db.add_all(steps)
    db.flush()

    tickets[0].current_step_id = steps[0].id
    tickets[1].current_step_id = steps[2].id
    tickets[2].current_step_id = steps[4].id

    db.add_all(
        [
            WatchRelation(ticket_id=tickets[2].id, user_id="u001"),
            ActivityLog(
                ticket_id=tickets[0].id,
                action="created",
                operator_name="系统",
                content="工单已创建，等待组长审批",
                created_at=now - timedelta(hours=5),
            ),
            ActivityLog(
                ticket_id=tickets[1].id,
                action="submitted",
                operator_name="系统",
                content="工单已提交，等待资产管理员确认",
                created_at=now - timedelta(days=1),
            ),
            ActivityLog(
                ticket_id=tickets[2].id,
                action="approved",
                operator_name="周管理员",
                content="日志查询权限已开通 7 天",
                created_at=now - timedelta(days=1, hours=1),
            ),
            SyncHealth(
                source_name="approval-center",
                status="healthy",
                last_synced_at=now - timedelta(minutes=2),
                error_count=0,
                message="最近一次同步成功",
            ),
        ]
    )
    db.commit()
