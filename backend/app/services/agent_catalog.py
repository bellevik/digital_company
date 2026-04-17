from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config import get_settings
from app.models.common import AgentRole


@dataclass(frozen=True, slots=True)
class AgentTemplateDefinition:
    id: str
    role: AgentRole
    name: str
    summary: str
    instructions: str
    is_default: bool = False


@dataclass(frozen=True, slots=True)
class AgentSkillDefinition:
    id: str
    name: str
    summary: str
    instructions: str
    path: Path
    source: str
    recommended_roles: tuple[AgentRole, ...] = ()


AGENT_TEMPLATES: tuple[AgentTemplateDefinition, ...] = (
    AgentTemplateDefinition(
        id="planner_delivery_strategist",
        role=AgentRole.PLANNER,
        name="Delivery Strategist",
        summary="Turns an idea into a bounded execution plan with explicit task budget.",
        instructions=(
            "You are a senior delivery planner. Convert ideas into an executable, finite plan with "
            "clear task boundaries, practical sequencing, and an explicit cap on future task growth."
        ),
        is_default=True,
    ),
    AgentTemplateDefinition(
        id="planner_product_scout",
        role=AgentRole.PLANNER,
        name="Product Scout",
        summary="Frames product ideas, risk, and recommended implementation phases.",
        instructions=(
            "You are a product planning lead. Clarify the value of the idea, map the major phases, "
            "and propose only the work needed to validate and ship it without runaway scope."
        ),
    ),
    AgentTemplateDefinition(
        id="designer_product_strategist",
        role=AgentRole.DESIGNER,
        name="Product Strategist",
        summary="Shapes user goals, flows, and clear design direction.",
        instructions=(
            "You are a senior product designer. Translate vague requests into a clear user journey, "
            "interaction model, and implementation-ready direction. Favor bold but usable ideas, "
            "state assumptions explicitly, and leave concrete artifact suggestions."
        ),
        is_default=True,
    ),
    AgentTemplateDefinition(
        id="designer_interface_systems",
        role=AgentRole.DESIGNER,
        name="Interface Systems Designer",
        summary="Focuses on structure, consistency, and reusable UI language.",
        instructions=(
            "You are a systems-minded interface designer. Prioritize information hierarchy, "
            "component consistency, layout rhythm, and states that developers can implement "
            "without guessing."
        ),
    ),
    AgentTemplateDefinition(
        id="architect_delivery_planner",
        role=AgentRole.ARCHITECT,
        name="Delivery Planner",
        summary="Turns goals into a pragmatic architecture and execution path.",
        instructions=(
            "You are a senior software architect. Break work into stable seams, choose the "
            "simplest durable design, and leave behind an execution plan that reduces ambiguity "
            "for downstream agents."
        ),
        is_default=True,
    ),
    AgentTemplateDefinition(
        id="architect_integration_guardian",
        role=AgentRole.ARCHITECT,
        name="Integration Guardian",
        summary="Protects system boundaries, contracts, and long-term coherence.",
        instructions=(
            "You are an integration-focused architect. Protect interfaces, data contracts, and "
            "operational safety. Push back on changes that create hidden coupling or ambiguous ownership."
        ),
    ),
    AgentTemplateDefinition(
        id="developer_senior_builder",
        role=AgentRole.DEVELOPER,
        name="Senior Builder",
        summary="Implements production-shaped code with strong defaults.",
        instructions=(
            "You are a senior developer. Prefer direct implementation over abstract planning, "
            "keep changes coherent, verify critical behavior, and leave real files behind in the workspace."
        ),
        is_default=True,
    ),
    AgentTemplateDefinition(
        id="developer_refactor_specialist",
        role=AgentRole.DEVELOPER,
        name="Refactor Specialist",
        summary="Improves structure while controlling regression risk.",
        instructions=(
            "You are a refactor-focused developer. Improve code structure, reduce repetition, "
            "and preserve existing behavior. Make the smallest set of edits that meaningfully improves maintainability."
        ),
    ),
    AgentTemplateDefinition(
        id="developer_prototype_sprinter",
        role=AgentRole.DEVELOPER,
        name="Prototype Sprinter",
        summary="Moves quickly while still producing testable artifacts.",
        instructions=(
            "You are a rapid prototyping developer. Move quickly toward a usable result, but do not "
            "fake completion. Produce tangible artifacts and clearly mark tradeoffs or missing hardening."
        ),
    ),
    AgentTemplateDefinition(
        id="tester_regression_hunter",
        role=AgentRole.TESTER,
        name="Regression Hunter",
        summary="Tries to break assumptions and surface hidden failures.",
        instructions=(
            "You are a sharp QA and test engineer. Attack edge cases, invalid states, and regressions "
            "first. Favor evidence, reproducibility, and concrete failure descriptions."
        ),
        is_default=True,
    ),
    AgentTemplateDefinition(
        id="tester_automation_driver",
        role=AgentRole.TESTER,
        name="Automation Driver",
        summary="Expands coverage with repeatable automated checks.",
        instructions=(
            "You are a test automation specialist. Convert risk into repeatable checks, strengthen "
            "coverage around fragile paths, and prefer executable verification over prose."
        ),
    ),
    AgentTemplateDefinition(
        id="reviewer_strict_code_review",
        role=AgentRole.REVIEWER,
        name="Strict Code Reviewer",
        summary="Finds correctness risks, regressions, and missing validation.",
        instructions=(
            "You are a demanding reviewer. Prioritize correctness issues, behavioral regressions, "
            "security or data risks, and insufficient testing before style or taste."
        ),
        is_default=True,
    ),
    AgentTemplateDefinition(
        id="reviewer_product_risk",
        role=AgentRole.REVIEWER,
        name="Product Risk Reviewer",
        summary="Reviews for user impact, clarity, and operational fallout.",
        instructions=(
            "You are a product-risk reviewer. Evaluate whether the change is understandable, "
            "operable, and safe for users and operators, not just technically valid."
        ),
    ),
    AgentTemplateDefinition(
        id="review_agent_release_gate",
        role=AgentRole.REVIEW_AGENT,
        name="Release Gate",
        summary="Acts as a final ship/no-ship checkpoint before human approval.",
        instructions=(
            "You are the release gate. Treat readiness seriously, demand concrete evidence, and "
            "recommend human approval only when the work is coherent, verified, and reviewable."
        ),
        is_default=True,
    ),
    AgentTemplateDefinition(
        id="review_agent_change_controller",
        role=AgentRole.REVIEW_AGENT,
        name="Change Controller",
        summary="Checks that changes are scoped, traceable, and properly handed off.",
        instructions=(
            "You are a change-control reviewer. Focus on whether the delivered work has clear scope, "
            "traceable artifacts, and enough context for human sign-off and follow-up."
        ),
    ),
)


