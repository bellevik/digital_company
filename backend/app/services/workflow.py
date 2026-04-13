from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.common import AgentStatus, ApprovalStatus, EventType, ReviewDecisionType, TaskStatus
from app.models.review_decision import ReviewDecision
from app.models.task import Task
from app.models.task_event import TaskEvent
from app.models.task_run import TaskRun
from app.models.task_workflow import TaskWorkflow
from app.schemas.workflow import ReviewDecisionCreate, SubmitForReviewRequest


class WorkflowService:
    def __init__(self, *, db: Session):
        self._db = db

    def get_workflow(self, *, task_id: uuid.UUID) -> TaskWorkflow | None:
        return self._db.scalar(
            select(TaskWorkflow)
            .where(TaskWorkflow.task_id == task_id)
            .options(
                selectinload(TaskWorkflow.review_decisions),
                selectinload(TaskWorkflow.latest_task_run),
            )
        )

    def ensure_workflow(self, *, task: Task, latest_task_run_id: uuid.UUID | None = None) -> TaskWorkflow:
        workflow = self._db.scalar(select(TaskWorkflow).where(TaskWorkflow.task_id == task.id))
        if workflow is None:
            workflow = TaskWorkflow(task_id=task.id, latest_task_run_id=latest_task_run_id)
            self._db.add(workflow)
            self._db.flush()
        elif latest_task_run_id is not None:
            workflow.latest_task_run_id = latest_task_run_id
        return workflow

    def list_workflows(self, *, approval_status: ApprovalStatus | None = None) -> list[TaskWorkflow]:
        query = select(TaskWorkflow).options(
            selectinload(TaskWorkflow.review_decisions),
            selectinload(TaskWorkflow.latest_task_run),
        ).order_by(TaskWorkflow.updated_at.desc())
        if approval_status is not None:
            query = query.where(TaskWorkflow.approval_status == approval_status)
        return list(self._db.scalars(query).all())

    def submit_for_review(self, *, task_id: uuid.UUID, payload: SubmitForReviewRequest) -> TaskWorkflow:
        task = self._db.get(Task, task_id)
        if task is None:
            raise LookupError("task_not_found")

        latest_run = self._db.scalar(
            select(TaskRun).where(TaskRun.task_id == task.id).order_by(TaskRun.created_at.desc())
        )
        workflow = self.ensure_workflow(task=task, latest_task_run_id=latest_run.id if latest_run else None)
        workflow.branch_name = payload.branch_name
        workflow.submission_notes = payload.submission_notes
        workflow.approval_status = ApprovalStatus.PENDING
        workflow.submitted_for_review_at = datetime.now(timezone.utc)
        workflow.reviewed_at = None

        self._db.add(
            TaskEvent(
                task_id=task.id,
                event_type=EventType.TASK_UPDATED,
                payload={
                    "action": "submitted_for_review",
                    "branch_name": payload.branch_name,
                },
            )
        )
        self._db.commit()
        return self.get_workflow(task_id=task.id)  # type: ignore[return-value]

    def record_review_decision(
        self,
        *,
        task_id: uuid.UUID,
        payload: ReviewDecisionCreate,
    ) -> TaskWorkflow:
        task = self._db.get(Task, task_id)
        if task is None:
            raise LookupError("task_not_found")

        workflow = self.ensure_workflow(task=task)
        latest_run = self._db.scalar(
            select(TaskRun).where(TaskRun.task_id == task.id).order_by(TaskRun.created_at.desc())
        )
        if latest_run is not None:
            workflow.latest_task_run_id = latest_run.id

        decision = ReviewDecision(
            task_id=task.id,
            task_workflow_id=workflow.id,
            task_run_id=workflow.latest_task_run_id,
            reviewer_name=payload.reviewer_name,
            decision=payload.decision,
            summary=payload.summary,
        )
        self._db.add(decision)

        workflow.reviewed_at = datetime.now(timezone.utc)
        if payload.decision == ReviewDecisionType.APPROVED:
            workflow.approval_status = ApprovalStatus.APPROVED
        else:
            workflow.approval_status = ApprovalStatus.CHANGES_REQUESTED
            task.status = TaskStatus.TODO
            task.completed_at = None
            task.assigned_agent_id = None
            if task.assigned_agent is not None and task.assigned_agent.current_task_id == task.id:
                task.assigned_agent.current_task_id = None
                task.assigned_agent.status = AgentStatus.IDLE

        self._db.add(
            TaskEvent(
                task_id=task.id,
                event_type=EventType.TASK_UPDATED,
                payload={
                    "action": "review_decision",
                    "decision": payload.decision.value,
                    "reviewer_name": payload.reviewer_name,
                },
            )
        )
        self._db.commit()
        return self.get_workflow(task_id=task.id)  # type: ignore[return-value]
