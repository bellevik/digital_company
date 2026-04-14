from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TaskRunStatus, TimestampMixin, enum_values, uuid_primary_key


class TaskRun(TimestampMixin, Base):
    __tablename__ = "task_runs"
    __table_args__ = (
        Index("ix_task_runs_task_id", "task_id"),
        Index("ix_task_runs_agent_id", "agent_id"),
    )

    id: Mapped[uuid.UUID] = uuid_primary_key()
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[TaskRunStatus] = mapped_column(
        Enum(TaskRunStatus, name="task_run_status", values_callable=enum_values),
        nullable=False,
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    stdout: Mapped[str] = mapped_column(Text, default="", nullable=False)
    stderr: Mapped[str] = mapped_column(Text, default="", nullable=False)
    exit_code: Mapped[int | None] = mapped_column(nullable=True)
    result_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_follow_up_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    task: Mapped["Task"] = relationship("Task", back_populates="task_runs")
    agent: Mapped["Agent"] = relationship("Agent", back_populates="task_runs")
    workflows: Mapped[list["TaskWorkflow"]] = relationship(
        "TaskWorkflow",
        foreign_keys="TaskWorkflow.latest_task_run_id",
        overlaps="latest_task_run",
    )
