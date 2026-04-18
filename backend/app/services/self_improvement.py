from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.agent import Agent
from app.models.common import (
    ApprovalStatus,
    AgentRole,
    MemoryType,
    SelfImprovementRunStatus,
    SelfImprovementTriggerMode,
    TaskStatus,
    TaskType,
)
from app.models.memory import Memory
from app.models.self_improvement_run import SelfImprovementRun
from app.models.task import Task
from app.models.task_run import TaskRun
from app.models.task_workflow import TaskWorkflow
from app.schemas.self_improvement import SeedDemoResponse, SeedStartupTeamResponse, SystemSummary
from app.services.memory import MemoryService
from app.services.agent_catalog import resolve_agent_skills, resolve_agent_template
from app.services.project_workspace import ProjectWorkspaceService
from app.services.projects import ProjectService


class SelfImprovementService:
    def __init__(self, *, db: Session, settings: Settings):
        self._db = db
        self._settings = settings

    def build_summary(self, *, scheduler_enabled: bool, scheduler_running: bool) -> SystemSummary:
        task_counts = Counter(self._db.scalars(select(Task.status)).all())
        agent_counts = Counter(self._db.scalars(select(Agent.status)).all())
        workflows_pending = self._db.scalar(
            select(func.count()).select_from(TaskWorkflow).where(
                TaskWorkflow.approval_status == ApprovalStatus.PENDING
            )
        ) or 0
        return SystemSummary(
            tasks_total=self._count(Task),
            tasks_todo=task_counts[TaskStatus.TODO],
            tasks_in_progress=task_counts[TaskStatus.IN_PROGRESS],
            tasks_done=task_counts[TaskStatus.DONE],
            tasks_failed=task_counts[TaskStatus.FAILED],
            agents_total=self._count(Agent),
            agents_idle=agent_counts["idle"],
            agents_busy=agent_counts["busy"],
            agents_offline=agent_counts["offline"],
            workflows_pending=workflows_pending,
            memories_total=self._count(Memory),
            task_runs_total=self._count(TaskRun),
            self_improvement_runs_total=self._count(SelfImprovementRun),
            scheduler_enabled=scheduler_enabled,
            scheduler_running=scheduler_running,
        )

    def _workspace_service(self) -> ProjectWorkspaceService:
        return ProjectWorkspaceService(settings=self._settings)

    def _project_service(self) -> ProjectService:
        return ProjectService(db=self._db, settings=self._settings)

    def list_runs(self) -> list[SelfImprovementRun]:
        return list(
            self._db.scalars(
                select(SelfImprovementRun).order_by(SelfImprovementRun.started_at.desc())
            ).all()
        )

    def run_once(self, *, trigger_mode: SelfImprovementTriggerMode) -> SelfImprovementRun:
        started_at = datetime.now(timezone.utc)
        stamp = started_at.strftime("%Y%m%d-%H%M%S")
        run = SelfImprovementRun(
            status=SelfImprovementRunStatus.RUNNING,
            trigger_mode=trigger_mode,
            summary="Analyzing current system state.",
            proposed_branch_name=f"{self._settings.self_improvement_branch_prefix}-{stamp}",
            proposed_pr_title=f"Self-improvement cycle {stamp}",
            started_at=started_at,
        )
        self._db.add(run)
        self._db.flush()

        suggestions = self._collect_suggestions()
        created_task_ids: list[str] = []
        for suggestion in suggestions:
            existing_open = self._db.scalar(
                select(Task).where(
                    Task.title == suggestion["title"],
                    Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
                )
            )
            if existing_open is not None:
                continue
            project = self._project_service().get_or_create_project(
                project_id=suggestion["project_id"],
            )
            task = Task(
                title=suggestion["title"],
                description=suggestion["description"],
                type=suggestion["type"],
                project_id=project.id,
            )
            self._db.add(task)
            self._db.flush()
            created_task_ids.append(str(task.id))

        run.status = SelfImprovementRunStatus.SUCCEEDED
        run.created_task_count = len(created_task_ids)
        run.summary = (
            f"Created {len(created_task_ids)} improvement task(s)."
            if created_task_ids
            else "No new improvement tasks were necessary."
        )
        run.payload = {
            "suggestions_considered": suggestions,
            "created_task_ids": created_task_ids,
        }
        run.finished_at = datetime.now(timezone.utc)
        self._db.commit()
        self._db.refresh(run)
        return run

    def seed_demo(self) -> SeedDemoResponse:
        created_agents = 0
        created_tasks = 0
        created_memories = 0
        workspace_service = self._workspace_service()
        workspace_service.ensure_root()

        if self._count(Agent) == 0:
            for name, role in [
                ("planner-1", AgentRole.PLANNER),
                ("arch-1", AgentRole.ARCHITECT),
                ("dev-1", AgentRole.DEVELOPER),
                ("tester-1", AgentRole.TESTER),
                ("reviewer-1", AgentRole.REVIEWER),
            ]:
                self._db.add(
                    Agent(
                        name=name,
                        role=role,
                        template_id=default_template_id_for_role(role),
                        skill_ids=[],
                    )
                )
                created_agents += 1
            self._db.flush()

        if self._count(Task) == 0:
            demo_tasks = [
                (
                    "Design deployment runbook",
                    "Create a concise deployment and operations runbook for the Digital Company stack.",
                    TaskType.OPS,
                    "platform",
                ),
                (
                    "Review worker prompts",
                    "Audit role prompts and tighten the task output contract where it is ambiguous.",
                    TaskType.REVIEW,
                    "platform",
                ),
                (
                    "Implement product onboarding",
                    "Create the first-run onboarding flow for a new operator.",
                    TaskType.FEATURE,
                    "operator",
                ),
            ]
            for title, description, task_type, project_id in demo_tasks:
                project = self._project_service().get_or_create_project(project_id=project_id)
                self._db.add(
                    Task(
                        title=title,
                        description=description,
                        type=task_type,
                        project_id=project.id,
                    )
                )
                created_tasks += 1
            self._db.flush()

        if self._count(Memory) == 0:
            memory = MemoryService(db=self._db, settings=self._settings).create_memory(
                memory_type=MemoryType.DECISION,
                summary="System starts local-first",
                content="The product is designed to run locally with explicit human approval gates.",
                source_task_id=None,
            )
            if memory.id:
                created_memories += 1

        self._db.commit()
        return SeedDemoResponse(
            created_agents=created_agents,
            created_tasks=created_tasks,
            created_memories=created_memories,
            message="Demo data seeded.",
        )

    def seed_startup_team(self) -> SeedStartupTeamResponse:
        created_names: list[str] = []
        existing_agents = 0

        for blueprint in _startup_team_blueprint():
            existing = self._db.scalar(select(Agent).where(Agent.name == blueprint["name"]))
            if existing is not None:
                existing_agents += 1
                continue

            template = resolve_agent_template(
                role=blueprint["role"],
                template_id=blueprint["template_id"],
            )
            skills = resolve_agent_skills(
                blueprint["skill_ids"],
                repo_root=self._settings.repo_root,
            )
            self._db.add(
                Agent(
                    name=blueprint["name"],
                    role=blueprint["role"],
                    template_id=template.id,
                    instructions=blueprint["instructions"],
                    skill_ids=[skill.id for skill in skills],
                )
            )
            created_names.append(blueprint["name"])

        self._db.commit()
        return SeedStartupTeamResponse(
            created_agents=len(created_names),
            existing_agents=existing_agents,
            created_names=created_names,
            message="Startup team seeded.",
        )

    def _collect_suggestions(self) -> list[dict]:
        suggestions: list[dict] = []

        failed_tasks = list(
            self._db.scalars(select(Task).where(Task.status == TaskStatus.FAILED)).all()
        )
        if failed_tasks:
            suggestions.append(
                {
                    "title": "Investigate failed task executions",
                    "description": (
                        f"Audit {len(failed_tasks)} failed task(s) and tighten execution handling."
                    ),
                    "type": TaskType.OPS,
                    "project_id": "platform",
                }
            )

        done_without_review = list(
            self._db.scalars(
                select(Task)
                .join(TaskWorkflow, TaskWorkflow.task_id == Task.id, isouter=True)
                .where(
                    Task.status == TaskStatus.DONE,
                    (
                        (TaskWorkflow.id.is_(None))
                        | (TaskWorkflow.approval_status == ApprovalStatus.NOT_REQUIRED)
                        | (TaskWorkflow.approval_status == ApprovalStatus.CHANGES_REQUESTED)
                    ),
                )
            ).all()
        )
        if done_without_review:
            suggestions.append(
                {
                    "title": "Review completed work awaiting approval",
                    "description": (
                        f"Submit or re-review {len(done_without_review)} completed task(s) still outside the approval gate."
                    ),
                    "type": TaskType.REVIEW,
                    "project_id": "platform",
                }
            )

        if self._count(Agent) < 3:
            suggestions.append(
                {
                    "title": "Expand baseline agent coverage",
                    "description": "Add missing baseline agents so design, development, testing, and review can run in sequence.",
                    "type": TaskType.OPS,
                    "project_id": "platform",
                }
            )

        if self._count(Memory) < 5:
            suggestions.append(
                {
                    "title": "Capture more durable decisions",
                    "description": "Create durable memory entries for architecture, workflow, and deployment decisions.",
                    "type": TaskType.RESEARCH,
                    "project_id": "platform",
                }
            )

        return suggestions

    def _count(self, model) -> int:
        return self._db.scalar(select(func.count()).select_from(model)) or 0


