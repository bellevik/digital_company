from fastapi import APIRouter

from app.config import get_settings

router = APIRouter()


@router.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/meta", tags=["system"])
def metadata() -> dict[str, str]:
    settings = get_settings()
    return {
        "name": settings.app_name,
        "environment": settings.app_env,
        "api_prefix": settings.api_v1_prefix,
    }

