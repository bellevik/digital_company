from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import db_session_dependency
from app.models.common import EventType
from app.models.memory import Memory
from app.models.task_event import TaskEvent
from app.schemas.memory import MemoryCreate, MemoryRead

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("", response_model=list[MemoryRead])
def list_memories(db: Session = Depends(db_session_dependency)) -> list[Memory]:
    return list(db.scalars(select(Memory).order_by(Memory.created_at.desc())).all())


@router.post("", response_model=MemoryRead, status_code=status.HTTP_201_CREATED)
def create_memory(payload: MemoryCreate, db: Session = Depends(db_session_dependency)) -> Memory:
    memory = Memory(
        type=payload.type,
        summary=payload.summary,
        content=payload.content,
        source_task_id=payload.source_task_id,
    )
    db.add(memory)
    db.flush()
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

