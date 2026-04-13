from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import db_session_dependency
from app.config import get_settings
from app.models.common import EventType
from app.models.memory import Memory
from app.models.task_event import TaskEvent
from app.schemas.memory import MemoryCreate, MemoryRead
from app.schemas.memory_search import MemorySearchResult
from app.services.memory import MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("", response_model=list[MemoryRead])
def list_memories(
    source_task_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(db_session_dependency),
) -> list[Memory]:
    query = select(Memory).order_by(Memory.created_at.desc())
    if source_task_id is not None:
        query = query.where(Memory.source_task_id == source_task_id)
    return list(db.scalars(query).all())


@router.get("/search", response_model=list[MemorySearchResult])
def search_memories(
    query: str,
    strategy: str = Query(default="hybrid", pattern="^(keyword|vector|hybrid)$"),
    limit: int = Query(default=5, ge=1, le=20),
    project_id: str | None = Query(default=None),
    source_task_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(db_session_dependency),
) -> list[MemorySearchResult]:
    service = MemoryService(db=db, settings=get_settings())
    return service.search_memories(
        query=query,
        limit=limit,
        project_id=project_id,
        source_task_id=source_task_id,
        strategy=strategy,
    )


@router.post("", response_model=MemoryRead, status_code=status.HTTP_201_CREATED)
def create_memory(payload: MemoryCreate, db: Session = Depends(db_session_dependency)) -> Memory:
    service = MemoryService(db=db, settings=get_settings())
    memory = service.create_memory(
        memory_type=payload.type,
        summary=payload.summary,
        content=payload.content,
        source_task_id=payload.source_task_id,
    )
    db.add(
        TaskEvent(
            task_id=memory.source_task_id,
            event_type=EventType.MEMORY_CREATED,
            payload={"memory_id": str(memory.id), "type": memory.type.value},
        )
    )
    db.commit()
    db.refresh(memory)
    return memory
