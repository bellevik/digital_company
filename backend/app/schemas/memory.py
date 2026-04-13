from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.common import MemoryType


class MemoryCreate(BaseModel):
    type: MemoryType
    summary: str
    content: str
    source_task_id: uuid.UUID | None = None


class MemoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: MemoryType
    summary: str
    content: str
    source_task_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
