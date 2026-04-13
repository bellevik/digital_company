from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.common import ApprovalStatus, ReviewDecisionType
from app.schemas.task_run import TaskRunRead


class SubmitForReviewRequest(BaseModel):
    branch_name: str
    submission_notes: str | None = None


class ReviewDecisionCreate(BaseModel):
    reviewer_name: str
    decision: ReviewDecisionType
    summary: str


class ReviewDecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    task_workflow_id: uuid.UUID
    task_run_id: uuid.UUID | None
    reviewer_name: str
    decision: ReviewDecisionType
    summary: str
    created_at: datetime
    updated_at: datetime


class TaskWorkflowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    latest_task_run_id: uuid.UUID | None
    approval_status: ApprovalStatus
    branch_name: str | None
    submission_notes: str | None
    submitted_for_review_at: datetime | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    latest_task_run: TaskRunRead | None = None
    review_decisions: list[ReviewDecisionRead] = []
