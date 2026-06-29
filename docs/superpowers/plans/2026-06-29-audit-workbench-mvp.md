# Audit Workbench MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个独立的 `audit-workbench` 仓库，交付 `FastAPI + SQLite` 后端、`React + Vite + Tailwind` 前端，以及“概览卡片直达列表 + 审批工单详情 + 对话式智能体进度卡片 + SSE 近实时更新”的可运行 MVP。

**Architecture:** 采用前后端分离架构。后端使用 FastAPI 暴露概览、工单、审批动作、智能体与 SSE 事件接口，SQLite 做持久化；前端使用 React + Vite + Tailwind 构建政务/国企蓝风格工作台，概览卡片作为主入口，右侧列表与智能体面板共享统一数据模型与事件流。智能体第一版不依赖外部大模型，而是使用可解释的规则层 + 数据查询层返回“文本 + 进度卡片”。

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.x, Pydantic v2, SQLite, pytest, React 18, TypeScript, Vite, Tailwind CSS, Vitest, Testing Library

---

## File Structure

以下文件结构在任务开始前就锁定，后续所有任务都按此拆分：

- `audit-workbench/README.md`
  - 仓库级启动说明、目录说明、联调说明
- `audit-workbench/backend/requirements.txt`
  - 后端依赖
- `audit-workbench/backend/app/main.py`
  - FastAPI 应用入口，挂载所有路由
- `audit-workbench/backend/app/core/config.py`
  - 配置项（数据库路径、CORS 白名单）
- `audit-workbench/backend/app/db/base.py`
  - SQLAlchemy `Base`
- `audit-workbench/backend/app/db/session.py`
  - engine / session 工厂
- `audit-workbench/backend/app/db/seed.py`
  - 初始化演示数据
- `audit-workbench/backend/app/models/*.py`
  - `Ticket`、`ApprovalStep`、`ActivityLog`、`WatchRelation`、`SyncHealth`
- `audit-workbench/backend/app/schemas/*.py`
  - 概览、工单、审批动作、智能体请求/响应、SSE 事件响应模型
- `audit-workbench/backend/app/services/*.py`
  - 概览聚合、工单查询与动作、智能体响应、事件总线
- `audit-workbench/backend/app/api/routes/*.py`
  - `overview.py`、`tickets.py`、`assistant.py`、`events.py`
- `audit-workbench/backend/tests/*.py`
  - API 与服务层测试
- `audit-workbench/frontend/package.json`
  - 前端依赖与脚本
- `audit-workbench/frontend/tailwind.config.cjs`
  - Tailwind 扫描配置
- `audit-workbench/frontend/postcss.config.cjs`
  - PostCSS 配置
- `audit-workbench/frontend/vite.config.ts`
  - Vite + Vitest 配置
- `audit-workbench/frontend/src/main.tsx`
  - 前端入口
- `audit-workbench/frontend/src/App.tsx`
  - 应用路由壳（MVP 单页）
- `audit-workbench/frontend/src/index.css`
  - Tailwind 指令 + 设计令牌 + 全局样式
- `audit-workbench/frontend/src/types/api.ts`
  - 前后端共享的响应类型
- `audit-workbench/frontend/src/services/api.ts`
  - HTTP 请求封装
- `audit-workbench/frontend/src/services/events.ts`
  - SSE 封装
- `audit-workbench/frontend/src/features/workbench/WorkbenchPage.tsx`
  - 工作台页容器
- `audit-workbench/frontend/src/features/workbench/OverviewCards.tsx`
  - 概览卡片区
- `audit-workbench/frontend/src/features/workbench/TicketTable.tsx`
  - 工单列表
- `audit-workbench/frontend/src/features/workbench/TicketDrawer.tsx`
  - 工单详情抽屉
- `audit-workbench/frontend/src/features/assistant/AssistantPanel.tsx`
  - 智能体面板
- `audit-workbench/frontend/src/test/setup.ts`
  - Vitest 初始化
- `audit-workbench/frontend/src/features/**/__tests__/*.test.tsx`
  - 工作台、抽屉、智能体交互测试

## Task 1: 初始化独立仓库与后端概览接口

**Files:**
- Create: `audit-workbench/README.md`
- Create: `audit-workbench/backend/requirements.txt`
- Create: `audit-workbench/backend/app/core/config.py`
- Create: `audit-workbench/backend/app/db/base.py`
- Create: `audit-workbench/backend/app/db/session.py`
- Create: `audit-workbench/backend/app/db/seed.py`
- Create: `audit-workbench/backend/app/models/ticket.py`
- Create: `audit-workbench/backend/app/models/approval_step.py`
- Create: `audit-workbench/backend/app/models/activity_log.py`
- Create: `audit-workbench/backend/app/models/watch_relation.py`
- Create: `audit-workbench/backend/app/models/sync_health.py`
- Create: `audit-workbench/backend/app/models/__init__.py`
- Create: `audit-workbench/backend/app/schemas/overview.py`
- Create: `audit-workbench/backend/app/services/overview_service.py`
- Create: `audit-workbench/backend/app/api/routes/overview.py`
- Create: `audit-workbench/backend/app/main.py`
- Test: `audit-workbench/backend/tests/test_overview_api.py`

- [ ] **Step 1: 写出失败测试**

```python
# audit-workbench/backend/tests/test_overview_api.py
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_overview_returns_expected_cards() -> None:
    response = client.get("/api/overview", headers={"x-user-id": "u001"})

    assert response.status_code == 200
    assert response.json() == {
        "todoCount": 2,
        "initiatedCount": 2,
        "watchingCount": 1,
        "syncHealth": {
            "status": "healthy",
            "sourceName": "approval-center",
            "errorCount": 0,
            "message": "最近一次同步成功"
        }
    }
```

- [ ] **Step 2: 运行测试，确认失败**

Run:

```bash
cd /workspace
mkdir -p audit-workbench/backend/tests
python3 -m venv audit-workbench/.venv
. audit-workbench/.venv/bin/activate
pip install pytest >/dev/null 2>&1 || true
pytest audit-workbench/backend/tests/test_overview_api.py -q
```

Expected:

```text
E   ModuleNotFoundError: No module named 'app'
```

- [ ] **Step 3: 写最小实现**

```python
# audit-workbench/backend/requirements.txt
fastapi==0.115.0
uvicorn==0.30.6
sqlalchemy==2.0.35
pydantic==2.9.2
pydantic-settings==2.5.2
pytest==8.3.3
httpx==0.27.2
```

```python
# audit-workbench/backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Audit Workbench API"
    database_url: str = "sqlite:///./audit_workbench.db"
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_prefix="AUDIT_", case_sensitive=False)


settings = Settings()
```

```python
# audit-workbench/backend/app/db/base.py
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

```python
# audit-workbench/backend/app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


