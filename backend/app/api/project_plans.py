from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import db_session_dependency
from app.config import get_settings
from app.schemas.project_plan import IdeaPitchRequest, PlanChangeRequest, ProjectPlanRead
from app.services.project_plans import ProjectPlanService
from app.services.projects import ProjectService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/project-plans", tags=["project-plans"])


@router.get("", response_model=list[ProjectPlanRead])
def list_project_plans(
    project_id: str | None = Query(default=None),
    db: Session = Depends(db_session_dependency),
) -> list:
    settings = get_settings()
    service = ProjectPlanService(
        db=db,
        project_service=ProjectService(db=db, settings=settings),
    )
    return service.list_plans(project_id=project_id)


@router.post("/projects/{project_id}/pitch", response_model=ProjectPlanRead, status_code=status.HTTP_201_CREATED)
def pitch_project_idea(
    project_id: str,
    payload: IdeaPitchRequest,
    db: Session = Depends(db_session_dependency),
):
    settings = get_settings()
    service = ProjectPlanService(
        db=db,
        project_service=ProjectService(db=db, settings=settings),
    )
    try:
        return service.pitch_idea(project_id=project_id, payload=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project_not_found") from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Project idea pitch failed", extra={"project_id": project_id})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="project_pitch_failed") from exc


@router.post("/{plan_id}/approve", response_model=ProjectPlanRead)
def approve_project_plan(plan_id: uuid.UUID, db: Session = Depends(db_session_dependency)):
    settings = get_settings()
    service = ProjectPlanService(
        db=db,
        project_service=ProjectService(db=db, settings=settings),
    )
    try:
        return service.approve_plan(plan_id=plan_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan_not_found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{plan_id}/request-changes", response_model=ProjectPlanRead)
def request_plan_changes(
    plan_id: uuid.UUID,
    payload: PlanChangeRequest,
    db: Session = Depends(db_session_dependency),
):
    settings = get_settings()
    service = ProjectPlanService(
        db=db,
        project_service=ProjectService(db=db, settings=settings),
    )
    try:
        return service.request_changes(plan_id=plan_id, feedback=payload.feedback)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan_not_found") from exc
