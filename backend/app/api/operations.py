from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session_dependency
from app.config import get_settings
from app.schemas.self_improvement import SeedDemoResponse, SelfImprovementRunRead, SystemSummary
from app.services.self_improvement import SelfImprovementService
from app.services.system_runtime import scheduler_runtime
from app.models.common import SelfImprovementTriggerMode

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/summary", response_model=SystemSummary)
def system_summary(db: Session = Depends(db_session_dependency)) -> SystemSummary:
    settings = get_settings()
    return SelfImprovementService(db=db, settings=settings).build_summary(
        scheduler_enabled=settings.scheduler_enabled,
        scheduler_running=scheduler_runtime.state.running,
    )


@router.get("/self-improvement/runs", response_model=list[SelfImprovementRunRead])
def list_self_improvement_runs(
    db: Session = Depends(db_session_dependency),
) -> list[SelfImprovementRunRead]:
    return SelfImprovementService(db=db, settings=get_settings()).list_runs()


@router.post("/self-improvement/run", response_model=SelfImprovementRunRead)
def trigger_self_improvement_run(
    db: Session = Depends(db_session_dependency),
) -> SelfImprovementRunRead:
    return SelfImprovementService(db=db, settings=get_settings()).run_once(
        trigger_mode=SelfImprovementTriggerMode.MANUAL
    )


@router.post("/seed-demo", response_model=SeedDemoResponse)
def seed_demo_data(db: Session = Depends(db_session_dependency)) -> SeedDemoResponse:
    return SelfImprovementService(db=db, settings=get_settings()).seed_demo()