engine = create_engine(settings.database_url, future=True, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

```python
# audit-workbench/backend/app/models/ticket.py
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    priority: Mapped[str] = mapped_column(String(32))
    creator_id: Mapped[str] = mapped_column(String(32), index=True)
    assignee_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    current_step_id: Mapped[int | None] = mapped_column(ForeignKey("approval_steps.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime())
    created_at: Mapped[datetime] = mapped_column(DateTime())

    approval_steps: Mapped[list["ApprovalStep"]] = relationship(
        "ApprovalStep",
        back_populates="ticket",
        foreign_keys="ApprovalStep.ticket_id",
        cascade="all, delete-orphan",
    )
```

```python
# audit-workbench/backend/app/models/approval_step.py
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ApprovalStep(Base):
    __tablename__ = "approval_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    step_name: Mapped[str] = mapped_column(String(64))
    approver_name: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    comment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    acted_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    sort_order: Mapped[int]

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="approval_steps", foreign_keys=[ticket_id])
```

```python
# audit-workbench/backend/app/models/activity_log.py
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    action: Mapped[str] = mapped_column(String(64))
    operator_name: Mapped[str] = mapped_column(String(64))
    content: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime())
```

```python
# audit-workbench/backend/app/models/watch_relation.py
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WatchRelation(Base):
    __tablename__ = "watch_relations"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
```

```python
# audit-workbench/backend/app/models/sync_health.py
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SyncHealth(Base):
    __tablename__ = "sync_health"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    last_synced_at: Mapped[datetime] = mapped_column(DateTime())
    error_count: Mapped[int]
    message: Mapped[str] = mapped_column(String(255))
```

```python
# audit-workbench/backend/app/models/__init__.py
from app.models.activity_log import ActivityLog
from app.models.approval_step import ApprovalStep
from app.models.sync_health import SyncHealth
from app.models.ticket import Ticket
from app.models.watch_relation import WatchRelation

__all__ = [
    "ActivityLog",
    "ApprovalStep",
    "SyncHealth",
    "Ticket",
    "WatchRelation",
]
```

```python
# audit-workbench/backend/app/db/seed.py
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.approval_step import ApprovalStep
from app.models.sync_health import SyncHealth
from app.models.ticket import Ticket
from app.models.watch_relation import WatchRelation


def seed_demo_data(db: Session) -> None:
    existing = db.scalar(select(Ticket).limit(1))
    if existing:
        return

    now = datetime(2026, 6, 29, 9, 0, 0)

    ticket_1 = Ticket(
        code="WK-20260629-001",
        title="审计项目访问权限变更",
        category="权限变更",
        status="pending",
        priority="high",
        creator_id="u001",
        assignee_id="u002",
        created_at=now - timedelta(hours=5),
        updated_at=now - timedelta(minutes=30),
    )
    ticket_2 = Ticket(
        code="WK-20260629-002",
        title="新入职审计员办公电脑领用",
        category="资产领用",
        status="pending",
        priority="medium",
        creator_id="u001",
        assignee_id="u003",
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(minutes=10),
    )
    ticket_3 = Ticket(
        code="WK-20260629-003",
        title="日志查询权限申请",
        category="日志查询",
        status="approved",
        priority="low",
        creator_id="u004",
        assignee_id=None,
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=1),
    )

    db.add_all([ticket_1, ticket_2, ticket_3])
    db.flush()

    steps = [
        ApprovalStep(ticket_id=ticket_1.id, step_name="组长审批", approver_name="张组长", status="pending", comment=None, acted_at=None, sort_order=1),
        ApprovalStep(ticket_id=ticket_1.id, step_name="部门负责人审批", approver_name="李主任", status="waiting", comment=None, acted_at=None, sort_order=2),
        ApprovalStep(ticket_id=ticket_2.id, step_name="资产管理员确认", approver_name="王管理员", status="pending", comment="等待确认库存", acted_at=None, sort_order=1),
        ApprovalStep(ticket_id=ticket_2.id, step_name="仓库出库", approver_name="库管员", status="waiting", comment=None, acted_at=None, sort_order=2),
        ApprovalStep(ticket_id=ticket_3.id, step_name="系统管理员审批", approver_name="周管理员", status="approved", comment="已开通 7 天权限", acted_at=now - timedelta(days=1, hours=2), sort_order=1),
    ]
    db.add_all(steps)
    db.flush()

    ticket_1.current_step_id = steps[0].id
    ticket_2.current_step_id = steps[2].id
    ticket_3.current_step_id = steps[4].id

    db.add(WatchRelation(ticket_id=ticket_3.id, user_id="u001"))
    db.add(
        SyncHealth(
            source_name="approval-center",
            status="healthy",
            last_synced_at=now - timedelta(minutes=2),
            error_count=0,
            message="最近一次同步成功",
        )
    )
    db.commit()
```

```python
# audit-workbench/backend/app/schemas/overview.py
from pydantic import BaseModel


class SyncHealthOut(BaseModel):
    status: str
    sourceName: str
    errorCount: int
    message: str


class OverviewOut(BaseModel):
    todoCount: int
    initiatedCount: int
    watchingCount: int
    syncHealth: SyncHealthOut
```

```python
# audit-workbench/backend/app/services/overview_service.py
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.sync_health import SyncHealth
from app.models.ticket import Ticket
from app.models.watch_relation import WatchRelation
from app.schemas.overview import OverviewOut, SyncHealthOut


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
```

```python
# audit-workbench/backend/app/api/routes/overview.py
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.overview import OverviewOut
from app.services.overview_service import get_overview

router = APIRouter(prefix="/api", tags=["overview"])


@router.get("/overview", response_model=OverviewOut)
def overview(x_user_id: str = Header(default="u001"), db: Session = Depends(get_db)) -> OverviewOut:
    return get_overview(db, x_user_id)
```

```python
# audit-workbench/backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.overview import router as overview_router
from app.core.config import settings
from app.db.base import Base
from app.db.seed import seed_demo_data
from app.db.session import SessionLocal, engine
from app.models import activity_log, approval_step, sync_health, ticket, watch_relation  # noqa: F401


app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(overview_router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_data(db)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

```python
# audit-workbench/README.md
# audit-workbench

审批工单工作台与智能体 MVP。

## 启动

### 后端

```bash
cd backend
python3 -m venv ../.venv
. ../.venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 测试

```bash
cd backend
. ../.venv/bin/activate
pytest
```
```

- [ ] **Step 4: 运行测试，确认通过**

Run:

```bash
cd /workspace/audit-workbench/backend
. ../.venv/bin/activate
pip install -r requirements.txt
pytest tests/test_overview_api.py -q
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 提交**

```bash
cd /workspace
git add audit-workbench docs/superpowers/plans/2026-06-29-audit-workbench-mvp.md
git commit -m "feat: bootstrap audit workbench backend overview api"
```

### Task 2: 实现工单列表与详情接口

**Files:**
- Modify: `audit-workbench/backend/app/schemas/overview.py`
- Create: `audit-workbench/backend/app/schemas/ticket.py`
- Create: `audit-workbench/backend/app/services/ticket_service.py`
- Create: `audit-workbench/backend/app/api/routes/tickets.py`
- Modify: `audit-workbench/backend/app/main.py`
- Test: `audit-workbench/backend/tests/test_ticket_api.py`

- [ ] **Step 1: 写出失败测试**

```python
# audit-workbench/backend/tests/test_ticket_api.py
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_list_tickets_uses_card_view_filter() -> None:
    response = client.get("/api/tickets?view=initiated", headers={"x-user-id": "u001"})

    assert response.status_code == 200
    payload = response.json()
    assert [item["code"] for item in payload["items"]] == [
        "WK-20260629-001",
        "WK-20260629-002",
    ]


def test_get_ticket_detail_contains_steps_and_recommended_actions() -> None:
    response = client.get("/api/tickets/1", headers={"x-user-id": "u001"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "WK-20260629-001"
    assert payload["currentStep"] == "组长审批"
    assert payload["blockerReason"] == "等待当前审批人处理"
    assert payload["recommendedActions"] == ["提醒当前审批人", "查看审批链路"]
    assert [step["status"] for step in payload["steps"]] == ["pending", "waiting"]
```

- [ ] **Step 2: 运行测试，确认失败**

Run:

```bash
cd /workspace/audit-workbench/backend
. ../.venv/bin/activate
pytest tests/test_ticket_api.py -q
```

Expected:

```text
404 Client Error 或 AssertionError，因为 /api/tickets 尚未实现
```

- [ ] **Step 3: 写最小实现**

```python
# audit-workbench/backend/app/schemas/ticket.py
from datetime import datetime

from pydantic import BaseModel


class TicketSummaryOut(BaseModel):
    id: int
    code: str
    title: str
    status: str
    priority: str
    currentStep: str
    updatedAt: datetime


class TicketListOut(BaseModel):
    items: list[TicketSummaryOut]


class ApprovalStepOut(BaseModel):
    id: int
    stepName: str
    approverName: str
    status: str
    comment: str | None


class TicketDetailOut(BaseModel):
    id: int
    code: str
    title: str
    category: str
    status: str
    priority: str
    currentStep: str
    blockerReason: str
    recommendedActions: list[str]
    steps: list[ApprovalStepOut]
```

```python
# audit-workbench/backend/app/services/ticket_service.py
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.approval_step import ApprovalStep
from app.models.ticket import Ticket
from app.models.watch_relation import WatchRelation
from app.schemas.ticket import ApprovalStepOut, TicketDetailOut, TicketListOut, TicketSummaryOut


def list_tickets(db: Session, user_id: str, view: str, status: str | None, keyword: str | None) -> TicketListOut:
    stmt = select(Ticket).options(selectinload(Ticket.approval_steps)).order_by(Ticket.updated_at.desc())

    if view == "todo":
        stmt = stmt.where(Ticket.assignee_id == user_id)
    elif view == "initiated":
        stmt = stmt.where(Ticket.creator_id == user_id)
    elif view == "watching":
        watched_ids = select(WatchRelation.ticket_id).where(WatchRelation.user_id == user_id)
        stmt = stmt.where(Ticket.id.in_(watched_ids))

    if status:
        stmt = stmt.where(Ticket.status == status)
    if keyword:
        stmt = stmt.where(Ticket.title.contains(keyword))

    items = db.scalars(stmt).all()
    return TicketListOut(
        items=[
            TicketSummaryOut(
                id=item.id,
                code=item.code,
                title=item.title,
                status=item.status,
                priority=item.priority,
                currentStep=_get_current_step_name(item),
                updatedAt=item.updated_at,
            )
            for item in items
        ]
    )


def get_ticket_detail(db: Session, ticket_id: int) -> TicketDetailOut:
    stmt = select(Ticket).where(Ticket.id == ticket_id).options(selectinload(Ticket.approval_steps))
    ticket = db.scalar(stmt)
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")

    current_step = _get_current_step(ticket)
    blocker_reason = "等待当前审批人处理" if ticket.status == "pending" else "无阻塞"
    recommended_actions = ["提醒当前审批人", "查看审批链路"] if ticket.status == "pending" else ["查看审批结果"]

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
            for step in sorted(ticket.approval_steps, key=lambda item: item.sort_order)
        ],
    )


def _get_current_step(ticket: Ticket) -> ApprovalStep | None:
    for step in ticket.approval_steps:
        if step.id == ticket.current_step_id:
            return step
    return None


def _get_current_step_name(ticket: Ticket) -> str:
    step = _get_current_step(ticket)
    return step.step_name if step else "无"
```

```python
# audit-workbench/backend/app/api/routes/tickets.py
from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ticket import TicketDetailOut, TicketListOut
from app.services.ticket_service import get_ticket_detail, list_tickets

router = APIRouter(prefix="/api", tags=["tickets"])


@router.get("/tickets", response_model=TicketListOut)
def tickets(
    view: str = Query(default="todo"),
    status: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    x_user_id: str = Header(default="u001"),
    db: Session = Depends(get_db),
) -> TicketListOut:
    return list_tickets(db, x_user_id, view, status, keyword)


@router.get("/tickets/{ticket_id}", response_model=TicketDetailOut)
def ticket_detail(ticket_id: int, db: Session = Depends(get_db)) -> TicketDetailOut:
    return get_ticket_detail(db, ticket_id)
```

```python
# audit-workbench/backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.overview import router as overview_router
from app.api.routes.tickets import router as tickets_router
from app.core.config import settings
from app.db.base import Base
from app.db.seed import seed_demo_data
from app.db.session import SessionLocal, engine
from app.models import activity_log, approval_step, sync_health, ticket, watch_relation  # noqa: F401


app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(overview_router)
app.include_router(tickets_router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_data(db)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: 运行测试，确认通过**

Run:

```bash
cd /workspace/audit-workbench/backend
. ../.venv/bin/activate
pytest tests/test_ticket_api.py -q
```

Expected:

```text
2 passed
```

- [ ] **Step 5: 提交**

```bash
cd /workspace
git add audit-workbench/backend
git commit -m "feat: add ticket list and detail endpoints"
```

### Task 3: 实现审批动作、SSE 事件流与智能体接口

**Files:**
- Create: `audit-workbench/backend/app/schemas/assistant.py`
- Create: `audit-workbench/backend/app/services/event_service.py`
- Create: `audit-workbench/backend/app/services/assistant_service.py`
- Modify: `audit-workbench/backend/app/services/ticket_service.py`
- Create: `audit-workbench/backend/app/api/routes/assistant.py`
- Create: `audit-workbench/backend/app/api/routes/events.py`
- Modify: `audit-workbench/backend/app/api/routes/tickets.py`
- Modify: `audit-workbench/backend/app/main.py`
- Test: `audit-workbench/backend/tests/test_actions_and_assistant.py`

- [ ] **Step 1: 写出失败测试**

```python
# audit-workbench/backend/tests/test_actions_and_assistant.py
import asyncio

from fastapi.testclient import TestClient

from app.main import app
from app.services.event_service import event_bus


client = TestClient(app)


def test_approve_ticket_updates_status_and_returns_latest_detail() -> None:
    response = client.post("/api/tickets/1/approve", json={"comment": "同意"}, headers={"x-user-id": "u002"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "approved"
    assert payload["currentStep"] == "组长审批"


def test_assistant_returns_progress_card() -> None:
    response = client.post(
        "/api/assistant/messages",
        json={"message": "这张单现在到哪一步了？", "ticketId": 2},
        headers={"x-user-id": "u001"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "当前工单处于" in payload["text"]
    assert payload["cards"][0]["currentStep"] == "资产管理员确认"
    assert payload["cards"][0]["recommendedActions"] == ["联系资产管理员", "查看审批链路"]


def test_event_bus_yields_published_message() -> None:
    async def _run() -> dict:
        stream = event_bus.subscribe()
        task = asyncio.create_task(anext(stream))
        await asyncio.sleep(0)
        await event_bus.publish({"type": "ticket.updated", "ticketId": 1})
        result = await task
        await stream.aclose()
        return result

    assert asyncio.run(_run()) == {"type": "ticket.updated", "ticketId": 1}
```

- [ ] **Step 2: 运行测试，确认失败**

Run:

```bash
cd /workspace/audit-workbench/backend
. ../.venv/bin/activate
pytest tests/test_actions_and_assistant.py -q
```

Expected:

```text
ImportError 或 404，因为审批动作、智能体路由和事件总线尚未实现
```

- [ ] **Step 3: 写最小实现**

```python
# audit-workbench/backend/app/schemas/assistant.py
from pydantic import BaseModel


class AssistantMessageIn(BaseModel):
    message: str
    ticketId: int | None = None


class AssistantCardOut(BaseModel):
    type: str
    ticketCode: str
    currentStep: str
    nextStep: str
    status: str
    blockerReason: str
    recommendedActions: list[str]


class AssistantMessageOut(BaseModel):
    text: str
    cards: list[AssistantCardOut]
    suggestions: list[str]


class DecisionPayload(BaseModel):
    comment: str
```

```python
# audit-workbench/backend/app/services/event_service.py
import asyncio
from collections.abc import AsyncIterator


class EventBus:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue] = set()

    async def publish(self, event: dict) -> None:
        for queue in list(self._subscribers):
            await queue.put(event)

    async def subscribe(self) -> AsyncIterator[dict]:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers.discard(queue)


event_bus = EventBus()
```

```python
# audit-workbench/backend/app/services/assistant_service.py
from sqlalchemy.orm import Session

from app.schemas.assistant import AssistantCardOut, AssistantMessageOut
from app.services.ticket_service import get_ticket_detail


def reply_to_message(db: Session, message: str, ticket_id: int | None) -> AssistantMessageOut:
    if ticket_id is None:
        return AssistantMessageOut(
            text="请先选择一张工单，我才能给出当前进度和下一步操作建议。",
            cards=[],
            suggestions=["查看待我处理", "查看我发起", "如何筛选阻塞工单"],
        )

    detail = get_ticket_detail(db, ticket_id)
    if detail.currentStep == "资产管理员确认":
        recommended_actions = ["联系资产管理员", "查看审批链路"]
    elif detail.status == "approved":
        recommended_actions = ["查看审批结果"]
    else:
        recommended_actions = detail.recommendedActions

    next_step = "仓库出库" if detail.currentStep == "资产管理员确认" else "已完成"
    blocker_reason = detail.blockerReason

    return AssistantMessageOut(
        text=f"当前工单处于{detail.currentStep}节点，状态为{detail.status}。{blocker_reason}。",
        cards=[
            AssistantCardOut(
                type="ticket_progress",
                ticketCode=detail.code,
                currentStep=detail.currentStep,
                nextStep=next_step,
                status=detail.status,
                blockerReason=blocker_reason,
                recommendedActions=recommended_actions,
            )
        ],
        suggestions=["查看审批链路", "查看退回原因", "下一步该谁处理"],
    )
```

```python
# audit-workbench/backend/app/services/ticket_service.py
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.activity_log import ActivityLog
from app.models.approval_step import ApprovalStep
from app.models.ticket import Ticket
from app.models.watch_relation import WatchRelation
from app.schemas.ticket import ApprovalStepOut, TicketDetailOut, TicketListOut, TicketSummaryOut


def list_tickets(db: Session, user_id: str, view: str, status: str | None, keyword: str | None) -> TicketListOut:
    stmt = select(Ticket).options(selectinload(Ticket.approval_steps)).order_by(Ticket.updated_at.desc())

    if view == "todo":
        stmt = stmt.where(Ticket.assignee_id == user_id)
    elif view == "initiated":
        stmt = stmt.where(Ticket.creator_id == user_id)
    elif view == "watching":
        watched_ids = select(WatchRelation.ticket_id).where(WatchRelation.user_id == user_id)
        stmt = stmt.where(Ticket.id.in_(watched_ids))

    if status:
        stmt = stmt.where(Ticket.status == status)
    if keyword:
        stmt = stmt.where(Ticket.title.contains(keyword))

    items = db.scalars(stmt).all()
    return TicketListOut(
        items=[
            TicketSummaryOut(
                id=item.id,
                code=item.code,
                title=item.title,
                status=item.status,
                priority=item.priority,
                currentStep=_get_current_step_name(item),
                updatedAt=item.updated_at,
            )
            for item in items
        ]
    )


def get_ticket_detail(db: Session, ticket_id: int) -> TicketDetailOut:
    ticket = _get_ticket(db, ticket_id)
    current_step = _get_current_step(ticket)
    blocker_reason = "等待当前审批人处理" if ticket.status == "pending" else "无阻塞"
    recommended_actions = ["提醒当前审批人", "查看审批链路"] if ticket.status == "pending" else ["查看审批结果"]

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
            for step in sorted(ticket.approval_steps, key=lambda item: item.sort_order)
        ],
    )


def approve_ticket(db: Session, ticket_id: int, operator_name: str, comment: str) -> TicketDetailOut:
    ticket = _get_ticket(db, ticket_id)
    current_step = _get_current_step(ticket)
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
            content=f"{operator_name} 已审批通过：{comment}",
            created_at=datetime.utcnow(),
        )
    )
    db.commit()
    db.refresh(ticket)
    return get_ticket_detail(db, ticket_id)


def reject_ticket(db: Session, ticket_id: int, operator_name: str, comment: str) -> TicketDetailOut:
    ticket = _get_ticket(db, ticket_id)
    current_step = _get_current_step(ticket)
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
            content=f"{operator_name} 已驳回：{comment}",
            created_at=datetime.utcnow(),
        )
    )
    db.commit()
    db.refresh(ticket)
    return get_ticket_detail(db, ticket_id)


def _get_ticket(db: Session, ticket_id: int) -> Ticket:
    stmt = select(Ticket).where(Ticket.id == ticket_id).options(selectinload(Ticket.approval_steps))
    ticket = db.scalar(stmt)
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")
    return ticket


def _get_current_step(ticket: Ticket) -> ApprovalStep | None:
    for step in ticket.approval_steps:
        if step.id == ticket.current_step_id:
            return step
    return None


def _get_current_step_name(ticket: Ticket) -> str:
    step = _get_current_step(ticket)
    return step.step_name if step else "无"
```

```python
# audit-workbench/backend/app/api/routes/assistant.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.assistant import AssistantMessageIn, AssistantMessageOut
from app.services.assistant_service import reply_to_message

router = APIRouter(prefix="/api", tags=["assistant"])


@router.post("/assistant/messages", response_model=AssistantMessageOut)
def assistant_message(payload: AssistantMessageIn, db: Session = Depends(get_db)) -> AssistantMessageOut:
    return reply_to_message(db, payload.message, payload.ticketId)
```

```python
# audit-workbench/backend/app/api/routes/events.py
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.event_service import event_bus

router = APIRouter(prefix="/api", tags=["events"])


@router.get("/events")
async def events() -> StreamingResponse:
    async def stream():
        async for event in event_bus.subscribe():
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
```

```python
# audit-workbench/backend/app/api/routes/tickets.py
from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.assistant import DecisionPayload
from app.schemas.ticket import TicketDetailOut, TicketListOut
from app.services.event_service import event_bus
from app.services.ticket_service import approve_ticket, get_ticket_detail, list_tickets, reject_ticket

router = APIRouter(prefix="/api", tags=["tickets"])


@router.get("/tickets", response_model=TicketListOut)
def tickets(
    view: str = Query(default="todo"),
    status: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    x_user_id: str = Header(default="u001"),
    db: Session = Depends(get_db),
) -> TicketListOut:
    return list_tickets(db, x_user_id, view, status, keyword)


@router.get("/tickets/{ticket_id}", response_model=TicketDetailOut)
def ticket_detail(ticket_id: int, db: Session = Depends(get_db)) -> TicketDetailOut:
    return get_ticket_detail(db, ticket_id)


@router.post("/tickets/{ticket_id}/approve", response_model=TicketDetailOut)
async def approve(
    ticket_id: int,
    payload: DecisionPayload,
    x_user_id: str = Header(default="u001"),
    db: Session = Depends(get_db),
) -> TicketDetailOut:
    detail = approve_ticket(db, ticket_id, x_user_id, payload.comment)
    await event_bus.publish({"type": "ticket.updated", "ticketId": ticket_id, "status": detail.status})
    return detail


@router.post("/tickets/{ticket_id}/reject", response_model=TicketDetailOut)
async def reject(
    ticket_id: int,
    payload: DecisionPayload,
    x_user_id: str = Header(default="u001"),
    db: Session = Depends(get_db),
) -> TicketDetailOut:
    detail = reject_ticket(db, ticket_id, x_user_id, payload.comment)
    await event_bus.publish({"type": "ticket.updated", "ticketId": ticket_id, "status": detail.status})
    return detail
```

```python
# audit-workbench/backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.assistant import router as assistant_router
from app.api.routes.events import router as events_router
from app.api.routes.overview import router as overview_router
from app.api.routes.tickets import router as tickets_router
from app.core.config import settings
from app.db.base import Base
from app.db.seed import seed_demo_data
from app.db.session import SessionLocal, engine
from app.models import activity_log, approval_step, sync_health, ticket, watch_relation  # noqa: F401


app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(overview_router)
app.include_router(tickets_router)
app.include_router(assistant_router)
app.include_router(events_router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_data(db)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: 运行测试，确认通过**

Run:

```bash
cd /workspace/audit-workbench/backend
. ../.venv/bin/activate
pytest tests/test_actions_and_assistant.py -q
```

Expected:

```text
3 passed
```

- [ ] **Step 5: 提交**

```bash
cd /workspace
git add audit-workbench/backend
git commit -m "feat: add ticket actions assistant and sse stream"
```

### Task 4: 初始化前端并实现工作台主布局

**Files:**
- Create: `audit-workbench/frontend/package.json`
- Create: `audit-workbench/frontend/tsconfig.json`
- Create: `audit-workbench/frontend/tsconfig.node.json`
- Create: `audit-workbench/frontend/vite.config.ts`
- Create: `audit-workbench/frontend/tailwind.config.cjs`
- Create: `audit-workbench/frontend/postcss.config.cjs`
- Create: `audit-workbench/frontend/index.html`
- Create: `audit-workbench/frontend/src/main.tsx`
- Create: `audit-workbench/frontend/src/App.tsx`
- Create: `audit-workbench/frontend/src/index.css`
- Create: `audit-workbench/frontend/src/types/api.ts`
- Create: `audit-workbench/frontend/src/services/api.ts`
- Create: `audit-workbench/frontend/src/features/workbench/OverviewCards.tsx`
- Create: `audit-workbench/frontend/src/features/workbench/TicketTable.tsx`
- Create: `audit-workbench/frontend/src/features/workbench/WorkbenchPage.tsx`
- Create: `audit-workbench/frontend/src/test/setup.ts`
- Test: `audit-workbench/frontend/src/features/workbench/__tests__/WorkbenchPage.test.tsx`

- [ ] **Step 1: 写出失败测试**

```tsx
// audit-workbench/frontend/src/features/workbench/__tests__/WorkbenchPage.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { WorkbenchPage } from "../WorkbenchPage";

vi.mock("../../../services/api", () => ({
  getOverview: vi.fn().mockResolvedValue({
    todoCount: 2,
    initiatedCount: 2,
    watchingCount: 1,
    syncHealth: { status: "healthy", sourceName: "approval-center", errorCount: 0, message: "最近一次同步成功" }
  }),
  getTickets: vi
    .fn()
    .mockResolvedValueOnce({
      items: [{ id: 1, code: "WK-001", title: "待我处理工单", status: "pending", priority: "high", currentStep: "组长审批", updatedAt: "2026-06-29T09:00:00" }]
    })
    .mockResolvedValueOnce({
      items: [{ id: 2, code: "WK-002", title: "我发起工单", status: "pending", priority: "medium", currentStep: "资产管理员确认", updatedAt: "2026-06-29T09:10:00" }]
    }),
}));


describe("WorkbenchPage", () => {
  it("默认展示待我处理，并在点击概览卡片后切换列表", async () => {
    const user = userEvent.setup();
    render(<WorkbenchPage />);

    expect(await screen.findByText("待我处理")).toBeInTheDocument();
    expect(await screen.findByText("待我处理工单")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "我发起 2" }));

    await waitFor(() => {
      expect(screen.getByText("我发起工单")).toBeInTheDocument();
    });
  });
});
```

- [ ] **Step 2: 运行测试，确认失败**

Run:

```bash
cd /workspace
npm create vite@latest audit-workbench/frontend -- --template react-ts
cd audit-workbench/frontend
npm install
npm install -D tailwindcss@3.4.13 postcss autoprefixer vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
npx tailwindcss init -p
npx vitest run src/features/workbench/__tests__/WorkbenchPage.test.tsx
```

Expected:

```text
FAIL  Cannot find module '../WorkbenchPage'
```

- [ ] **Step 3: 写最小实现**

```json
// audit-workbench/frontend/package.json
{
  "name": "audit-workbench-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "test": "vitest"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.2",
    "@testing-library/react": "^16.0.1",
    "@testing-library/user-event": "^14.5.2",
    "@types/react": "^18.3.10",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.2",
    "autoprefixer": "^10.4.20",
    "jsdom": "^25.0.1",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.13",
    "typescript": "^5.6.2",
    "vite": "^5.4.8",
    "vitest": "^2.1.1"
  }
}
```

```ts
// audit-workbench/frontend/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";


