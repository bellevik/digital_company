from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import db_session_dependency, execution_adapter_dependency
from app.config import get_settings
from app.models.agent import Agent
from app.models.common import AgentStatus, EventType
from app.models.task_event import TaskEvent
from app.schemas.agent import AgentCreate, AgentRead
from app.schemas.worker import WorkerCycleResponse
from app.services.execution import ExecutionAdapter
from app.services.worker import WorkerService

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentRead])
def list_agents(db: Session = Depends(db_session_dependency)) -> list[Agent]:
    return list(db.scalars(select(Agent).order_by(Agent.created_at.desc())).all())


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
def create_agent(payload: AgentCreate, db: Session = Depends(db_session_dependency)) -> Agent:
    agent = Agent(name=payload.name, role=payload.role, status=AgentStatus.IDLE)
    db.add(agent)
    db.flush()
    db.add(
        TaskEvent(
            agent_id=agent.id,
            event_type=EventType.AGENT_CREATED,
            payload={"name": agent.name, "role": agent.role.value},
        )
    )
    db.commit()
    db.refresh(agent)
    return agent


@router.post("/{agent_id}/work", response_model=WorkerCycleResponse)
def run_agent_once(
    agent_id: uuid.UUID,
    db: Session = Depends(db_session_dependency),
    execution_adapter: ExecutionAdapter = Depends(execution_adapter_dependency),
) -> WorkerCycleResponse:
    service = WorkerService(
        db=db,
        execution_adapter=execution_adapter,
        settings=get_settings(),
    )
    try:
        return service.run_agent_once(agent_id=agent_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found") from exc
