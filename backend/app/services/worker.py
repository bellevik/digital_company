from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.agent import Agent
from app.models.common import AgentStatus, EventType, MemoryType, TaskRunStatus, TaskStatus
from app.models.memory import Memory
from app.models.task import Task
from app.models.task_event import TaskEvent
from app.models.task_run import TaskRun
from app.repositories.task_repository import TaskClaimConflictError, claim_task
from app.schemas.worker import WorkerCycleResponse, WorkerExecutionPayload
from app.services.execution import ExecutionAdapter, ExecutionResult
from app.services.prompting import get_role_profile, build_prompt


@dataclass(slots=True)
class ClaimedTaskContext:
    task: Task
    prompt: str
    run: TaskRun


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

        execution_result = self._execute_prompt(prompt=claimed_context.prompt)
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
                    memories=self._recent_memories(task=task),
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
                return ClaimedTaskContext(task=task, prompt=prompt, run=run)
            except TaskClaimConflictError:
                self._db.rollback()

        return None

    def _recent_memories(self, *, task: Task) -> list[Memory]:
        query = select(Memory).order_by(Memory.created_at.desc()).limit(self._settings.worker_memory_window)
        if task.project_id is not None:
            query = (
                select(Memory)
                .join(Task, Memory.source_task_id == Task.id, isouter=True)
                .where((Task.project_id == task.project_id) | (Memory.source_task_id.is_(None)))
                .order_by(Memory.created_at.desc())
                .limit(self._settings.worker_memory_window)
            )
        return list(self._db.scalars(query).all())

    def _execute_prompt(self, *, prompt: str) -> ExecutionResult:
        try:
            return self._execution_adapter.run(prompt=prompt)
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
                memory = Memory(
                    type=MemoryType.TASK_RESULT,
                    summary=payload.memory_summary or payload.summary,
                    content=payload.memory_content or payload.summary,
                    source_task_id=task.id,
                )
                self._db.add(memory)
                self._db.flush()
                memory_id = memory.id
                self._db.add(
                    TaskEvent(
                        task_id=task.id,
                        agent_id=agent.id,
                        event_type=EventType.MEMORY_CREATED,
                        payload={"memory_id": str(memory.id)},
                    )
                )

            for follow_up in payload.follow_up_tasks:
                next_task = Task(
                    title=follow_up.title,
                    description=follow_up.description,
                    type=follow_up.type,
                    project_id=follow_up.project_id or task.project_id,
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
        self._db.add(
            TaskEvent(
                task_id=task.id,
                agent_id=agent.id,
                event_type=EventType.TASK_UPDATED,
                payload={
                    "action": "execution_finished",
                    "task_status": task.status.value,
                    "run_status": run.status.value,
                    "follow_up_tasks": [str(task_id) for task_id in follow_up_task_ids],
                },
            )
        )
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
    for index, char in enumerate(candidate):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(candidate[index:])
        except json.JSONDecodeError:
            continue
        return WorkerExecutionPayload.model_validate(parsed)

    return WorkerExecutionPayload(
        summary="Execution completed without structured JSON output.",
        memory_summary="Unstructured execution output",
        memory_content=raw_output,
        follow_up_tasks=[],
    )