export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    globals: true,
  },
});
```

```js
// audit-workbench/frontend/tailwind.config.cjs
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        gov: {
          50: "#f3f7fc",
          100: "#e8f0fa",
          500: "#1d4f91",
          700: "#153a6b",
          900: "#0d2340"
        }
      },
      boxShadow: {
        soft: "0 10px 24px rgba(15, 23, 42, 0.08)"
      }
    }
  },
  plugins: [],
};
```

```js
// audit-workbench/frontend/postcss.config.cjs
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

```tsx
// audit-workbench/frontend/src/test/setup.ts
import "@testing-library/jest-dom/vitest";
```

```ts
// audit-workbench/frontend/src/types/api.ts
export type Overview = {
  todoCount: number;
  initiatedCount: number;
  watchingCount: number;
  syncHealth: {
    status: string;
    sourceName: string;
    errorCount: number;
    message: string;
  };
};

export type TicketSummary = {
  id: number;
  code: string;
  title: string;
  status: string;
  priority: string;
  currentStep: string;
  updatedAt: string;
};

export type TicketListResponse = {
  items: TicketSummary[];
};
```

```ts
// audit-workbench/frontend/src/services/api.ts
import type { Overview, TicketListResponse } from "../types/api";


const API_BASE = "http://localhost:8000/api";


export async function getOverview(): Promise<Overview> {
  const response = await fetch(`${API_BASE}/overview`, { headers: { "x-user-id": "u001" } });
  return response.json();
}


export async function getTickets(view: "todo" | "initiated" | "watching"): Promise<TicketListResponse> {
  const response = await fetch(`${API_BASE}/tickets?view=${view}`, { headers: { "x-user-id": "u001" } });
  return response.json();
}
```

