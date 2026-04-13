from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import db_session_dependency
from app.models.common import ApprovalStatus
from app.schemas.workflow import ReviewDecisionCreate, TaskWorkflowRead
from app.services.workflow import WorkflowService

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("", response_model=list[TaskWorkflowRead])
def list_workflows(
    approval_status: ApprovalStatus | None = Query(default=None),
    db: Session = Depends(db_session_dependency),
) -> list[TaskWorkflowRead]:
    return WorkflowService(db=db).list_workflows(approval_status=approval_status)


@router.get("/{task_id}", response_model=TaskWorkflowRead)
def get_workflow(task_id: uuid.UUID, db: Session = Depends(db_session_dependency)) -> TaskWorkflowRead:
    workflow = WorkflowService(db=db).get_workflow(task_id=task_id)
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return workflow
