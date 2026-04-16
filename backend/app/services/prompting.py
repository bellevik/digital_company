from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.models.agent import Agent
from app.models.common import AgentRole, TaskType
from app.schemas.memory_search import MemorySearchResult
from app.models.task import Task


@dataclass(frozen=True)
class RoleProfile:
    role: AgentRole
    supported_task_types: tuple[TaskType, ...]
    prompt_instruction: str


ROLE_PROFILES: dict[AgentRole, RoleProfile] = {
    AgentRole.DESIGNER: RoleProfile(
        role=AgentRole.DESIGNER,
        supported_task_types=(TaskType.FEATURE, TaskType.RESEARCH),
        prompt_instruction=(
            "Approach the task as a product and UX designer. Clarify the user-facing shape, "
            "constraints, and the recommended next implementation step."
        ),
    ),
    AgentRole.ARCHITECT: RoleProfile(
        role=AgentRole.ARCHITECT,
        supported_task_types=(TaskType.FEATURE, TaskType.RESEARCH, TaskType.OPS),
        prompt_instruction=(
            "Approach the task as a software architect. Produce a concrete implementation decision "
            "that keeps the system simple, evolvable, and consistent."
        ),
    ),
    AgentRole.DEVELOPER: RoleProfile(
        role=AgentRole.DEVELOPER,
        supported_task_types=(TaskType.FEATURE, TaskType.BUGFIX, TaskType.OPS),
        prompt_instruction=(
            "Implement the requested change directly. Keep scope tight and report concrete outcomes."
        ),
    ),
    AgentRole.TESTER: RoleProfile(
        role=AgentRole.TESTER,
        supported_task_types=(TaskType.FEATURE, TaskType.BUGFIX, TaskType.REVIEW),
        prompt_instruction=(
            "Validate behavior with tests and failure-oriented reasoning. Surface regressions clearly."
        ),
    ),
    AgentRole.REVIEWER: RoleProfile(
        role=AgentRole.REVIEWER,
        supported_task_types=(TaskType.REVIEW,),
        prompt_instruction=(
            "Review the work critically. Focus on defects, risks, and missing verification."
        ),
    ),
    AgentRole.REVIEW_AGENT: RoleProfile(
        role=AgentRole.REVIEW_AGENT,
        supported_task_types=(TaskType.REVIEW, TaskType.OPS),
        prompt_instruction=(
            "Act as the final approval gate. Confirm whether work is ready for human review."
        ),
    ),
}


def get_role_profile(role: AgentRole) -> RoleProfile:
    return ROLE_PROFILES[role]


def build_prompt(
    *,
    agent: Agent,
    task: Task,
    memories: list[MemorySearchResult],
    repo_root: Path,
    project_workspace: Path | None,
) -> str:
    role_profile = get_role_profile(agent.role)
    memory_block = _format_memories(memories)
    workspace_block = _format_workspace_context(
        repo_root=repo_root,
        project_workspace=project_workspace,
    )

    return f"""You are the {agent.role.value} agent named {agent.name}.

Role instruction:
{role_profile.prompt_instruction}

Task:
Title: {task.title}
Type: {task.type.value}
Project: {task.project_id or "unscoped"}
Description:
{task.description}

Workspace:
{workspace_block}

Recent memory context:
{memory_block}

Return JSON only with this shape:
{{
  "summary": "short execution summary",
  "memory_summary": "short memory title",
  "memory_content": "durable implementation notes",
  "artifact_paths": ["relative/path/inside/project/workspace"],
  "follow_up_tasks": [
    {{
      "title": "task title",
      "description": "task description",
      "type": "feature|bugfix|research|review|ops",
      "project_id": "optional project id"
    }}
  ]
}}

For project-scoped tasks, create or update concrete files inside the project workspace before reporting success.
If no concrete artifact is produced for a project-scoped task, return "final_status": "failed" and explain the blocker.
List artifact_paths relative to the project workspace. Omit artifact_paths only when there is genuinely no filesystem artifact.
Omit follow_up_tasks when none are needed. Do not include markdown fences.
"""


def _format_memories(memories: list[MemorySearchResult]) -> str:
    if not memories:
        return "No prior memory available."

    lines = []
    for memory in memories:
        lines.append(
            f"- [{memory.type.value}] {memory.summary} "
            f"(score={memory.combined_score:.3f}): {memory.content}"
        )
    return "\n".join(lines)


def _format_workspace_context(*, repo_root: Path, project_workspace: Path | None) -> str:
    if project_workspace is None:
        return (
            f"Repository root: {repo_root}\n"
            "This task is not scoped to a project workspace. Use the repository root when you need to create files."
        )

    return (
        f"Repository root: {repo_root}\n"
        f"Project workspace: {project_workspace}\n"
        "Do the concrete work inside the project workspace unless the task explicitly requires touching shared repo files."
    )
