from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import db_session_dependency
from app.config import get_settings
from app.models.common import AgentStatus, EventType, TaskStatus
from app.models.task import Task
from app.models.task_event import TaskEvent
from app.repositories.task_repository import TaskClaimConflictError, claim_task
from app.schemas.task import (
    TaskClaimRequest,
    TaskCreate,
    TaskEventRead,
    TaskRead,
    TaskUpdate,
)
from app.schemas.workflow import ReviewDecisionCreate, SubmitForReviewRequest, TaskWorkflowRead
from app.services.project_workspace import ProjectWorkspaceService
from app.services.workflow import WorkflowService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
def list_tasks(
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(db_session_dependency),
) -> list[Task]:
    query = select(Task).order_by(Task.created_at.desc())
    if status_filter is not None:
        query = query.where(Task.status == status_filter)
    return list(db.scalars(query).all())


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(db_session_dependency)) -> Task:
    workspace_service = ProjectWorkspaceService(settings=get_settings())
    try:
        project_id = workspace_service.normalize_project_id(payload.project_id)
        workspace_service.ensure_project_directory(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    task = Task(
        title=payload.title,
        description=payload.description,
        type=payload.type,
        project_id=project_id,
    )
    db.add(task)
    db.flush()
    db.add(
        TaskEvent(
            task_id=task.id,
            event_type=EventType.TASK_CREATED,
            payload={"title": task.title, "type": task.type.value},
        )
    )
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    db: Session = Depends(db_session_dependency),
) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    workspace_service = ProjectWorkspaceService(settings=get_settings())
    previous_agent = task.assigned_agent
    update_data = payload.model_dump(exclude_unset=True)
    if "project_id" in update_data:
        try:
            update_data["project_id"] = workspace_service.normalize_project_id(update_data["project_id"])
            workspace_service.ensure_project_directory(update_data["project_id"])
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

    for field_name, value in update_data.items():
        setattr(task, field_name, value)

    if task.status in {TaskStatus.DONE, TaskStatus.FAILED} and task.completed_at is None:
        task.completed_at = datetime.now(timezone.utc)
    if task.status == TaskStatus.TODO:
        task.completed_at = None
        task.assigned_agent_id = None

    if task.status != TaskStatus.IN_PROGRESS and previous_agent is not None:
        if previous_agent.current_task_id == task.id:
            previous_agent.current_task_id = None
            previous_agent.status = AgentStatus.IDLE

    db.add(
        TaskEvent(
            task_id=task.id,
            agent_id=previous_agent.id if previous_agent is not None else task.assigned_agent_id,
            event_type=EventType.TASK_UPDATED,
            payload=update_data,
        )
    )
    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/claim", response_model=TaskRead)
def claim_task_endpoint(
    task_id: uuid.UUID,
    payload: TaskClaimRequest,
    db: Session = Depends(db_session_dependency),
) -> Task:
    try:
        task = claim_task(db=db, task_id=task_id, agent_id=payload.agent_id)
        db.commit()
        db.refresh(task)
        return task
    except LookupError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        ) from exc
    except TaskClaimConflictError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get("/{task_id}/events", response_model=list[TaskEventRead])
def list_task_events(
    task_id: uuid.UUID,
    db: Session = Depends(db_session_dependency),
) -> list[TaskEvent]:
    return list(
        db.scalars(
            select(TaskEvent)
            .where(TaskEvent.task_id == task_id)
            .order_by(TaskEvent.created_at.asc())
        ).all()
    )


@router.post("/{task_id}/submit-for-review", response_model=TaskWorkflowRead)
def submit_task_for_review(
    task_id: uuid.UUID,
    payload: SubmitForReviewRequest,
    db: Session = Depends(db_session_dependency),
) -> TaskWorkflowRead:
    try:
        return WorkflowService(db=db).submit_for_review(task_id=task_id, payload=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc


@router.post("/{task_id}/review-decisions", response_model=TaskWorkflowRead)
def record_review_decision(
    task_id: uuid.UUID,
    payload: ReviewDecisionCreate,
    db: Session = Depends(db_session_dependency),
) -> TaskWorkflowRead:
    try:
        return WorkflowService(db=db).record_review_decision(task_id=task_id, payload=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc
