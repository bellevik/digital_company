from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.agent import Agent
from app.models.common import AgentStatus
from app.models.memory import Memory
from app.models.project import Project
from app.models.project_plan import ProjectPlan
from app.models.review_decision import ReviewDecision
from app.models.task import Task
from app.models.task_event import TaskEvent
from app.models.task_run import TaskRun
from app.models.task_workflow import TaskWorkflow
from app.schemas.project import (
    ProjectCreate,
    ProjectRead,
    ProjectResetResponse,
    ProjectRuntimeRead,
)
from app.services.project_runtime import ProjectRuntimeService
from app.services.project_workspace import ProjectWorkspaceService


class ProjectService:
    def __init__(self, *, db: Session, settings: Settings):
        self._db = db
        self._settings = settings
        self._workspace_service = ProjectWorkspaceService(settings=settings)
        self._runtime_service = ProjectRuntimeService(settings=settings)

    def list_projects(self) -> list[ProjectRead]:
        return [
            self.serialize_project(project)
            for project in self._db.scalars(select(Project).order_by(Project.created_at.asc())).all()
        ]

    def create_project(self, payload: ProjectCreate) -> ProjectRead:
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
        self._runtime_service.bootstrap_project(project=project, requested_type=payload.project_type)
        return self.serialize_project(project)

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

    def get_project(self, project_id: str) -> Project:
        normalized_project_id = self._workspace_service.normalize_project_id(project_id)
        if normalized_project_id is None:
            raise LookupError("project_not_found")
        project = self._db.get(Project, normalized_project_id)
        if project is None:
            raise LookupError("project_not_found")
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

    def reset_project(self, project_id: str) -> ProjectResetResponse:
        normalized_project_id = self._workspace_service.normalize_project_id(project_id)
        if normalized_project_id is None:
            raise LookupError("project_not_found")

        project = self._db.get(Project, normalized_project_id)
        if project is None:
            raise LookupError("project_not_found")

        runtime = self._runtime_service.describe_project(project_id=project.id)
        if runtime.project_type == "web" and runtime.runtime_status == "running":
            self._runtime_service.stop(project=project)

        deleted_plan_count = self._db.scalar(
            select(func.count()).select_from(ProjectPlan).where(ProjectPlan.project_id == project.id)
        ) or 0

        from app.services.project_plans import ProjectPlanService

        plan_service = ProjectPlanService(db=self._db, project_service=self)
        tasks = list(
            self._db.scalars(select(Task).where(Task.project_id == project.id)).all()
        )
        deleted_task_count = 0
        deleted_memory_count = 0

        for task in tasks:
            agent_query = select(Agent).where(Agent.current_task_id == task.id)
            if task.assigned_agent_id is not None:
                agent_query = select(Agent).where(
                    (Agent.current_task_id == task.id) | (Agent.id == task.assigned_agent_id)
                )
            for agent in self._db.scalars(agent_query).all():
                if agent.current_task_id == task.id:
                    agent.current_task_id = None
                if agent.status == AgentStatus.BUSY:
                    agent.status = AgentStatus.IDLE

            for memory in self._db.scalars(
                select(Memory).where(Memory.source_task_id == task.id)
            ).all():
                self._db.delete(memory)
                deleted_memory_count += 1

            for review_decision in self._db.scalars(
                select(ReviewDecision).where(ReviewDecision.task_id == task.id)
            ).all():
                self._db.delete(review_decision)
            for workflow in self._db.scalars(
                select(TaskWorkflow).where(TaskWorkflow.task_id == task.id)
            ).all():
                self._db.delete(workflow)
            for task_run in self._db.scalars(
                select(TaskRun).where(TaskRun.task_id == task.id)
            ).all():
                self._db.delete(task_run)
            for task_event in self._db.scalars(
                select(TaskEvent).where(TaskEvent.task_id == task.id)
            ).all():
                self._db.delete(task_event)

            plan_service.cancel_task_link(task=task)
            self._db.delete(task)
            deleted_task_count += 1

        self._db.delete(project)
        self._db.commit()
        self._workspace_service.delete_project_directory(project.id)

        return ProjectResetResponse(
            project_id=project.id,
            message="project_reset",
            deleted_task_count=deleted_task_count,
            deleted_memory_count=deleted_memory_count,
            deleted_plan_count=deleted_plan_count,
        )

    def serialize_project(self, project: Project) -> ProjectRead:
        runtime = self._runtime_service.bootstrap_project(project=project)
        return ProjectRead(
            id=project.id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
            runtime=ProjectRuntimeRead(
                project_type=runtime.project_type,
                framework=runtime.framework,
                runtime_status=runtime.runtime_status,
                port=runtime.port,
                pid=runtime.pid,
                proxy_path=runtime.proxy_path,
                local_url=runtime.local_url,
                log_path=runtime.log_path,
                scripts=runtime.scripts,
            ),
        )

    @property
    def runtime_service(self) -> ProjectRuntimeService:
        return self._runtime_service


def _default_project_name(project_id: str) -> str:
    return project_id.replace("-", " ").replace("_", " ").strip().title()
