from fastapi import APIRouter

from app.api.agents import router as agents_router
from app.api.memories import router as memories_router
from app.api.system import router as system_router
from app.api.tasks import router as tasks_router

router = APIRouter()

router.include_router(system_router)
router.include_router(tasks_router)
router.include_router(agents_router)
router.include_router(memories_router)
