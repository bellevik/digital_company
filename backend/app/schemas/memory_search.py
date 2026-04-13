from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.common import MemoryType


class MemorySearchResult(BaseModel):
    memory_id: uuid.UUID
    type: MemoryType
    summary: str
    content: str
    source_task_id: uuid.UUID | None
    created_at: datetime
    keyword_score: float
    vector_score: float
    combined_score: float

