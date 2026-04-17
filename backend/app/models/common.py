from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"


class TaskType(str, enum.Enum):
    IDEA = "idea"
    FEATURE = "feature"
    BUGFIX = "bugfix"
    RESEARCH = "research"
    REVIEW = "review"
    OPS = "ops"


class AgentRole(str, enum.Enum):
    PLANNER = "planner"
    DESIGNER = "designer"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    TESTER = "tester"
    REVIEWER = "reviewer"
    REVIEW_AGENT = "review_agent"


class AgentStatus(str, enum.Enum):
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"


class MemoryType(str, enum.Enum):
    CONVERSATION = "conversation"
    DECISION = "decision"
    TASK_RESULT = "task_result"
    NOTE = "note"


class EventType(str, enum.Enum):
    TASK_CREATED = "task_created"
    TASK_CLAIMED = "task_claimed"
    TASK_UPDATED = "task_updated"
    AGENT_CREATED = "agent_created"
    MEMORY_CREATED = "memory_created"
    PLAN_UPDATED = "plan_updated"


class TaskRunStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ApprovalStatus(str, enum.Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending_approval"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class ReviewDecisionType(str, enum.Enum):
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class SelfImprovementRunStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class SelfImprovementTriggerMode(str, enum.Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    SEEDED = "seeded"


class ProjectPlanStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    COMPLETED = "completed"


class ProjectPlanTaskStatus(str, enum.Enum):
    PROPOSED = "proposed"
    QUEUED = "queued"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


def enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_cls]


def uuid_primary_key() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
