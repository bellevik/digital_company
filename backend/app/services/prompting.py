from __future__ import annotations

from dataclasses import dataclass

from app.models.agent import Agent
from app.models.common import AgentRole, TaskType
from app.models.memory import Memory
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


def build_prompt(*, agent: Agent, task: Task, memories: list[Memory]) -> str:
    role_profile = get_role_profile(agent.role)
    memory_block = _format_memories(memories)

    return f"""You are the {agent.role.value} agent named {agent.name}.

Role instruction:
{role_profile.prompt_instruction}

Task:
Title: {task.title}
Type: {task.type.value}
Project: {task.project_id or "unscoped"}
Description:
{task.description}

Recent memory context:
{memory_block}

Return JSON only with this shape:
{{
  "summary": "short execution summary",
  "memory_summary": "short memory title",
  "memory_content": "durable implementation notes",
  "follow_up_tasks": [
    {{
      "title": "task title",
      "description": "task description",
      "type": "feature|bugfix|research|review|ops",
      "project_id": "optional project id"
    }}
  ]
}}

Omit follow_up_tasks when none are needed. Do not include markdown fences.
"""


def _format_memories(memories: list[Memory]) -> str:
    if not memories:
        return "No prior memory available."

    lines = []
    for memory in memories:
        lines.append(f"- [{memory.type.value}] {memory.summary}: {memory.content}")
    return "\n".join(lines)
