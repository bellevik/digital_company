from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import db_session_dependency, execution_adapter_dependency
from app.config import get_settings
from app.models.agent import Agent
from app.models.common import AgentStatus, EventType
from app.models.task_event import TaskEvent
from app.schemas.agent import (
    AgentCatalogRead,
    AgentCreate,
    AgentRead,
    AgentSkillRead,
    AgentTemplateRead,
)
from app.schemas.worker import WorkerCycleResponse
from app.schemas.worker import WorkerBatchResponse
from app.services.agent_catalog import (
    default_template_id_for_role,
    list_agent_skills,
    list_agent_templates,
    resolve_agent_skills,
    resolve_agent_template,
)
from app.services.execution import ExecutionAdapter
from app.services.worker import WorkerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/catalog", response_model=AgentCatalogRead)
def get_agent_catalog() -> AgentCatalogRead:
    settings = get_settings()
    return AgentCatalogRead(
        templates=[
            AgentTemplateRead(
                id=template.id,
                role=template.role,
                name=template.name,
                summary=template.summary,
                instructions=template.instructions,
                is_default=template.is_default,
            )
            for template in list_agent_templates()
        ],
        skills=[
            AgentSkillRead(
                id=skill.id,
                name=skill.name,
                summary=skill.summary,
                instructions=skill.instructions,
                path=str(skill.path),
                source=skill.source,
                recommended_roles=list(skill.recommended_roles),
            )
            for skill in list_agent_skills(repo_root=settings.repo_root)
        ],
    )


@router.get("", response_model=list[AgentRead])
def list_agents(db: Session = Depends(db_session_dependency)) -> list[Agent]:
    return list(db.scalars(select(Agent).order_by(Agent.created_at.desc())).all())


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
def create_agent(payload: AgentCreate, db: Session = Depends(db_session_dependency)) -> Agent:
    settings = get_settings()
    try:
        template = resolve_agent_template(role=payload.role, template_id=payload.template_id)
        skills = resolve_agent_skills(payload.skill_ids, repo_root=settings.repo_root)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    instructions = payload.instructions.strip() if payload.instructions else None
    if instructions == "":
        instructions = None

    agent = Agent(
        name=payload.name,
        role=payload.role,
        template_id=template.id,
        instructions=instructions,
        skill_ids=[skill.id for skill in skills],
        status=AgentStatus.IDLE,
    )
    db.add(agent)
    db.flush()
    db.add(
        TaskEvent(
            agent_id=agent.id,
            event_type=EventType.AGENT_CREATED,
            payload={
                "name": agent.name,
                "role": agent.role.value,
                "template_id": agent.template_id or default_template_id_for_role(agent.role),
                "skill_ids": agent.skill_ids,
            },
        )
    )
    db.commit()
    db.refresh(agent)
    return agent


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_agent(agent_id: uuid.UUID, db: Session = Depends(db_session_dependency)) -> Response:
    agent = db.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    if agent.current_task_id is not None or agent.status == AgentStatus.BUSY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Busy agents cannot be deleted.",
        )
    if agent.task_runs:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Agents with execution history cannot be deleted.",
        )
    if agent.assigned_tasks:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Agents referenced by tasks cannot be deleted.",
        )

    db.delete(agent)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
    except Exception as exc:  # noqa: BLE001
        logger.exception("Agent work endpoint failed", extra={"agent_id": str(agent_id)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="agent_work_failed") from exc


@router.post("/run-all", response_model=WorkerBatchResponse)
def run_all_agents_once(
    db: Session = Depends(db_session_dependency),
    execution_adapter: ExecutionAdapter = Depends(execution_adapter_dependency),
) -> WorkerBatchResponse:
    service = WorkerService(
        db=db,
        execution_adapter=execution_adapter,
        settings=get_settings(),
    )
    agents = list(
        db.scalars(
            select(Agent)
            .where(Agent.status != AgentStatus.OFFLINE)
            .order_by(Agent.created_at.asc())
        ).all()
    )
    results: list[WorkerCycleResponse] = []
    completed = 0
    failed = 0
    idle = 0

    for agent in agents:
        try:
            result = service.run_agent_once(agent_id=agent.id)
        except LookupError as exc:
            logger.exception("Agent disappeared during run-all cycle", extra={"agent_id": str(agent.id)})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found") from exc
        except Exception as exc:  # noqa: BLE001
            logger.exception("Run-all endpoint failed", extra={"agent_id": str(agent.id)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="agent_work_failed") from exc

        results.append(result)
        if result.outcome == "completed":
            completed += 1
        elif result.outcome == "failed":
            failed += 1
        else:
            idle += 1

    return WorkerBatchResponse(
        total_agents=len(agents),
        completed=completed,
        failed=failed,
        idle=idle,
        results=results,
    )