def _startup_team_blueprint() -> list[dict]:
    return [
        {
            "name": "RoadmapPlanner",
            "role": AgentRole.PLANNER,
            "template_id": "planner_delivery_strategist",
            "skill_ids": ["implementation_planning", "documentation_handoff"],
            "instructions": "Own bounded planning passes and keep total scope finite.",
        },
        {
            "name": "DesignLead",
            "role": AgentRole.DESIGNER,
            "template_id": "designer_product_strategist",
            "skill_ids": ["ux_flow_mapping", "visual_polish"],
            "instructions": "Own bold product direction and user-facing design decisions.",
        },
        {
            "name": "InterfaceSystems",
            "role": AgentRole.DESIGNER,
            "template_id": "designer_interface_systems",
            "skill_ids": ["frontend_implementation", "ux_flow_mapping"],
            "instructions": "Own interaction systems, state clarity, and implementable UI structure.",
        },
        {
            "name": "PlatformArchitect",
            "role": AgentRole.ARCHITECT,
            "template_id": "architect_delivery_planner",
            "skill_ids": ["implementation_planning", "api_contracts"],
            "instructions": "Own delivery seams, architecture choices, and execution sequencing.",
        },
        {
            "name": "IntegrationGuardian",
            "role": AgentRole.ARCHITECT,
            "template_id": "architect_integration_guardian",
            "skill_ids": ["api_contracts", "database_modeling"],
            "instructions": "Own interfaces, contracts, and long-term system coherence.",
        },
        {
            "name": "SeniorBuilder",
            "role": AgentRole.DEVELOPER,
            "template_id": "developer_senior_builder",
            "skill_ids": ["frontend_implementation", "testing_strategy"],
            "instructions": "Take core feature implementation work and finish production-shaped slices.",
        },
        {
            "name": "RefactorSpecialist",
            "role": AgentRole.DEVELOPER,
            "template_id": "developer_refactor_specialist",
            "skill_ids": ["debugging_discipline", "testing_strategy"],
            "instructions": "Take structural cleanup, debugging, and risk-controlled refactors.",
        },
        {
            "name": "PrototypeSprinter",
            "role": AgentRole.DEVELOPER,
            "template_id": "developer_prototype_sprinter",
            "skill_ids": ["frontend_implementation", "documentation_handoff"],
            "instructions": "Take fast implementation spikes that still leave usable artifacts behind.",
        },
        {
            "name": "RegressionHunter",
            "role": AgentRole.TESTER,
            "template_id": "tester_regression_hunter",
            "skill_ids": ["testing_strategy", "debugging_discipline"],
            "instructions": "Own regression discovery, edge-case validation, and failure reproduction.",
        },
        {
            "name": "StrictReviewer",
            "role": AgentRole.REVIEWER,
            "template_id": "reviewer_strict_code_review",
            "skill_ids": ["release_readiness", "documentation_handoff"],
            "instructions": "Own critical review passes and call out correctness or verification gaps directly.",
        },
        {
            "name": "ReleaseGate",
            "role": AgentRole.REVIEW_AGENT,
            "template_id": "review_agent_release_gate",
            "skill_ids": ["release_readiness", "documentation_handoff"],
            "instructions": "Own final readiness checks before human approval.",
        },
    ]
