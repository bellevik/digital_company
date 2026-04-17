from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid

from app.db.base import Base
from app.models.common import TaskStatus, TaskType, TimestampMixin, enum_values, uuid_primary_key


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_project_id", "project_id"),
    )

    id: Mapped[uuid.UUID] = uuid_primary_key()
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[TaskType] = mapped_column(
        Enum(TaskType, name="task_type", values_callable=enum_values),
        nullable=False,
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status", values_callable=enum_values),
        default=TaskStatus.TODO,
        nullable=False,
    )
    assigned_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
    )
    project_id: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    plan_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    plan_item_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assigned_agent: Mapped["Agent | None"] = relationship(
        "Agent",
        back_populates="assigned_tasks",
        foreign_keys=[assigned_agent_id],
    )
    project: Mapped["Project | None"] = relationship("Project", back_populates="tasks")
    memories: Mapped[list["Memory"]] = relationship("Memory", back_populates="source_task")
    events: Mapped[list["TaskEvent"]] = relationship("TaskEvent", back_populates="task")
    task_runs: Mapped[list["TaskRun"]] = relationship("TaskRun", back_populates="task")
    workflow: Mapped["TaskWorkflow | None"] = relationship("TaskWorkflow", back_populates="task", uselist=False)
    review_decisions: Mapped[list["ReviewDecision"]] = relationship(
        "ReviewDecision",
        back_populates="task",
        cascade="all, delete-orphan",
    )
