"""Skills Discovery API router.

Exposes the skills registry as a discoverable API, allowing the frontend
and external consumers to list available agent skills, inspect individual
skill details, and query accessibility-to-skill policy mappings.
"""

from __future__ import annotations

import functools
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Response

from ...app.authz import require_authenticated
from ...shared.config import get_settings

router = APIRouter()
_log = structlog.get_logger("ailine.api.skills")

# Sentinel for caching None results (registry unavailable).
_REGISTRY_UNAVAILABLE = object()


@functools.lru_cache(maxsize=1)
def _get_registry_cached() -> Any:
    """Build and cache the skill registry singleton (thread-safe via lru_cache).

    Returns the SkillRegistry or _REGISTRY_UNAVAILABLE sentinel on failure.
    """
    try:
        from ailine_agents.skills.registry import SkillRegistry

        settings = get_settings()
        registry = SkillRegistry()
        count = registry.scan_paths(settings.skill_source_paths())
        _log.info("skills_registry.loaded", skill_count=count)
        return registry
    except Exception:
        _log.warning("skills_registry.unavailable", exc_info=True)
        return _REGISTRY_UNAVAILABLE


def _get_registry() -> Any:
    """Get the cached skill registry, returning None if unavailable."""
    result = _get_registry_cached()
    return None if result is _REGISTRY_UNAVAILABLE else result


def _get_accessibility_policy() -> dict[str, Any] | None:
    """Import the accessibility skill policy mapping."""
    try:
        from ailine_agents.skills.accessibility_policy import (
            ACCESSIBILITY_SKILL_POLICY,
        )

        return ACCESSIBILITY_SKILL_POLICY  # type: ignore[return-value]
    except ImportError:
        return None


def _skill_to_summary(name: str, skill: Any) -> dict[str, Any]:
    """Convert a SkillDefinition to a JSON-safe summary dict."""
    metadata = getattr(skill, "metadata", {}) or {}
    return {
        "slug": name,
        "name": name,
        "description": getattr(skill, "description", ""),
        "category": metadata.get("category", "general"),
        "version": metadata.get("version", "1.0.0"),
        "compatibility": metadata.get("compatibility", ""),
        "has_instructions": bool(getattr(skill, "instructions", "")),
    }


def _skill_to_detail(name: str, skill: Any) -> dict[str, Any]:
    """Convert a SkillDefinition to a detailed JSON-safe dict."""
    summary = _skill_to_summary(name, skill)
    instructions = getattr(skill, "instructions", "")
    # Provide a truncated preview (first 500 chars) and full metadata
    summary["instructions_preview"] = instructions[:500] if instructions else ""
    summary["instructions_length"] = len(instructions)
    summary["metadata"] = getattr(skill, "metadata", {}) or {}
    return summary


@router.get("")
async def list_skills(
    response: Response,
    category: str | None = Query(None, description="Filter by category."),
    q: str | None = Query(None, description="Search skills by name or description."),
    _teacher_id: str = Depends(require_authenticated),
) -> dict[str, Any]:
    """List all available skills with metadata.

    Returns skill count, category breakdown, and a list of skill summaries.
    Supports optional filtering by category and text search.
    """
    response.headers["Cache-Control"] = "public, max-age=300"
    registry = _get_registry()
    if registry is None:
        return {"count": 0, "categories": {}, "skills": []}

    skills_dict = registry.skills
    summaries = [
        _skill_to_summary(name, skill) for name, skill in sorted(skills_dict.items())
    ]

    # Apply category filter
    if category:
        summaries = [s for s in summaries if s["category"] == category]

    # Apply text search
    if q:
        q_lower = q.lower()
        summaries = [
            s
            for s in summaries
            if q_lower in s["name"].lower() or q_lower in s["description"].lower()
        ]

    # Build category breakdown
    categories: dict[str, int] = {}
    for s in summaries:
        cat = s["category"]
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "count": len(summaries),
        "categories": categories,
        "skills": summaries,
    }


@router.get("/policy/{profile}")
async def skill_policy_for_profile(
    profile: str,
    max_skills: int = Query(8, ge=1, le=20, description="Max skills to return."),
    _teacher_id: str = Depends(require_authenticated),
) -> dict[str, Any]:
    """Get the accessibility skill policy for a given profile.

    Returns the ordered list of recommended skills with priority tiers
    (must/should/nice) and whether human review is required.

    Valid profiles: autism, adhd, learning, hearing, visual,
    speech_language, motor.
    """
    try:
        from ailine_agents.skills.accessibility_policy import (
            ACCESSIBILITY_NEED_CATEGORIES,
            resolve_accessibility_skills,
        )
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Accessibility policy module unavailable.",
        ) from exc

    if profile not in ACCESSIBILITY_NEED_CATEGORIES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown profile '{profile}'. Valid profiles: {sorted(ACCESSIBILITY_NEED_CATEGORIES)}",
        )

    skills_list, needs_human_review = resolve_accessibility_skills(
        [profile],
        max_skills=max_skills,
    )

    return {
        "profile": profile,
        "max_skills": max_skills,
        "needs_human_review": needs_human_review,
        "skills": [
            {"slug": slug, "reason": reason, "priority": priority}
            for slug, reason, priority in skills_list
        ],
        "skill_count": len(skills_list),
    }


@router.get("/policies")
async def list_all_policies(
    _teacher_id: str = Depends(require_authenticated),
) -> dict[str, Any]:
    """List all accessibility profiles and their skill policies summary."""
    policy_map = _get_accessibility_policy()
    if policy_map is None:
        return {"profiles": {}}

    profiles: dict[str, dict[str, Any]] = {}
    for name, policy in policy_map.items():
        profiles[name] = {
            "must": list(policy.must),
            "should": list(policy.should),
            "nice": list(policy.nice),
            "human_review_triggers": list(policy.human_review_triggers),
            "total_skills": len(
                set(policy.must) | set(policy.should) | set(policy.nice)
            ),
        }

    return {"profiles": profiles}


@router.get("/{slug}")
async def get_skill_detail(
    slug: str,
    _teacher_id: str = Depends(require_authenticated),
) -> dict[str, Any]:
    """Get detailed skill information including instructions preview.

    Returns full metadata and a preview of the skill instructions.
    """
    registry = _get_registry()
    if registry is None:
        raise HTTPException(status_code=503, detail="Skills registry unavailable.")

    skill = registry.get_by_name(slug)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill '{slug}' not found.")

    return _skill_to_detail(slug, skill)