```tsx
// audit-workbench/frontend/src/features/workbench/OverviewCards.tsx
import type { Overview } from "../../types/api";


type Props = {
  overview: Overview;
  activeView: "todo" | "initiated" | "watching";
  onChange: (view: "todo" | "initiated" | "watching") => void;
};


export function OverviewCards({ overview, activeView, onChange }: Props) {
  const cards = [
    { key: "todo" as const, label: "待我处理", count: overview.todoCount },
    { key: "initiated" as const, label: "我发起", count: overview.initiatedCount },
    { key: "watching" as const, label: "我关注", count: overview.watchingCount },
  ];

  return (
    <div className="space-y-3">
      {cards.map((card) => (
        <button
          key={card.key}
          type="button"
          onClick={() => onChange(card.key)}
          className={`w-full rounded-2xl border p-4 text-left shadow-soft transition ${
            activeView === card.key ? "border-gov-500 bg-gov-50" : "border-slate-200 bg-white"
          }`}
          aria-label={`${card.label} ${card.count}`}
        >
          <div className="text-sm text-slate-500">{card.label}</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900">{card.count}</div>
        </button>
      ))}

      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft">
        <div className="text-sm text-slate-500">系统同步健康</div>
        <div className="mt-2 text-lg font-semibold text-slate-900">{overview.syncHealth.status}</div>
        <div className="mt-1 text-sm text-slate-500">{overview.syncHealth.message}</div>
      </div>
    </div>
  );
}
```

