from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.models.common import TaskRunStatus, TaskType
from app.schemas.task_run import TaskRunRead


class WorkerPlannedTask(BaseModel):
    title: str
    description: str
    type: TaskType
    spawn_budget: int = 0


class WorkerFollowUpTask(BaseModel):
    title: str
    description: str
    type: TaskType
    project_id: str | None = None


class WorkerExecutionPayload(BaseModel):
    summary: str
    memory_summary: str | None = None
    memory_content: str | None = None
    plan_summary: str | None = None
    max_total_tasks: int | None = None
    planned_tasks: list[WorkerPlannedTask] = Field(default_factory=list)
    final_status: TaskRunStatus | None = None
    artifact_paths: list[str] = Field(default_factory=list)
    follow_up_tasks: list[WorkerFollowUpTask] = Field(default_factory=list)


class WorkerCycleResponse(BaseModel):
    agent_id: uuid.UUID
    outcome: str
    task_id: uuid.UUID | None = None
    task_run: TaskRunRead | None = None
    memory_id: uuid.UUID | None = None
    follow_up_task_ids: list[uuid.UUID] = Field(default_factory=list)


class WorkerBatchResponse(BaseModel):
    total_agents: int
    completed: int
    failed: int
    idle: int
    results: list[WorkerCycleResponse] = Field(default_factory=list)
