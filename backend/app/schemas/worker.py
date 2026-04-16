from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.models.common import TaskRunStatus, TaskType
from app.schemas.task_run import TaskRunRead


class WorkerFollowUpTask(BaseModel):
    title: str
    description: str
    type: TaskType
    project_id: str | None = None


class WorkerExecutionPayload(BaseModel):
    summary: str
    memory_summary: str | None = None
    memory_content: str | None = None
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
