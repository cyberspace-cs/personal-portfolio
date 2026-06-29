from datetime import datetime

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


class ActivityOut(BaseModel):
    id: int
    action: str
    operatorName: str
    content: str
    createdAt: datetime


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
    activities: list[ActivityOut]


class DecisionPayload(BaseModel):
    comment: str


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