```tsx
// audit-workbench/frontend/src/features/workbench/TicketTable.tsx
import type { TicketSummary } from "../../types/api";


type Props = {
  items: TicketSummary[];
};


export function TicketTable({ items }: Props) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-soft">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-3 text-left">工单编号</th>
            <th className="px-4 py-3 text-left">标题</th>
            <th className="px-4 py-3 text-left">当前节点</th>
            <th className="px-4 py-3 text-left">状态</th>
            <th className="px-4 py-3 text-left">优先级</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {items.map((item) => (
            <tr key={item.id}>
              <td className="px-4 py-3">{item.code}</td>
              <td className="px-4 py-3">{item.title}</td>
              <td className="px-4 py-3">{item.currentStep}</td>
              <td className="px-4 py-3">{item.status}</td>
              <td className="px-4 py-3">{item.priority}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

```tsx
// audit-workbench/frontend/src/features/workbench/WorkbenchPage.tsx
import { useEffect, useState } from "react";

import { getOverview, getTickets } from "../../services/api";
import type { Overview, TicketSummary } from "../../types/api";
import { OverviewCards } from "./OverviewCards";
import { TicketTable } from "./TicketTable";


type View = "todo" | "initiated" | "watching";


export function WorkbenchPage() {
  const [view, setView] = useState<View>("todo");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [items, setItems] = useState<TicketSummary[]>([]);

  useEffect(() => {
    getOverview().then(setOverview);
  }, []);

  useEffect(() => {
    getTickets(view).then((payload) => setItems(payload.items));
  }, [view]);

  if (!overview) return <div className="p-6 text-slate-500">加载中...</div>;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-semibold text-gov-900">统一审批工单工作台</h1>
          <p className="mt-2 text-sm text-slate-500">概览卡片直接作为入口，默认进入“待我处理”列表。</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[280px,1fr]">
          <OverviewCards overview={overview} activeView={view} onChange={setView} />
          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft">
              <div className="text-sm text-slate-500">智能输入</div>
              <input
                className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-gov-500"
                placeholder="例如：这张单卡在哪一步了？"
              />
            </div>
            <TicketTable items={items} />
          </div>
        </div>
      </div>
    </div>
  );
}
```

```tsx
// audit-workbench/frontend/src/App.tsx
import { WorkbenchPage } from "./features/workbench/WorkbenchPage";


