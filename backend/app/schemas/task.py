from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.common import EventType, TaskStatus, TaskType


class TaskCreate(BaseModel):
    title: str
    description: str
    type: TaskType
    project_id: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    type: TaskType | None = None
    status: TaskStatus | None = None
    project_id: str | None = None


class TaskClaimRequest(BaseModel):
    agent_id: uuid.UUID


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    type: TaskType
    status: TaskStatus
    assigned_agent_id: uuid.UUID | None
    project_id: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class TaskEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID | None
    agent_id: uuid.UUID | None
    event_type: EventType
    payload: dict
    created_at: datetime

