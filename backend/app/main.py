from contextlib import asynccontextmanager
from functools import partial

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.config import get_settings
from app.db.session import SessionLocal, engine
from app.models.common import SelfImprovementTriggerMode
from app.services.self_improvement import SelfImprovementService
from app.services.system_runtime import scheduler_runtime

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    async def run_scheduled_self_improvement() -> None:
        def run_sync() -> None:
            db = SessionLocal()
            try:
                service = SelfImprovementService(db=db, settings=settings)
                service.run_once(trigger_mode=SelfImprovementTriggerMode.SCHEDULED)
            finally:
                db.close()

        import asyncio

        await asyncio.to_thread(run_sync)

    if settings.scheduler_enabled:
        await scheduler_runtime.start(
            interval_seconds=settings.self_improvement_interval_seconds,
            run_once_coro=run_scheduled_self_improvement,
        )
    yield
    if settings.scheduler_enabled:
        await scheduler_runtime.stop()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "status": "ready",
        "docs": "/docs",
        "api": settings.api_v1_prefix,
        "database": engine.url.render_as_string(hide_password=True),
    }
