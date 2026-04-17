from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import ProjectPlanStatus, ProjectPlanTaskStatus, TaskType


class IdeaPitchRequest(BaseModel):
    idea_title: str
    idea_description: str


class PlanChangeRequest(BaseModel):
    feedback: str


class ProjectPlanTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    parent_plan_task_id: uuid.UUID | None
    source_task_id: uuid.UUID | None
    created_task_id: uuid.UUID | None
    sequence: int
    title: str
    description: str
    type: TaskType
    status: ProjectPlanTaskStatus
    spawn_budget: int
    created_at: datetime
    updated_at: datetime


class ProjectPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: str
    planning_task_id: uuid.UUID | None
    idea_title: str
    idea_description: str
    planner_summary: str | None
    status: ProjectPlanStatus
    feedback: str | None
    max_total_tasks: int
    created_task_count: int
    approved_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[ProjectPlanTaskRead] = Field(default_factory=list)
