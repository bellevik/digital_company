from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import ReviewDecisionType, TimestampMixin, enum_values, uuid_primary_key


class ReviewDecision(TimestampMixin, Base):
    __tablename__ = "review_decisions"

    id: Mapped[uuid.UUID] = uuid_primary_key()
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("task_workflows.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("task_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    decision: Mapped[ReviewDecisionType] = mapped_column(
        Enum(ReviewDecisionType, name="review_decision_type", values_callable=enum_values),
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    task: Mapped["Task"] = relationship("Task", back_populates="review_decisions")
    task_workflow: Mapped["TaskWorkflow"] = relationship("TaskWorkflow", back_populates="review_decisions")
    task_run: Mapped["TaskRun | None"] = relationship("TaskRun")
