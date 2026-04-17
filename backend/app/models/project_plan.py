from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import (
    ProjectPlanStatus,
    ProjectPlanTaskStatus,
    TaskType,
    TimestampMixin,
    enum_values,
    uuid_primary_key,
)


class ProjectPlan(TimestampMixin, Base):
    __tablename__ = "project_plans"

    id: Mapped[uuid.UUID] = uuid_primary_key()
    project_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    planning_task_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    idea_title: Mapped[str] = mapped_column(String(255), nullable=False)
    idea_description: Mapped[str] = mapped_column(Text, nullable=False)
    planner_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectPlanStatus] = mapped_column(
        Enum(ProjectPlanStatus, name="project_plan_status", values_callable=enum_values),
        nullable=False,
        default=ProjectPlanStatus.DRAFT,
    )
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_total_tasks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="plans")
    items: Mapped[list["ProjectPlanTask"]] = relationship(
        "ProjectPlanTask",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="ProjectPlanTask.sequence.asc()",
    )


class ProjectPlanTask(TimestampMixin, Base):
    __tablename__ = "project_plan_tasks"

    id: Mapped[uuid.UUID] = uuid_primary_key()
    project_plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_plan_task_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    source_task_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    created_task_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[TaskType] = mapped_column(
        Enum(TaskType, name="task_type", values_callable=enum_values),
        nullable=False,
    )
    status: Mapped[ProjectPlanTaskStatus] = mapped_column(
        Enum(ProjectPlanTaskStatus, name="project_plan_task_status", values_callable=enum_values),
        nullable=False,
        default=ProjectPlanTaskStatus.PROPOSED,
    )
    spawn_budget: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    plan: Mapped["ProjectPlan"] = relationship("ProjectPlan", back_populates="items")
