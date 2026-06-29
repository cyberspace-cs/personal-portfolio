from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


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

    steps: Mapped[list["ApprovalStep"]] = relationship(
        "ApprovalStep",
        back_populates="ticket",
        foreign_keys="ApprovalStep.ticket_id",
        cascade="all, delete-orphan",
    )
    activities: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="ActivityLog.created_at.desc()",
    )


class ApprovalStep(Base):
    __tablename__ = "approval_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    step_name: Mapped[str] = mapped_column(String(64))
    approver_name: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    comment: Mapped[str | None] = mapped_column(Text(), nullable=True)
    acted_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer)

    ticket: Mapped[Ticket] = relationship("Ticket", back_populates="steps", foreign_keys=[ticket_id])


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    action: Mapped[str] = mapped_column(String(64))
    operator_name: Mapped[str] = mapped_column(String(64))
    content: Mapped[str] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(DateTime())

    ticket: Mapped[Ticket] = relationship("Ticket", back_populates="activities")


class WatchRelation(Base):
    __tablename__ = "watch_relations"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)


class SyncHealth(Base):
    __tablename__ = "sync_health"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    last_synced_at: Mapped[datetime] = mapped_column(DateTime())
    error_count: Mapped[int] = mapped_column(Integer)
    message: Mapped[str] = mapped_column(Text())
