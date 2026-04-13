from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import db_session_dependency
from app.models.task_run import TaskRun
from app.schemas.task_run import TaskRunRead

router = APIRouter(prefix="/task-runs", tags=["task-runs"])


@router.get("", response_model=list[TaskRunRead])
def list_task_runs(
    task_id: uuid.UUID | None = Query(default=None),
    agent_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(db_session_dependency),
) -> list[TaskRun]:
    query = select(TaskRun).order_by(TaskRun.created_at.desc())
    if task_id is not None:
        query = query.where(TaskRun.task_id == task_id)
    if agent_id is not None:
        query = query.where(TaskRun.agent_id == agent_id)
    return list(db.scalars(query).all())
