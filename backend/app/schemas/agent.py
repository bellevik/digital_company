from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.common import AgentRole, AgentStatus


class AgentCreate(BaseModel):
    name: str
    role: AgentRole


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    role: AgentRole
    status: AgentStatus
    current_task_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