export default function App() {
  return <WorkbenchPage />;
}
```

```tsx
// audit-workbench/frontend/src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import "./index.css";


ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

```css
/* audit-workbench/frontend/src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  color-scheme: light;
}

body {
  margin: 0;
  font-family: "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
  background: #f8fafc;
}
```

- [ ] **Step 4: 运行测试，确认通过**

Run:

```bash
cd /workspace/audit-workbench/frontend
npm install
npx vitest run src/features/workbench/__tests__/WorkbenchPage.test.tsx
```

Expected:

```text
✓ src/features/workbench/__tests__/WorkbenchPage.test.tsx (1 test)
```

- [ ] **Step 5: 提交**

```bash
cd /workspace
git add audit-workbench/frontend
git commit -m "feat: add workbench layout and overview cards"
```

### Task 5: 实现详情抽屉、智能体面板与 SSE 联动

**Files:**
- Create: `audit-workbench/frontend/src/services/events.ts`
- Modify: `audit-workbench/frontend/src/types/api.ts`
- Modify: `audit-workbench/frontend/src/services/api.ts`
- Modify: `audit-workbench/frontend/src/features/workbench/TicketTable.tsx`
- Create: `audit-workbench/frontend/src/features/workbench/TicketDrawer.tsx`
- Create: `audit-workbench/frontend/src/features/assistant/AssistantPanel.tsx`
- Modify: `audit-workbench/frontend/src/features/workbench/WorkbenchPage.tsx`
- Test: `audit-workbench/frontend/src/features/workbench/__tests__/WorkbenchRealtime.test.tsx`

- [ ] **Step 1: 写出失败测试**

```tsx
// audit-workbench/frontend/src/features/workbench/__tests__/WorkbenchRealtime.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { WorkbenchPage } from "../WorkbenchPage";


const mockGetOverview = vi.fn().mockResolvedValue({
  todoCount: 2,
  initiatedCount: 2,
  watchingCount: 1,
  syncHealth: { status: "healthy", sourceName: "approval-center", errorCount: 0, message: "最近一次同步成功" }
});

const mockGetTickets = vi.fn().mockResolvedValue({
  items: [{ id: 1, code: "WK-001", title: "待我处理工单", status: "pending", priority: "high", currentStep: "组长审批", updatedAt: "2026-06-29T09:00:00" }]
});

const mockGetTicketDetail = vi.fn().mockResolvedValue({
  id: 1,
  code: "WK-001",
  title: "待我处理工单",
  category: "权限变更",
  status: "pending",
  priority: "high",
  currentStep: "组长审批",
  blockerReason: "等待当前审批人处理",
  recommendedActions: ["提醒当前审批人", "查看审批链路"],
  steps: [{ id: 1, stepName: "组长审批", approverName: "张组长", status: "pending", comment: null }]
});

const mockAskAssistant = vi.fn().mockResolvedValue({
  text: "当前工单处于组长审批节点，等待当前审批人处理。",
  cards: [{
    type: "ticket_progress",
    ticketCode: "WK-001",
    currentStep: "组长审批",
    nextStep: "部门负责人审批",
    status: "pending",
    blockerReason: "等待当前审批人处理",
    recommendedActions: ["提醒当前审批人", "查看审批链路"]
  }],
  suggestions: ["查看审批链路"]
});


vi.mock("../../../services/api", () => ({
  getOverview: (...args: unknown[]) => mockGetOverview(...args),
  getTickets: (...args: unknown[]) => mockGetTickets(...args),
  getTicketDetail: (...args: unknown[]) => mockGetTicketDetail(...args),
  askAssistant: (...args: unknown[]) => mockAskAssistant(...args),
}));

vi.mock("../../../services/events", () => ({
  subscribeToEvents: (onMessage: (event: { type: string; ticketId: number }) => void) => {
    queueMicrotask(() => onMessage({ type: "ticket.updated", ticketId: 1 }));
    return () => undefined;
  },
}));


describe("Workbench realtime behaviors", () => {
  it("打开详情抽屉、发送智能体问题，并在收到 SSE 后重新拉取列表", async () => {
    const user = userEvent.setup();
    render(<WorkbenchPage />);

    expect(await screen.findByText("待我处理工单")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "查看工单 WK-001" }));
    expect(await screen.findByText("等待当前审批人处理")).toBeInTheDocument();

    await user.type(screen.getByPlaceholderText("例如：为什么这张单卡住了？"), "这张单现在到哪一步了？");
    await user.click(screen.getByRole("button", { name: "发送问题" }));

    await waitFor(() => {
      expect(screen.getByText("当前工单处于组长审批节点，等待当前审批人处理。")).toBeInTheDocument();
    });
    expect(mockGetTickets).toHaveBeenCalledTimes(2);
  });
});
```

- [ ] **Step 2: 运行测试，确认失败**

Run:

```bash
cd /workspace/audit-workbench/frontend
npx vitest run src/features/workbench/__tests__/WorkbenchRealtime.test.tsx
```

Expected:

```text
FAIL  getTicketDetail is not a function 或无法找到 TicketDrawer / AssistantPanel
```

- [ ] **Step 3: 写最小实现**

