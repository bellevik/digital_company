from __future__ import annotations

import uuid

from sqlalchemy import JSON, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import AgentRole, AgentStatus, TimestampMixin, enum_values, uuid_primary_key


class Agent(TimestampMixin, Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = uuid_primary_key()
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    role: Mapped[AgentRole] = mapped_column(
        Enum(AgentRole, name="agent_role", values_callable=enum_values),
        nullable=False,
    )
    template_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    skill_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus, name="agent_status", values_callable=enum_values),
        default=AgentStatus.IDLE,
        nullable=False,
    )
    current_task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL", use_alter=True, name="fk_agents_current_task_id_tasks"),
        nullable=True,
    )

    current_task: Mapped["Task | None"] = relationship(
        "Task",
        foreign_keys=[current_task_id],
        post_update=True,
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="assigned_agent",
        foreign_keys="Task.assigned_agent_id",
    )
    events: Mapped[list["TaskEvent"]] = relationship("TaskEvent", back_populates="agent")
    task_runs: Mapped[list["TaskRun"]] = relationship("TaskRun", back_populates="agent")
