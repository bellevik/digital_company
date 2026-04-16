from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import db_session_dependency
from app.config import get_settings
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectRead
from app.services.projects import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(db_session_dependency)) -> list[Project]:
    return ProjectService(db=db, settings=get_settings()).list_projects()


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(db_session_dependency),
) -> Project:
    try:
        return ProjectService(db=db, settings=get_settings()).create_project(payload)
    except ValueError as exc:
        detail = str(exc)
        status_code = (
            status.HTTP_409_CONFLICT
            if detail in {"project already exists", "project name already exists"}
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(status_code=status_code, detail=detail) from exc
