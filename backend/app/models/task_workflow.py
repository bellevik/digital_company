from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import ApprovalStatus, TimestampMixin, enum_values, uuid_primary_key


class TaskWorkflow(TimestampMixin, Base):
    __tablename__ = "task_workflows"
    __table_args__ = (Index("ix_task_workflows_approval_status", "approval_status"),)

    id: Mapped[uuid.UUID] = uuid_primary_key()
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    latest_task_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("task_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="approval_status", values_callable=enum_values),
        default=ApprovalStatus.NOT_REQUIRED,
        nullable=False,
    )
    branch_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    submission_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_for_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    task: Mapped["Task"] = relationship("Task", back_populates="workflow")
    latest_task_run: Mapped["TaskRun | None"] = relationship(
        "TaskRun",
        foreign_keys=[latest_task_run_id],
        overlaps="workflows",
    )
    review_decisions: Mapped[list["ReviewDecision"]] = relationship(
        "ReviewDecision",
        back_populates="task_workflow",
        cascade="all, delete-orphan",
    )
