from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import db_session_dependency
from app.config import get_settings
from app.schemas.project import (
    ProjectCreate,
    ProjectRead,
    ProjectResetResponse,
    ProjectRuntimeActionResponse,
)
from app.services.projects import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(db_session_dependency)) -> list[ProjectRead]:
    return ProjectService(db=db, settings=get_settings()).list_projects()


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(db_session_dependency),
) -> ProjectRead:
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


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_project(project_id: str, db: Session = Depends(db_session_dependency)) -> Response:
    try:
        ProjectService(db=db, settings=get_settings()).delete_project(project_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project_not_found") from exc
    except ValueError as exc:
        detail = str(exc)
        status_code = (
            status.HTTP_409_CONFLICT if detail in {"project_has_tasks", "project_has_files"} else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(status_code=status_code, detail=detail) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{project_id}/reset", response_model=ProjectResetResponse)
def reset_project(project_id: str, db: Session = Depends(db_session_dependency)) -> ProjectResetResponse:
    try:
        return ProjectService(db=db, settings=get_settings()).reset_project(project_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project_not_found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="project_reset_failed",
        ) from exc


@router.get("/{project_id}/runtime", response_model=ProjectRuntimeActionResponse)
def project_runtime_status(
    project_id: str,
    db: Session = Depends(db_session_dependency),
) -> ProjectRuntimeActionResponse:
    service = ProjectService(db=db, settings=get_settings())
    try:
        project = service.get_project(project_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project_not_found") from exc

    return ProjectRuntimeActionResponse(
        project_id=project.id,
        message="runtime_status_loaded",
        runtime=service.serialize_project(project).runtime,
    )


@router.post("/{project_id}/runtime/start", response_model=ProjectRuntimeActionResponse)
def start_project_runtime(
    project_id: str,
    db: Session = Depends(db_session_dependency),
) -> ProjectRuntimeActionResponse:
    return _runtime_action(project_id=project_id, action="start", db=db)


@router.post("/{project_id}/runtime/stop", response_model=ProjectRuntimeActionResponse)
def stop_project_runtime(
    project_id: str,
    db: Session = Depends(db_session_dependency),
) -> ProjectRuntimeActionResponse:
    return _runtime_action(project_id=project_id, action="stop", db=db)


@router.post("/{project_id}/runtime/restart", response_model=ProjectRuntimeActionResponse)
def restart_project_runtime(
    project_id: str,
    db: Session = Depends(db_session_dependency),
) -> ProjectRuntimeActionResponse:
    return _runtime_action(project_id=project_id, action="restart", db=db)


def _runtime_action(
    *,
    project_id: str,
    action: str,
    db: Session,
) -> ProjectRuntimeActionResponse:
    service = ProjectService(db=db, settings=get_settings())
    try:
        project = service.get_project(project_id)
        if action == "start":
            runtime = service.runtime_service.start(project=project)
            message = "project_runtime_started"
        elif action == "stop":
            runtime = service.runtime_service.stop(project=project)
            message = "project_runtime_stopped"
        else:
            runtime = service.runtime_service.restart(project=project)
            message = "project_runtime_restarted"
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project_not_found") from exc
    except ValueError as exc:
        detail = str(exc)
        status_code = (
            status.HTTP_409_CONFLICT
            if detail in {"project_is_not_web", "project_runtime_not_configured", "project_app_not_running"}
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(status_code=status_code, detail=detail) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="project_runtime_failed",
        ) from exc

    return ProjectRuntimeActionResponse(
        project_id=project.id,
        message=message,
        runtime=service.serialize_project(project).runtime,
    )
