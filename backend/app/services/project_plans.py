from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.common import EventType, ProjectPlanStatus, ProjectPlanTaskStatus, TaskStatus, TaskType
from app.models.project_plan import ProjectPlan, ProjectPlanTask
from app.models.task import Task
from app.models.task_event import TaskEvent
from app.schemas.project_plan import IdeaPitchRequest
from app.schemas.worker import WorkerExecutionPayload, WorkerFollowUpTask
from app.services.projects import ProjectService


class ProjectPlanService:
    def __init__(self, *, db: Session, project_service: ProjectService):
        self._db = db
        self._project_service = project_service

    def list_plans(self, *, project_id: str | None = None) -> list[ProjectPlan]:
        query = select(ProjectPlan).order_by(ProjectPlan.created_at.desc())
        if project_id is not None:
            query = query.where(ProjectPlan.project_id == project_id)
        return list(self._db.scalars(query).all())

    def get_plan(self, plan_id: uuid.UUID) -> ProjectPlan | None:
        return self._db.get(ProjectPlan, plan_id)

    def latest_plan_for_project(self, project_id: str) -> ProjectPlan | None:
        return self._db.scalar(
            select(ProjectPlan)
            .where(ProjectPlan.project_id == project_id)
            .order_by(ProjectPlan.created_at.desc())
            .limit(1)
        )

    def latest_approved_plan_for_project(self, project_id: str) -> ProjectPlan | None:
        return self._db.scalar(
            select(ProjectPlan)
            .where(
                ProjectPlan.project_id == project_id,
                ProjectPlan.status.in_([ProjectPlanStatus.APPROVED, ProjectPlanStatus.COMPLETED]),
            )
            .order_by(ProjectPlan.approved_at.desc().nullslast(), ProjectPlan.created_at.desc())
            .limit(1)
        )

    def pitch_idea(self, *, project_id: str, payload: IdeaPitchRequest) -> ProjectPlan:
        project = self._project_service.require_project(project_id)
        if project is None:
            raise LookupError("project_not_found")

        task = Task(
            title=payload.idea_title.strip(),
            description=payload.idea_description.strip(),
            type=TaskType.IDEA,
            project_id=project,
        )
        self._db.add(task)
        self._db.flush()
        self._db.add(
            TaskEvent(
                task_id=task.id,
                event_type=EventType.TASK_CREATED,
                payload={"title": task.title, "type": task.type.value},
            )
        )

        plan = ProjectPlan(
            project_id=project,
            planning_task_id=task.id,
            idea_title=payload.idea_title.strip(),
            idea_description=payload.idea_description.strip(),
            status=ProjectPlanStatus.DRAFT,
            max_total_tasks=0,
            created_task_count=0,
        )
        self._db.add(plan)
        self._db.flush()
        task.plan_id = plan.id
        self._db.add(
            TaskEvent(
                task_id=task.id,
                event_type=EventType.PLAN_UPDATED,
                payload={"action": "idea_pitched", "plan_id": str(plan.id)},
            )
        )
        self._db.commit()
        self._db.refresh(plan)
        return plan

    def replace_plan_from_idea_task(self, *, task: Task, payload: WorkerExecutionPayload) -> ProjectPlan:
        if task.project_id is None or task.plan_id is None:
            raise LookupError("idea_task_missing_plan")

        plan = self._db.get(ProjectPlan, task.plan_id)
        if plan is None:
            raise LookupError("plan_not_found")

        plan.idea_title = task.title
        plan.idea_description = task.description
        plan.planner_summary = payload.plan_summary or payload.summary
        plan.status = ProjectPlanStatus.PENDING_APPROVAL
        plan.feedback = None
        plan.completed_at = None
        plan.max_total_tasks = max(
            payload.max_total_tasks or len(payload.planned_tasks),
            len(payload.planned_tasks),
        )
        for item in list(plan.items):
            self._db.delete(item)
        self._db.flush()

        for index, item in enumerate(payload.planned_tasks, start=1):
            self._db.add(
                ProjectPlanTask(
                    project_plan_id=plan.id,
                    sequence=index,
                    title=item.title,
                    description=item.description,
                    type=item.type,
                    spawn_budget=max(item.spawn_budget, 0),
                    status=ProjectPlanTaskStatus.PROPOSED,
                )
            )

        self._db.add(
            TaskEvent(
                task_id=task.id,
                event_type=EventType.PLAN_UPDATED,
                payload={
                    "action": "plan_generated",
                    "plan_id": str(plan.id),
                    "planned_tasks": len(payload.planned_tasks),
                    "max_total_tasks": plan.max_total_tasks,
                },
            )
        )
        self._db.flush()
        self._db.commit()
        self._db.refresh(plan)
        return plan

    def approve_plan(self, *, plan_id: uuid.UUID) -> ProjectPlan:
        plan = self._db.get(ProjectPlan, plan_id)
        if plan is None:
            raise LookupError("plan_not_found")
        if not plan.items:
            raise ValueError("plan_has_no_tasks")

        next_count = 0
        for item in plan.items:
            if item.created_task_id is not None:
                continue
            task = Task(
                title=item.title,
                description=item.description,
                type=item.type,
                project_id=plan.project_id,
                plan_id=plan.id,
                plan_item_id=item.id,
            )
            self._db.add(task)
            self._db.flush()
            item.created_task_id = task.id
            item.status = ProjectPlanTaskStatus.QUEUED
            next_count += 1
            self._db.add(
                TaskEvent(
                    task_id=task.id,
                    event_type=EventType.TASK_CREATED,
                    payload={
                        "title": task.title,
                        "type": task.type.value,
                        "plan_id": str(plan.id),
                    },
                )
            )

        plan.created_task_count += next_count
        plan.status = ProjectPlanStatus.APPROVED
        plan.approved_at = datetime.now(timezone.utc)
        if plan.planning_task_id is not None:
            planning_task = self._db.get(Task, plan.planning_task_id)
            if planning_task is not None:
                self._db.add(
                    TaskEvent(
                        task_id=planning_task.id,
                        event_type=EventType.PLAN_UPDATED,
                        payload={"action": "plan_approved", "plan_id": str(plan.id)},
                    )
                )
        self._db.commit()
        self._db.refresh(plan)
        return plan

    def request_changes(self, *, plan_id: uuid.UUID, feedback: str) -> ProjectPlan:
        plan = self._db.get(ProjectPlan, plan_id)
        if plan is None:
            raise LookupError("plan_not_found")

        plan.status = ProjectPlanStatus.CHANGES_REQUESTED
        plan.feedback = feedback.strip()
        if plan.planning_task_id is not None:
            planning_task = self._db.get(Task, plan.planning_task_id)
            if planning_task is not None:
                planning_task.status = TaskStatus.TODO
                planning_task.completed_at = None
                planning_task.assigned_agent_id = None
                self._db.add(
                    TaskEvent(
                        task_id=planning_task.id,
                        event_type=EventType.PLAN_UPDATED,
                        payload={
                            "action": "plan_changes_requested",
                            "plan_id": str(plan.id),
                            "feedback": plan.feedback,
                        },
                    )
                )
        self._db.commit()
        self._db.refresh(plan)
        return plan

    def plan_context_for_task(self, task: Task) -> str | None:
        if task.project_id is None:
            return None

        if task.type == TaskType.IDEA and task.plan_id is not None:
            plan = self._db.get(ProjectPlan, task.plan_id)
        else:
            plan = self.latest_approved_plan_for_project(task.project_id)
        if plan is None:
            return None

        lines = [
            f"Plan status: {plan.status.value}",
            f"Idea: {plan.idea_title}",
            f"Plan summary: {plan.planner_summary or 'No planner summary yet.'}",
            f"Task budget: {plan.created_task_count}/{plan.max_total_tasks}",
        ]
        if plan.feedback:
            lines.append(f"Latest human feedback: {plan.feedback}")
        if plan.items:
            lines.append("Planned tasks:")
            for item in plan.items:
                lines.append(
                    f"- [{item.status.value}] {item.title} ({item.type.value}, spawn_budget={item.spawn_budget})"
                )
        if task.type.value != "idea":
            lines.append(
                "Do not create unbounded follow-up work. Any spawned task must be strictly necessary and remain within the approved plan budget."
            )
        return "\n".join(lines)

    def create_follow_up_tasks(
        self,
        *,
        source_task: Task,
        follow_ups: list[WorkerFollowUpTask],
    ) -> list[uuid.UUID]:
        if source_task.project_id is None:
            return []
        plan = self.latest_approved_plan_for_project(source_task.project_id)
        if plan is None:
            return []
        if source_task.plan_id is not None and source_task.plan_id != plan.id:
            return []

        source_plan_task = None
        if source_task.plan_item_id is not None:
            source_plan_task = self._db.get(ProjectPlanTask, source_task.plan_item_id)
        source_budget = source_plan_task.spawn_budget if source_plan_task is not None else 0
        if source_budget <= 0 or not follow_ups:
            return []

        remaining_capacity = max(plan.max_total_tasks - plan.created_task_count, 0)
        allowed_count = min(len(follow_ups), source_budget, remaining_capacity)
        created_ids: list[uuid.UUID] = []
        if allowed_count <= 0:
            return created_ids

        next_sequence = max((item.sequence for item in plan.items), default=0) + 1
        for offset, follow_up in enumerate(follow_ups[:allowed_count], start=0):
            plan_task = ProjectPlanTask(
                project_plan_id=plan.id,
                parent_plan_task_id=source_task.plan_item_id,
                source_task_id=source_task.id,
                sequence=next_sequence + offset,
                title=follow_up.title,
                description=follow_up.description,
                type=follow_up.type,
                status=ProjectPlanTaskStatus.QUEUED,
                spawn_budget=0,
            )
            self._db.add(plan_task)
            self._db.flush()
            task = Task(
                title=follow_up.title,
                description=follow_up.description,
                type=follow_up.type,
                project_id=follow_up.project_id or source_task.project_id,
                plan_id=plan.id,
                plan_item_id=plan_task.id,
            )
            self._db.add(task)
            self._db.flush()
            plan_task.created_task_id = task.id
            created_ids.append(task.id)
            self._db.add(
                TaskEvent(
                    task_id=task.id,
                    event_type=EventType.TASK_CREATED,
                    payload={
                        "title": task.title,
                        "type": task.type.value,
                        "source_task_id": str(source_task.id),
                        "plan_id": str(plan.id),
                    },
                )
            )

        plan.created_task_count += len(created_ids)
        if source_plan_task is not None:
            source_plan_task.spawn_budget = max(source_plan_task.spawn_budget - len(created_ids), 0)
        self._update_plan_completion(plan)
        return created_ids

    def sync_task_status(self, *, task: Task) -> None:
        if task.plan_item_id is None:
            return
        plan_item = self._db.get(ProjectPlanTask, task.plan_item_id)
        if plan_item is None:
            return
        if task.status == TaskStatus.DONE:
            plan_item.status = ProjectPlanTaskStatus.DONE
        elif task.status == TaskStatus.FAILED:
            plan_item.status = ProjectPlanTaskStatus.FAILED
        else:
            plan_item.status = ProjectPlanTaskStatus.QUEUED
        plan = self._db.get(ProjectPlan, task.plan_id) if task.plan_id is not None else None
        if plan is not None:
            self._update_plan_completion(plan)

    def cancel_task_link(self, *, task: Task) -> None:
        if task.plan_item_id is None:
            return
        plan_item = self._db.get(ProjectPlanTask, task.plan_item_id)
        if plan_item is None:
            return
        plan_item.status = ProjectPlanTaskStatus.CANCELLED
        plan_item.created_task_id = None
        plan = self._db.get(ProjectPlan, task.plan_id) if task.plan_id is not None else None
        if plan is not None:
            self._update_plan_completion(plan)

    def _update_plan_completion(self, plan: ProjectPlan) -> None:
        open_statuses = {ProjectPlanTaskStatus.PROPOSED, ProjectPlanTaskStatus.QUEUED}
        if plan.status == ProjectPlanStatus.APPROVED and not any(
            item.status in open_statuses for item in plan.items
        ):
            plan.status = ProjectPlanStatus.COMPLETED
            plan.completed_at = datetime.now(timezone.utc)
