from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    id: str
    name: str
    description: str | None = None
    project_type: str = "web"


class ProjectRuntimeRead(BaseModel):
    project_type: str
    framework: str | None
    runtime_status: str
    port: int | None
    pid: int | None
    proxy_path: str | None
    local_url: str | None
    log_path: str | None
    scripts: dict[str, str | None]


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    runtime: ProjectRuntimeRead


class ProjectRuntimeActionResponse(BaseModel):
    project_id: str
    message: str
    runtime: ProjectRuntimeRead


class ProjectResetResponse(BaseModel):
    project_id: str
    message: str
    deleted_task_count: int
    deleted_memory_count: int
    deleted_plan_count: int
