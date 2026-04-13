from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.models.common import AgentStatus, EventType, TaskStatus
from app.models.task import Task
from app.models.task_event import TaskEvent


class TaskClaimConflictError(Exception):
    pass


def claim_task(*, db: Session, task_id: uuid.UUID, agent_id: uuid.UUID) -> Task:
    agent = db.scalar(select(Agent).where(Agent.id == agent_id))
    if agent is None:
        raise LookupError("agent_not_found")

    if agent.current_task_id is not None:
        raise TaskClaimConflictError("agent_already_has_task")

    claimed_agent = db.execute(
        update(Agent)
        .where(Agent.id == agent_id, Agent.current_task_id.is_(None))
        .values(status=AgentStatus.BUSY, current_task_id=task_id)
        .returning(Agent)
    ).scalar_one_or_none()

    if claimed_agent is None:
        raise TaskClaimConflictError("agent_unavailable")

    task = db.execute(
        update(Task)
        .where(
            Task.id == task_id,
            Task.status == TaskStatus.TODO,
            Task.assigned_agent_id.is_(None),
        )
        .values(
            status=TaskStatus.IN_PROGRESS,
            assigned_agent_id=agent_id,
            updated_at=datetime.now(timezone.utc),
        )
        .returning(Task)
    ).scalar_one_or_none()

    if task is None:
        db.execute(
            update(Agent)
            .where(Agent.id == agent_id)
            .values(status=AgentStatus.IDLE, current_task_id=None)
        )
        raise TaskClaimConflictError("task_not_available")

    db.add(
        TaskEvent(
            task_id=task.id,
            agent_id=agent_id,
            event_type=EventType.TASK_CLAIMED,
            payload={"status": task.status.value},
        )
    )
    db.flush()
    return task

