from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import AgentRole, AgentStatus


class AgentCreate(BaseModel):
    name: str
    role: AgentRole
    template_id: str | None = None
    instructions: str | None = None
    skill_ids: list[str] = Field(default_factory=list)


class AgentTemplateRead(BaseModel):
    id: str
    role: AgentRole
    name: str
    summary: str
    instructions: str
    is_default: bool


class AgentSkillRead(BaseModel):
    id: str
    name: str
    summary: str
    instructions: str
    path: str
    source: str
    recommended_roles: list[AgentRole]


class AgentCatalogRead(BaseModel):
    templates: list[AgentTemplateRead]
    skills: list[AgentSkillRead]


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    role: AgentRole
    template_id: str | None
    instructions: str | None
    skill_ids: list[str]
    status: AgentStatus
    current_task_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
