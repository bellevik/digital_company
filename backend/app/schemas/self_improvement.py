from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.common import SelfImprovementRunStatus, SelfImprovementTriggerMode


class SelfImprovementRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: SelfImprovementRunStatus
    trigger_mode: SelfImprovementTriggerMode
    summary: str
    proposed_branch_name: str
    proposed_pr_title: str
    created_task_count: int
    payload: dict
    started_at: datetime
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SystemSummary(BaseModel):
    tasks_total: int
    tasks_todo: int
    tasks_in_progress: int
    tasks_done: int
    tasks_failed: int
    agents_total: int
    agents_idle: int
    agents_busy: int
    agents_offline: int
    workflows_pending: int
    memories_total: int
    task_runs_total: int
    self_improvement_runs_total: int
    scheduler_enabled: bool
    scheduler_running: bool


class SeedDemoResponse(BaseModel):
    created_agents: int
    created_tasks: int
    created_memories: int
    message: str
