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


def _contains_term(haystack: str, term: str) -> bool:
    if " " in term:
        return term in haystack
    return re.search(rf"\b{re.escape(term)}\b", haystack) is not None
