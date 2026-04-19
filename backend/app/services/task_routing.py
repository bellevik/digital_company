from __future__ import annotations

import re

from app.models.common import AgentRole, TaskType
from app.models.task import Task

_VISUAL_DESIGN_HINTS = (
    "visual",
    "motion",
    "animation",
    "typography",
    "layout",
    "look and feel",
)
_ARCHITECT_HINTS = (
    "scope",
    "state model",
    "architecture",
    "contract",
    "boundary",
    "schema",
    "data model",
    "ownership",
    "seam",
    "integration",
)
_TEST_HINTS = (
    "test",
    "qa",
    "verification",
    "validate",
    "regression",
)
_RELEASE_HINTS = (
    "final",
    "approval",
    "gate",
    "ship",
    "release",
    "sign-off",
    "scope lock",
)
_IMPLEMENTATION_VERBS = (
    "implement",
    "build",
    "layer",
    "wire",
    "ship",
    "create",
)
_PLANNING_VERBS = (
    "define",
    "design",
    "establish",
    "lock",
)
_BUGFIX_HINTS = (
    "bug",
    "fix",
    "repair",
    "regression",
    "broken",
    "500",
    "404",
    "error",
    "crash",
    "failure",
)
_PROTOTYPE_HINTS = (
    "prototype",
    "spike",
    "experiment",
    "proof of concept",
    "poc",
    "mvp",
    "draft",
)
_REFACTOR_HINTS = (
    "refactor",
    "cleanup",
    "stabilize",
    "simplify",
    "maintainability",
    "debt",
)


def preferred_role_for_task(*, title: str, description: str, task_type: TaskType) -> AgentRole:
    haystack = f"{title}\n{description}".lower()
    title_text = title.lower()

    if task_type == TaskType.IDEA:
        return AgentRole.PLANNER
    if task_type == TaskType.BUGFIX:
        return AgentRole.DEVELOPER
    if task_type == TaskType.OPS:
        return AgentRole.ARCHITECT
    if task_type == TaskType.REVIEW:
        if any(_contains_term(haystack, term) for term in _TEST_HINTS):
            return AgentRole.TESTER
        if any(_contains_term(haystack, term) for term in _RELEASE_HINTS):
            return AgentRole.REVIEW_AGENT
        return AgentRole.REVIEWER
    if task_type == TaskType.RESEARCH:
        if any(_contains_term(haystack, term) for term in _ARCHITECT_HINTS):
            return AgentRole.ARCHITECT
        if any(_contains_term(haystack, term) for term in _VISUAL_DESIGN_HINTS):
            return AgentRole.DESIGNER
        return AgentRole.ARCHITECT
    if task_type == TaskType.FEATURE:
        if any(_contains_term(title_text, verb) for verb in _IMPLEMENTATION_VERBS):
            return AgentRole.DEVELOPER
        if (
            any(_contains_term(title_text, verb) for verb in _PLANNING_VERBS)
            and any(_contains_term(haystack, term) for term in _VISUAL_DESIGN_HINTS)
        ):
            return AgentRole.DESIGNER
        if any(_contains_term(haystack, term) for term in _ARCHITECT_HINTS):
            return AgentRole.ARCHITECT
        return AgentRole.DEVELOPER
    return AgentRole.DEVELOPER


def task_matches_role(*, task: Task, role: AgentRole) -> bool:
    return preferred_role_for_task(
        title=task.title,
        description=task.description,
        task_type=task.type,
    ) == role


def task_matches_agent(*, task: Task, role: AgentRole, template_id: str | None) -> bool:
    if not task_matches_role(task=task, role=role):
        return False
    return agent_task_match_score(
        title=task.title,
        description=task.description,
        task_type=task.type,
        role=role,
        template_id=template_id,
    ) > 0


def agent_task_match_score(
    *,
    title: str,
    description: str,
    task_type: TaskType,
    role: AgentRole,
    template_id: str | None,
) -> int:
    if preferred_role_for_task(title=title, description=description, task_type=task_type) != role:
        return 0

    if role != AgentRole.DEVELOPER:
        return 1

    haystack = f"{title}\n{description}".lower()
    title_text = title.lower()

    if template_id == "developer_refactor_specialist":
        if task_type == TaskType.BUGFIX:
            return 4
        if any(_contains_term(haystack, term) for term in _BUGFIX_HINTS + _REFACTOR_HINTS):
            return 3
        if task_type == TaskType.FEATURE and any(_contains_term(haystack, term) for term in _REFACTOR_HINTS):
            return 2
        return 0

    if template_id == "developer_prototype_sprinter":
        if any(_contains_term(haystack, term) for term in _PROTOTYPE_HINTS):
            return 4
        if task_type == TaskType.FEATURE and any(
            _contains_term(title_text, verb) for verb in ("prototype", "spike", "draft", "create")
        ):
            return 2
        return 0 if task_type == TaskType.BUGFIX else 1

    if template_id == "developer_senior_builder":
        if task_type == TaskType.FEATURE:
            if any(_contains_term(title_text, verb) for verb in _IMPLEMENTATION_VERBS):
                return 4
            return 3
        if task_type == TaskType.BUGFIX:
            return 2
        return 1

    if task_type == TaskType.BUGFIX:
        return 2
    if task_type == TaskType.FEATURE:
        return 2
    return 1


def _contains_term(haystack: str, term: str) -> bool:
    if " " in term:
        return term in haystack
    return re.search(rf"\b{re.escape(term)}\b", haystack) is not None
