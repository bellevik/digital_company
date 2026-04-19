from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status
import httpx

from app.config import get_settings
from app.services.project_runtime import ProjectRuntimeService

router = APIRouter(tags=["project-apps"])

_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "host",
}


@router.api_route("/project-apps/{project_id}", methods=["GET", "HEAD"])
@router.api_route(
    "/project-apps/{project_id}/{path:path}",
    methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def proxy_project_app(project_id: str, request: Request, path: str = "") -> Response:
    runtime_service = ProjectRuntimeService(settings=get_settings())
    try:
        target_root = runtime_service.proxy_target(project_id=project_id)
    except ValueError as exc:
        detail = str(exc)
        status_code = (
            status.HTTP_409_CONFLICT
            if detail in {"project_is_not_web", "project_app_not_running"}
            else status.HTTP_404_NOT_FOUND
        )
        raise HTTPException(status_code=status_code, detail=detail) from exc

    target_url = f"{target_root}/{path}".rstrip("/")
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in _HOP_BY_HOP_HEADERS
    }
    body = await request.body()
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        upstream = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
        )

    response_headers = {
        key: value
        for key, value in upstream.headers.items()
        if key.lower() not in _HOP_BY_HOP_HEADERS
    }
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )
