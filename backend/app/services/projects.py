from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.project import Project
from app.models.task import Task
from app.schemas.project import ProjectCreate
from app.services.project_workspace import ProjectWorkspaceService


class ProjectService:
    def __init__(self, *, db: Session, settings: Settings):
        self._db = db
        self._workspace_service = ProjectWorkspaceService(settings=settings)

    def list_projects(self) -> list[Project]:
        return list(self._db.scalars(select(Project).order_by(Project.created_at.asc())).all())

    def create_project(self, payload: ProjectCreate) -> Project:
        project_id = self._workspace_service.normalize_project_id(payload.id)
        if project_id is None:
            raise ValueError("project id is required")

        if self._db.get(Project, project_id) is not None:
            raise ValueError("project already exists")

        name = payload.name.strip()
        if not name:
            raise ValueError("project name is required")
        if self._db.scalar(select(Project).where(Project.name == name)) is not None:
            raise ValueError("project name already exists")

        project = Project(
            id=project_id,
            name=name,
            description=payload.description.strip() if payload.description else None,
        )
        self._db.add(project)
        self._workspace_service.ensure_project_directory(project.id)
        self._db.commit()
        self._db.refresh(project)
        return project

    def require_project(self, project_id: str | None) -> str | None:
        normalized_project_id = self._workspace_service.normalize_project_id(project_id)
        if normalized_project_id is None:
            return None
        project = self._db.get(Project, normalized_project_id)
        if project is None:
            raise LookupError("project_not_found")
        return project.id

    def get_or_create_project(
        self,
        *,
        project_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> Project:
        normalized_project_id = self._workspace_service.normalize_project_id(project_id)
        if normalized_project_id is None:
            raise ValueError("project id is required")

        project = self._db.get(Project, normalized_project_id)
        if project is not None:
            self._workspace_service.ensure_project_directory(project.id)
            return project

        project = Project(
            id=normalized_project_id,
            name=(name or _default_project_name(normalized_project_id)).strip(),
            description=description.strip() if description else None,
        )
        self._db.add(project)
        self._db.flush()
        self._workspace_service.ensure_project_directory(project.id)
        return project

    def delete_project(self, project_id: str) -> None:
        normalized_project_id = self._workspace_service.normalize_project_id(project_id)
        if normalized_project_id is None:
            raise LookupError("project_not_found")

        project = self._db.get(Project, normalized_project_id)
        if project is None:
            raise LookupError("project_not_found")

        task_count = self._db.scalar(
            select(func.count()).select_from(Task).where(Task.project_id == project.id)
        ) or 0
        if task_count > 0:
            raise ValueError("project_has_tasks")

        if self._workspace_service.has_workspace_artifacts(project.id):
            raise ValueError("project_has_files")

        self._db.delete(project)
        self._db.commit()
        self._workspace_service.delete_project_directory(project.id)


def _default_project_name(project_id: str) -> str:
    return project_id.replace("-", " ").replace("_", " ").strip().title()
