from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.common import TaskRunStatus


class TaskRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    agent_id: uuid.UUID
    status: TaskRunStatus
    prompt: str
    stdout: str
    stderr: str
    exit_code: int | None
    result_payload: dict
    created_follow_up_tasks: int
    started_at: datetime
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime
