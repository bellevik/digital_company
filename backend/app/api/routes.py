from fastapi import APIRouter

from app.api.agents import router as agents_router
from app.api.memories import router as memories_router
from app.api.operations import router as operations_router
from app.api.system import router as system_router
from app.api.task_runs import router as task_runs_router
from app.api.tasks import router as tasks_router
from app.api.workflows import router as workflows_router

router = APIRouter()

router.include_router(system_router)
router.include_router(operations_router)
router.include_router(tasks_router)
router.include_router(agents_router)
router.include_router(memories_router)
router.include_router(task_runs_router)
router.include_router(workflows_router)