_TEMPLATE_BY_ID = {template.id: template for template in AGENT_TEMPLATES}


def list_agent_templates(*, role: AgentRole | None = None) -> list[AgentTemplateDefinition]:
    if role is None:
        return list(AGENT_TEMPLATES)
    return [template for template in AGENT_TEMPLATES if template.role == role]


def list_agent_skills(*, repo_root: Path | None = None) -> list[AgentSkillDefinition]:
    skills_by_id: dict[str, AgentSkillDefinition] = {}
    for source, root in _skill_roots(repo_root=repo_root):
        if not root.exists():
            continue
        for candidate in sorted(root.iterdir()):
            if not candidate.is_dir() or candidate.name.startswith("."):
                continue
            skill_file = candidate / "SKILL.md"
            if not skill_file.is_file() or candidate.name in skills_by_id:
                continue
            skill = _load_skill_definition(skill_file=skill_file, source=source)
            if skill is not None:
                skills_by_id[skill.id] = skill
    return sorted(skills_by_id.values(), key=lambda skill: skill.name.lower())


def get_agent_template(template_id: str) -> AgentTemplateDefinition | None:
    return _TEMPLATE_BY_ID.get(template_id)


def get_agent_skill(skill_id: str, *, repo_root: Path | None = None) -> AgentSkillDefinition | None:
    return next((skill for skill in list_agent_skills(repo_root=repo_root) if skill.id == skill_id), None)


def default_template_id_for_role(role: AgentRole) -> str:
    for template in AGENT_TEMPLATES:
        if template.role == role and template.is_default:
            return template.id
    raise LookupError(f"default_template_missing_for_{role.value}")


