from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.agent import Agent
from app.models.common import AgentStatus, EventType, MemoryType, TaskRunStatus, TaskStatus, TaskType
from app.models.memory import Memory
from app.models.task import Task
from app.models.task_event import TaskEvent
from app.models.task_run import TaskRun
from app.repositories.task_repository import TaskClaimConflictError, claim_task
from app.schemas.worker import WorkerCycleResponse, WorkerExecutionPayload
from app.services.execution import ExecutionAdapter, ExecutionResult
from app.services.memory import MemoryService
from app.services.project_workspace import ProjectWorkspaceService
from app.services.project_plans import ProjectPlanService
from app.services.projects import ProjectService
from app.services.prompting import get_role_profile, build_prompt
from app.services.workflow import WorkflowService


@dataclass(slots=True)
class ClaimedTaskContext:
    task: Task
    prompt: str
    run: TaskRun
    workdir: Path | None


class WorkerService:
    def __init__(self, *, db: Session, execution_adapter: ExecutionAdapter, settings: Settings):
        self._db = db
        self._execution_adapter = execution_adapter
        self._settings = settings

    def run_agent_once(self, *, agent_id: uuid.UUID) -> WorkerCycleResponse:
        agent = self._db.get(Agent, agent_id)
        if agent is None:
            raise LookupError("agent_not_found")

        claimed_context = self._claim_next_task(agent=agent)
        if claimed_context is None:
            return WorkerCycleResponse(agent_id=agent.id, outcome="idle")

        execution_result = self._execute_prompt(
            prompt=claimed_context.prompt,
            workdir=claimed_context.workdir,
        )
        return self._finalize_run(
            agent_id=agent.id,
            task_id=claimed_context.task.id,
            run_id=claimed_context.run.id,
            execution_result=execution_result,
        )

    def _claim_next_task(self, *, agent: Agent) -> ClaimedTaskContext | None:
        supported_task_types = get_role_profile(agent.role).supported_task_types
        candidate_ids = list(
            self._db.scalars(
                select(Task.id)
                .where(
                    Task.status == TaskStatus.TODO,
                    Task.assigned_agent_id.is_(None),
                    Task.type.in_(supported_task_types),
                )
                .order_by(Task.created_at.asc())
                .limit(10)
            ).all()
        )

        for task_id in candidate_ids:
            try:
                task = claim_task(db=self._db, task_id=task_id, agent_id=agent.id)
                prompt = build_prompt(
                    agent=agent,
                    task=task,
                    memories=self._retrieved_memories(task=task),
                    repo_root=self._settings.resolved_codex_workdir,
                    project_workspace=self._workspace_service().codex_project_directory(task.project_id),
                    plan_context=self._plan_service().plan_context_for_task(task),
                )
                run = TaskRun(
                    task_id=task.id,
                    agent_id=agent.id,
                    status=TaskRunStatus.RUNNING,
                    prompt=prompt,
                    started_at=datetime.now(timezone.utc),
                )
                self._db.add(run)
                self._db.add(
                    TaskEvent(
                        task_id=task.id,
                        agent_id=agent.id,
                        event_type=EventType.TASK_UPDATED,
                        payload={"action": "execution_started"},
                    )
                )
                self._db.commit()
                self._db.refresh(task)
                self._db.refresh(run)
                return ClaimedTaskContext(
                    task=task,
                    prompt=prompt,
                    run=run,
                    workdir=self._workspace_service().codex_project_directory(task.project_id),
                )
            except TaskClaimConflictError:
                self._db.rollback()

        return None

    def _retrieved_memories(self, *, task: Task):
        memory_service = MemoryService(db=self._db, settings=self._settings)
        query = f"{task.title}\n{task.description}"
        return memory_service.search_memories(
            query=query,
            limit=self._settings.worker_memory_window,
            project_id=task.project_id,
            source_task_id=task.id,
            strategy="hybrid",
        )

    def _workspace_service(self) -> ProjectWorkspaceService:
        return ProjectWorkspaceService(settings=self._settings)

    def _project_service(self) -> ProjectService:
        return ProjectService(db=self._db, settings=self._settings)

    def _plan_service(self) -> ProjectPlanService:
        return ProjectPlanService(db=self._db, project_service=self._project_service())

    def _execute_prompt(self, *, prompt: str, workdir: Path | None) -> ExecutionResult:
        try:
            return self._execution_adapter.run(prompt=prompt, workdir=workdir)
        except Exception as exc:  # noqa: BLE001
            return ExecutionResult(
                stdout="",
                stderr=str(exc),
                exit_code=1,
                command=["execution-error"],
            )

    def _finalize_run(
        self,
        *,
        agent_id: uuid.UUID,
        task_id: uuid.UUID,
        run_id: uuid.UUID,
        execution_result: ExecutionResult,
    ) -> WorkerCycleResponse:
        agent = self._db.get(Agent, agent_id)
        task = self._db.get(Task, task_id)
        run = self._db.get(TaskRun, run_id)
        if agent is None or task is None or run is None:
            raise LookupError("runtime_state_missing")

        payload = _parse_worker_payload(execution_result.stdout)
        final_status = TaskRunStatus.SUCCEEDED if execution_result.exit_code == 0 else TaskRunStatus.FAILED
        if payload is not None and payload.final_status is not None:
            final_status = payload.final_status
        artifact_paths: list[str] = []
        if payload is not None:
            artifact_paths = self._validated_artifact_paths(task=task, payload=payload)
            if (
                task.type != TaskType.IDEA
                and task.project_id
                and final_status == TaskRunStatus.SUCCEEDED
                and not artifact_paths
            ):
                final_status = TaskRunStatus.FAILED
                artifact_error = (
                    f"Project task completed without creating files in projects/{task.project_id}. "
                    "Return concrete artifact_paths and ensure those files exist before reporting success."
                )
                execution_result = ExecutionResult(
                    stdout=execution_result.stdout,
                    stderr="\n".join(part for part in [execution_result.stderr, artifact_error] if part),
                    exit_code=execution_result.exit_code if execution_result.exit_code != 0 else 1,
                    command=execution_result.command,
                )

        task.status = TaskStatus.DONE if final_status == TaskRunStatus.SUCCEEDED else TaskStatus.FAILED
        task.completed_at = datetime.now(timezone.utc)
        agent.status = AgentStatus.IDLE
        agent.current_task_id = None

        run.status = final_status
        run.stdout = execution_result.stdout
        run.stderr = execution_result.stderr
        run.exit_code = execution_result.exit_code
        run.finished_at = datetime.now(timezone.utc)

        follow_up_task_ids: list[uuid.UUID] = []
        memory_id: uuid.UUID | None = None

        if payload is not None:
            run.result_payload = payload.model_dump(mode="json")
            if payload.memory_summary or payload.memory_content:
                memory = MemoryService(db=self._db, settings=self._settings).create_memory(
                    memory_type=MemoryType.TASK_RESULT,
                    summary=payload.memory_summary or payload.summary,
                    content=payload.memory_content or payload.summary,
                    source_task_id=task.id,
                )
                memory_id = memory.id
                self._db.add(
                    TaskEvent(
                        task_id=task.id,
                        agent_id=agent.id,
                        event_type=EventType.MEMORY_CREATED,
                        payload={"memory_id": str(memory.id)},
                    )
                )

            if task.type == TaskType.IDEA and final_status == TaskRunStatus.SUCCEEDED:
                self._plan_service().replace_plan_from_idea_task(task=task, payload=payload)
            elif payload.follow_up_tasks:
                if task.plan_id is not None:
                    follow_up_task_ids = self._plan_service().create_follow_up_tasks(
                        source_task=task,
                        follow_ups=payload.follow_up_tasks,
                    )
                else:
                    for follow_up in payload.follow_up_tasks:
                        project_id = self._project_service().require_project(
                            follow_up.project_id or task.project_id
                        )
                        self._workspace_service().ensure_project_directory(project_id)
                        next_task = Task(
                            title=follow_up.title,
                            description=follow_up.description,
                            type=follow_up.type,
                            project_id=project_id,
                        )
                        self._db.add(next_task)
                        self._db.flush()
                        follow_up_task_ids.append(next_task.id)
                        self._db.add(
                            TaskEvent(
                                task_id=next_task.id,
                                agent_id=agent.id,
                                event_type=EventType.TASK_CREATED,
                                payload={
                                    "title": next_task.title,
                                    "type": next_task.type.value,
                                    "source_task_id": str(task.id),
                                },
                            )
                        )

        run.created_follow_up_tasks = len(follow_up_task_ids)
        self._plan_service().sync_task_status(task=task)
        self._db.add(
            TaskEvent(
                task_id=task.id,
                agent_id=agent.id,
                event_type=EventType.TASK_UPDATED,
                payload={
                    "action": "execution_finished",
                    "task_status": task.status.value,
                    "run_status": run.status.value,
                    "artifact_paths": artifact_paths,
                    "follow_up_tasks": [str(task_id) for task_id in follow_up_task_ids],
                },
            )
        )
        WorkflowService(db=self._db).ensure_workflow(task=task, latest_task_run_id=run.id)
        self._db.commit()
        self._db.refresh(run)

        return WorkerCycleResponse(
            agent_id=agent.id,
            outcome="completed" if run.status == TaskRunStatus.SUCCEEDED else "failed",
            task_id=task.id,
            task_run=run,
            memory_id=memory_id,
            follow_up_task_ids=follow_up_task_ids,
        )

    def _validated_artifact_paths(
        self,
        *,
        task: Task,
        payload: WorkerExecutionPayload,
    ) -> list[str]:
        if task.type == TaskType.IDEA:
            return []
        if task.project_id is None:
            return payload.artifact_paths

        project_directory = self._workspace_service().ensure_project_directory(task.project_id)
        if project_directory is None:
            return []

        root = project_directory.resolve()
        validated_paths: list[str] = []
        for relative_path in payload.artifact_paths:
            normalized = relative_path.strip().lstrip("/")
            if not normalized:
                continue
            candidate = (project_directory / normalized).resolve()
            if root not in candidate.parents and candidate != root:
                continue
            if candidate.is_file():
                validated_paths.append(normalized)

        if validated_paths:
            return validated_paths

        return [str(path) for path in self._workspace_service().list_workspace_artifacts(task.project_id)]


def _parse_worker_payload(raw_output: str) -> WorkerExecutionPayload | None:
    candidate = raw_output.strip()
    if not candidate:
        return None

    if candidate.startswith("```"):
        first_break = candidate.find("\n")
        last_fence = candidate.rfind("```")
        if first_break != -1 and last_fence != -1 and last_fence > first_break:
            candidate = candidate[first_break + 1 : last_fence].strip()

    decoder = json.JSONDecoder()
    saw_invalid_json_payload = False
    for index, char in enumerate(candidate):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(candidate[index:])
        except json.JSONDecodeError:
            continue
        try:
            return WorkerExecutionPayload.model_validate(parsed)
        except ValidationError:
            saw_invalid_json_payload = True
            continue

    return WorkerExecutionPayload(
        summary=(
            "Execution returned JSON that did not match the required schema."
            if saw_invalid_json_payload
            else "Execution completed without structured JSON output."
        ),
        memory_summary="Invalid execution output" if saw_invalid_json_payload else "Unstructured execution output",
        memory_content=raw_output,
        final_status=TaskRunStatus.FAILED,
        follow_up_tasks=[],
    )