```ts
// audit-workbench/frontend/src/types/api.ts
export type Overview = {
  todoCount: number;
  initiatedCount: number;
  watchingCount: number;
  syncHealth: {
    status: string;
    sourceName: string;
    errorCount: number;
    message: string;
  };
};

export type TicketSummary = {
  id: number;
  code: string;
  title: string;
  status: string;
  priority: string;
  currentStep: string;
  updatedAt: string;
};

export type TicketListResponse = {
  items: TicketSummary[];
};

export type ApprovalStep = {
  id: number;
  stepName: string;
  approverName: string;
  status: string;
  comment: string | null;
};

export type TicketDetail = {
  id: number;
  code: string;
  title: string;
  category: string;
  status: string;
  priority: string;
  currentStep: string;
  blockerReason: string;
  recommendedActions: string[];
  steps: ApprovalStep[];
};

export type AssistantResponse = {
  text: string;
  cards: Array<{
    type: string;
    ticketCode: string;
    currentStep: string;
    nextStep: string;
    status: string;
    blockerReason: string;
    recommendedActions: string[];
  }>;
  suggestions: string[];
};
```

```ts
// audit-workbench/frontend/src/services/api.ts
import type { AssistantResponse, Overview, TicketDetail, TicketListResponse } from "../types/api";


const API_BASE = "http://localhost:8000/api";
const DEFAULT_HEADERS = { "x-user-id": "u001", "Content-Type": "application/json" };


export async function getOverview(): Promise<Overview> {
  const response = await fetch(`${API_BASE}/overview`, { headers: DEFAULT_HEADERS });
  return response.json();
}


export async function getTickets(view: "todo" | "initiated" | "watching"): Promise<TicketListResponse> {
  const response = await fetch(`${API_BASE}/tickets?view=${view}`, { headers: DEFAULT_HEADERS });
  return response.json();
}


export async function getTicketDetail(ticketId: number): Promise<TicketDetail> {
  const response = await fetch(`${API_BASE}/tickets/${ticketId}`, { headers: DEFAULT_HEADERS });
  return response.json();
}


export async function askAssistant(message: string, ticketId?: number): Promise<AssistantResponse> {
  const response = await fetch(`${API_BASE}/assistant/messages`, {
    method: "POST",
    headers: DEFAULT_HEADERS,
    body: JSON.stringify({ message, ticketId }),
  });
  return response.json();
}
```

```ts
// audit-workbench/frontend/src/services/events.ts
export function subscribeToEvents(onMessage: (event: { type: string; ticketId?: number }) => void) {
  const source = new EventSource("http://localhost:8000/api/events");
  source.onmessage = (event) => onMessage(JSON.parse(event.data));
  return () => source.close();
}
```

```tsx
// audit-workbench/frontend/src/features/workbench/TicketTable.tsx
import type { TicketSummary } from "../../types/api";


type Props = {
  items: TicketSummary[];
  onSelect: (ticketId: number) => void;
};


export function TicketTable({ items, onSelect }: Props) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-soft">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-3 text-left">工单编号</th>
            <th className="px-4 py-3 text-left">标题</th>
            <th className="px-4 py-3 text-left">当前节点</th>
            <th className="px-4 py-3 text-left">状态</th>
            <th className="px-4 py-3 text-left">操作</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {items.map((item) => (
            <tr key={item.id}>
              <td className="px-4 py-3">{item.code}</td>
              <td className="px-4 py-3">{item.title}</td>
              <td className="px-4 py-3">{item.currentStep}</td>
              <td className="px-4 py-3">{item.status}</td>
              <td className="px-4 py-3">
                <button
                  type="button"
                  onClick={() => onSelect(item.id)}
                  aria-label={`查看工单 ${item.code}`}
                  className="rounded-lg border border-gov-500 px-3 py-1 text-gov-700"
                >
                  查看
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

```tsx
// audit-workbench/frontend/src/features/workbench/TicketDrawer.tsx
import type { TicketDetail } from "../../types/api";


type Props = {
  detail: TicketDetail | null;
};


export function TicketDrawer({ detail }: Props) {
  if (!detail) return null;

  return (
    <aside className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
      <div className="text-xs uppercase tracking-wide text-slate-500">工单详情</div>
      <h2 className="mt-2 text-xl font-semibold text-slate-900">{detail.title}</h2>
      <div className="mt-2 text-sm text-slate-500">{detail.code}</div>

      <div className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-700">{detail.blockerReason}</div>

      <div className="mt-5 space-y-3">
        {detail.steps.map((step) => (
          <div key={step.id} className="rounded-xl border border-slate-200 p-3">
            <div className="font-medium text-slate-900">{step.stepName}</div>
            <div className="text-sm text-slate-500">{step.approverName}</div>
            <div className="mt-1 text-sm text-slate-600">{step.status}</div>
          </div>
        ))}
      </div>
    </aside>
  );
}
```

```tsx
// audit-workbench/frontend/src/features/assistant/AssistantPanel.tsx
import { useState } from "react";

import type { AssistantResponse } from "../../types/api";


type Props = {
  ticketId?: number;
  onSend: (message: string, ticketId?: number) => Promise<AssistantResponse>;
};


