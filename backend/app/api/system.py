from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["system"])


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/meta")
def metadata() -> dict[str, str]:
    settings = get_settings()
    return {
        "name": settings.app_name,
        "environment": settings.app_env,
        "api_prefix": settings.api_v1_prefix,
        "scheduler_enabled": str(settings.scheduler_enabled).lower(),
    }