def resolve_agent_template(*, role: AgentRole, template_id: str | None) -> AgentTemplateDefinition:
    resolved_id = template_id or default_template_id_for_role(role)
    template = get_agent_template(resolved_id)
    if template is None:
        raise ValueError(f"Unknown template_id '{resolved_id}'.")
    if template.role != role:
        raise ValueError(
            f"Template '{resolved_id}' is for role '{template.role.value}', not '{role.value}'."
        )
    return template


def resolve_agent_skills(
    skill_ids: list[str],
    *,
    repo_root: Path | None = None,
) -> list[AgentSkillDefinition]:
    resolved: list[AgentSkillDefinition] = []
    available_skills = {skill.id: skill for skill in list_agent_skills(repo_root=repo_root)}
    seen: set[str] = set()
    for skill_id in skill_ids:
        if skill_id in seen:
            continue
        skill = available_skills.get(skill_id)
        if skill is None:
            raise ValueError(f"Unknown skill_id '{skill_id}'.")
        resolved.append(skill)
        seen.add(skill_id)
    return resolved


def _skill_roots(*, repo_root: Path | None) -> list[tuple[str, Path]]:
    settings = get_settings()
    candidates: list[tuple[str, Path | None]] = []
    for source, root in [
        ("repo", settings.resolved_codex_workdir / "agent_skills"),
        ("repo", settings.repo_root / "agent_skills"),
        ("repo", Path("/workspace") / "agent_skills"),
        ("repo", (repo_root / "agent_skills") if repo_root is not None else None),
        ("codex_home", Path.home() / ".codex" / "skills"),
    ]:
        if root is None:
            continue
        candidates.append((source, root))

    unique_roots: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    for source, root in candidates:
        if root in seen:
            continue
        unique_roots.append((source, root))
        seen.add(root)
    return unique_roots


def _load_skill_definition(*, skill_file: Path, source: str) -> AgentSkillDefinition | None:
    raw = skill_file.read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(raw)
    metadata = frontmatter.get("metadata")
    metadata_map = metadata if isinstance(metadata, dict) else {}
    name = str(frontmatter.get("name") or skill_file.parent.name)
    description = str(frontmatter.get("description") or "")
    summary = str(metadata_map.get("short-description") or description or name)
    instructions = body.strip() or description
    if not instructions:
        return None

    return AgentSkillDefinition(
        id=skill_file.parent.name,
        name=name,
        summary=summary,
        instructions=instructions,
        path=skill_file,
        source=source,
        recommended_roles=_parse_recommended_roles(metadata_map.get("recommended-roles")),
    )


def _split_frontmatter(raw: str) -> tuple[dict[str, object], str]:
    lines = raw.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return {}, raw.strip()

    for index in range(1, len(lines)):
        if lines[index].strip() != "---":
            continue
        frontmatter = _parse_simple_yaml("\n".join(lines[1:index]))
        body = "\n".join(lines[index + 1 :]).strip()
        return frontmatter, body

    return {}, raw.strip()


def _parse_simple_yaml(raw: str) -> dict[str, object]:
    payload: dict[str, object] = {}
    active_section: str | None = None
    for raw_line in raw.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith("  "):
            if line.endswith(":"):
                active_section = line[:-1].strip()
                payload[active_section] = {}
                continue
            key, _, value = line.partition(":")
            payload[key.strip()] = _parse_scalar(value)
            active_section = None
            continue
        if active_section is None:
            continue
        nested = line.strip()
        if nested.endswith(":"):
            continue
        key, _, value = nested.partition(":")
        section = payload.get(active_section)
        if isinstance(section, dict):
            section[key.strip()] = _parse_scalar(value)
    return payload


def _parse_scalar(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _parse_recommended_roles(raw: object) -> tuple[AgentRole, ...]:
    if not isinstance(raw, str) or not raw.strip():
        return ()

    resolved: list[AgentRole] = []
    for part in raw.split(","):
        candidate = part.strip()
        if not candidate:
            continue
        try:
            resolved.append(AgentRole(candidate))
        except ValueError:
            continue
    return tuple(dict.fromkeys(resolved))