export function AssistantPanel({ ticketId, onSend }: Props) {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState<AssistantResponse | null>(null);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
      <div className="text-sm font-medium text-slate-900">智能助手</div>
      <input
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        placeholder="例如：为什么这张单卡住了？"
        className="mt-3 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-gov-500"
      />
      <button
        type="button"
        onClick={async () => setResponse(await onSend(message, ticketId))}
        className="mt-3 rounded-xl bg-gov-700 px-4 py-2 text-white"
        aria-label="发送问题"
      >
        发送问题
      </button>

      {response ? (
        <div className="mt-4 space-y-3">
          <div className="rounded-xl bg-gov-50 p-4 text-sm text-slate-700">{response.text}</div>
          {response.cards.map((card) => (
            <div key={card.ticketCode} className="rounded-xl border border-gov-100 bg-white p-4">
              <div className="text-sm font-semibold text-slate-900">{card.ticketCode}</div>
              <div className="mt-2 text-sm text-slate-600">当前节点：{card.currentStep}</div>
              <div className="text-sm text-slate-600">下一节点：{card.nextStep}</div>
              <div className="mt-2 text-sm text-slate-600">{card.blockerReason}</div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
```

```tsx
// audit-workbench/frontend/src/features/workbench/WorkbenchPage.tsx
import { useEffect, useState } from "react";

import { AssistantPanel } from "../assistant/AssistantPanel";
import { askAssistant, getOverview, getTicketDetail, getTickets } from "../../services/api";
import { subscribeToEvents } from "../../services/events";
import type { Overview, TicketDetail, TicketSummary } from "../../types/api";
import { OverviewCards } from "./OverviewCards";
import { TicketDrawer } from "./TicketDrawer";
import { TicketTable } from "./TicketTable";


type View = "todo" | "initiated" | "watching";


export function WorkbenchPage() {
  const [view, setView] = useState<View>("todo");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [items, setItems] = useState<TicketSummary[]>([]);
  const [selectedTicketId, setSelectedTicketId] = useState<number | undefined>(undefined);
  const [detail, setDetail] = useState<TicketDetail | null>(null);

  async function loadOverview() {
    setOverview(await getOverview());
  }

  async function loadTickets(currentView: View) {
    const payload = await getTickets(currentView);
    setItems(payload.items);
  }

  useEffect(() => {
    loadOverview();
  }, []);

  useEffect(() => {
    loadTickets(view);
  }, [view]);

  useEffect(() => {
    const unsubscribe = subscribeToEvents(async () => {
      await loadOverview();
      await loadTickets(view);
      if (selectedTicketId) {
        setDetail(await getTicketDetail(selectedTicketId));
      }
    });

    return unsubscribe;
  }, [view, selectedTicketId]);

  async function handleSelect(ticketId: number) {
    setSelectedTicketId(ticketId);
    setDetail(await getTicketDetail(ticketId));
  }

  if (!overview) return <div className="p-6 text-slate-500">加载中...</div>;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-semibold text-gov-900">统一审批工单工作台</h1>
          <p className="mt-2 text-sm text-slate-500">概览卡片直接承担导航功能，智能体负责解释流程与推荐下一步动作。</p>
        </div>

        <div className="grid gap-6 xl:grid-cols-[280px,1fr,360px]">
          <OverviewCards overview={overview} activeView={view} onChange={setView} />
          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft">
              <div className="text-sm text-slate-500">智能输入</div>
              <input
                className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-gov-500"
                placeholder="例如：这张单卡在哪一步了？"
              />
            </div>
            <TicketTable items={items} onSelect={handleSelect} />
          </div>
          <div className="space-y-4">
            <TicketDrawer detail={detail} />
            <AssistantPanel ticketId={selectedTicketId} onSend={askAssistant} />
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: 运行测试，确认通过**

Run:

```bash
cd /workspace/audit-workbench/frontend
npx vitest run src/features/workbench/__tests__/WorkbenchRealtime.test.tsx
```

Expected:

```text
✓ src/features/workbench/__tests__/WorkbenchRealtime.test.tsx (1 test)
```

- [ ] **Step 5: 提交**

```bash
cd /workspace
git add audit-workbench/frontend
git commit -m "feat: add ticket drawer assistant panel and sse refresh"
```

### Task 6: 联调、启动脚本与最终验收

**Files:**
- Modify: `audit-workbench/README.md`
- Create: `audit-workbench/backend/tests/test_full_flow.py`
- Create: `audit-workbench/frontend/src/features/workbench/__tests__/TicketDrawer.test.tsx`
- Create: `audit-workbench/frontend/src/features/assistant/__tests__/AssistantPanel.test.tsx`

- [ ] **Step 1: 写出失败测试**

```python
# audit-workbench/backend/tests/test_full_flow.py
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_full_ticket_flow_supports_overview_detail_and_assistant() -> None:
    overview = client.get("/api/overview", headers={"x-user-id": "u001"})
    assert overview.status_code == 200

    tickets = client.get("/api/tickets?view=todo", headers={"x-user-id": "u001"})
    assert tickets.status_code == 200
    first_ticket_id = tickets.json()["items"][0]["id"]

    detail = client.get(f"/api/tickets/{first_ticket_id}", headers={"x-user-id": "u001"})
    assert detail.status_code == 200

    answer = client.post(
        "/api/assistant/messages",
        json={"message": "为什么这张单卡住了？", "ticketId": first_ticket_id},
        headers={"x-user-id": "u001"},
    )
    assert answer.status_code == 200
    assert answer.json()["cards"][0]["ticketCode"].startswith("WK-")
```

```tsx
// audit-workbench/frontend/src/features/workbench/__tests__/TicketDrawer.test.tsx
import { render, screen } from "@testing-library/react";

import { TicketDrawer } from "../TicketDrawer";


describe("TicketDrawer", () => {
  it("展示阻塞原因和审批步骤", () => {
    render(
      <TicketDrawer
        detail={{
          id: 1,
          code: "WK-001",
          title: "待我处理工单",
          category: "权限变更",
          status: "pending",
          priority: "high",
          currentStep: "组长审批",
          blockerReason: "等待当前审批人处理",
          recommendedActions: ["提醒当前审批人"],
          steps: [{ id: 1, stepName: "组长审批", approverName: "张组长", status: "pending", comment: null }],
        }}
      />
    );

    expect(screen.getByText("等待当前审批人处理")).toBeInTheDocument();
    expect(screen.getByText("张组长")).toBeInTheDocument();
  });
});
```

```tsx
// audit-workbench/frontend/src/features/assistant/__tests__/AssistantPanel.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AssistantPanel } from "../AssistantPanel";


describe("AssistantPanel", () => {
  it("发送问题后渲染智能体卡片", async () => {
    const user = userEvent.setup();
    render(
      <AssistantPanel
        ticketId={1}
        onSend={async () => ({
          text: "当前工单处于组长审批节点。",
          cards: [
            {
              type: "ticket_progress",
              ticketCode: "WK-001",
              currentStep: "组长审批",
              nextStep: "部门负责人审批",
              status: "pending",
              blockerReason: "等待当前审批人处理",
              recommendedActions: ["提醒当前审批人", "查看审批链路"],
            },
          ],
          suggestions: ["查看审批链路"],
        })}
      />
    );

    await user.type(screen.getByPlaceholderText("例如：为什么这张单卡住了？"), "现在到哪一步了");
    await user.click(screen.getByRole("button", { name: "发送问题" }));

    expect(await screen.findByText("当前工单处于组长审批节点。")).toBeInTheDocument();
    expect(screen.getByText("下一节点：部门负责人审批")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行测试，确认失败**

Run:

```bash
cd /workspace/audit-workbench/backend
. ../.venv/bin/activate
pytest tests/test_full_flow.py -q
cd /workspace/audit-workbench/frontend
npx vitest run src/features/workbench/__tests__/TicketDrawer.test.tsx src/features/assistant/__tests__/AssistantPanel.test.tsx
```

Expected:

```text
至少一个测试失败，因为 README 还未补齐完整联调说明，且部分目录/测试文件尚未存在
```

- [ ] **Step 3: 写最小实现**

```md
<!-- audit-workbench/README.md -->
# audit-workbench

审批工单工作台与智能体 MVP。

## 目录

- `backend/`：FastAPI + SQLite + SSE
- `frontend/`：React + Vite + Tailwind 工作台

## 本地启动

### 1. 启动后端

```bash
cd backend
python3 -m venv ../.venv
. ../.venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

### 3. 运行测试

```bash
cd backend
. ../.venv/bin/activate
pytest

cd ../frontend
npm test -- --run
```

## 演示路径

1. 打开工作台首页，默认进入“待我处理”
2. 点击“我发起”或“我关注”概览卡片切换右侧列表
3. 点击工单行右侧“查看”按钮打开详情抽屉
4. 在智能体面板提问“这张单现在到哪一步了？”
5. 观察智能体返回文本说明与进度卡片
```

- [ ] **Step 4: 运行测试，确认通过**

Run:

```bash
cd /workspace/audit-workbench/backend
. ../.venv/bin/activate
pytest -q
cd /workspace/audit-workbench/frontend
npm test -- --run
```

Expected:

```text
后端测试全部通过
前端测试全部通过
```

- [ ] **Step 5: 提交**

```bash
cd /workspace
git add audit-workbench
git commit -m "test: cover full workbench flow and document local runbook"
```

## Self-Review

### Spec coverage

- 独立新仓库：Task 1、Task 4、Task 6
- FastAPI + SQLite：Task 1、Task 2、Task 3
- 概览卡片直达列表：Task 4
- 默认进入待我处理：Task 4
- 工单详情与审批链路：Task 2、Task 5
- 智能体文本 + 进度卡片：Task 3、Task 5
- SSE 近实时刷新：Task 3、Task 5
- 政务/国企蓝布局：Task 4、Task 5
- 测试与本地运行说明：Task 6

### Placeholder scan

- 已检查全文，无 `TBD`、`TODO`、`implement later`、`similar to task` 等占位表达。

### Type consistency

- 后端 `OverviewOut`、`TicketListOut`、`TicketDetailOut`、`AssistantMessageOut` 与前端 `Overview`、`TicketListResponse`、`TicketDetail`、`AssistantResponse` 字段名已对齐。
- 前端统一使用 `view: "todo" | "initiated" | "watching"`，与后端查询参数一致。
- 智能体卡片统一使用 `ticketCode`、`currentStep`、`nextStep`、`status`、`blockerReason`、`recommendedActions`。
