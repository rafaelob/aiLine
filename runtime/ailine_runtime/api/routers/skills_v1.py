# ruff: noqa: B008
"""Skills CRUD API (F-176) -- database-backed skill management.

Provides RESTful endpoints for creating, reading, updating, and deleting
skills stored in the skills database. Supports forking, rating, and
context-based skill suggestions.

All endpoints require authentication. Write operations (create, update,
delete, fork) require teacher or admin role. Rating requires any
authenticated teacher.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...app.authz import (
    require_authenticated,
    require_teacher_or_admin,
)
from ...domain.entities.skill import Skill
from ...domain.entities.user import UserRole
from ...domain.ports.skills import SkillRepository
from ...shared.tenant import get_current_user_role

router = APIRouter()
_log = structlog.get_logger("ailine.api.skills_v1")

# ---------------------------------------------------------------------------
# Dependency: SkillRepository
# ---------------------------------------------------------------------------

# The repository is injected at the app level via dependency_overrides.
# Production wires PostgresSkillRepository; tests wire FakeSkillRepository.

_skill_repo_instance: SkillRepository | None = None


def set_skill_repo(repo: SkillRepository) -> None:
    """Set the skill repository instance (called during app setup)."""
    global _skill_repo_instance
    _skill_repo_instance = repo


def is_skill_repo_set() -> bool:
    """Check whether a skill repository has been injected."""
    return _skill_repo_instance is not None


def get_skill_repo() -> SkillRepository:
    """FastAPI dependency that returns the skill repository."""
    if _skill_repo_instance is None:
        raise HTTPException(
            status_code=503,
            detail="Skills database not configured.",
        )
    return _skill_repo_instance


# ---------------------------------------------------------------------------
# Request/Response schemas
# ---------------------------------------------------------------------------


class SkillCreateIn(BaseModel):
    """Request body for creating a new skill."""

    slug: str = Field(..., min_length=1, max_length=200, description="Unique skill slug")
    title: str = Field(default="", max_length=500, description="Human-readable title")
    description: str = Field(default="", max_length=5000)
    instructions_md: str = Field(default="", max_length=50000)
    metadata_json: dict[str, str] = Field(default_factory=dict)
    license: str = Field(default="", max_length=100)
    compatibility: str = Field(default="", max_length=500)
    allowed_tools: str = Field(default="", max_length=2000)


class SkillUpdateIn(BaseModel):
    """Request body for updating an existing skill."""

    title: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    instructions_md: str | None = Field(default=None, max_length=50000)
    metadata_json: dict[str, str] | None = None
    change_summary: str = Field(default="", max_length=500)


class SkillRateIn(BaseModel):
    """Request body for rating a skill."""

    score: int = Field(..., ge=1, le=5, description="Rating score 1-5")
    comment: str = Field(default="", max_length=2000)


class SkillSummaryOut(BaseModel):
    """Skill summary (no full instructions)."""

    id: str
    slug: str
    description: str
    license: str = ""
    compatibility: str = ""
    allowed_tools: str = ""
    teacher_id: str | None = None
    forked_from_id: str | None = None
    is_active: bool = True
    is_system: bool = False
    version: int = 1
    avg_rating: float = 0.0
    rating_count: int = 0
    created_at: str = ""
    updated_at: str = ""


class SkillDetailOut(SkillSummaryOut):
    """Full skill detail with instructions."""

    instructions_md: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)


class SkillListOut(BaseModel):
    """Paginated skill list response."""

    count: int
    skills: list[SkillSummaryOut]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _skill_to_summary(skill: Skill) -> SkillSummaryOut:
    return SkillSummaryOut(
        id=skill.id,
        slug=skill.slug,
        description=skill.description,
        license=skill.license,
        compatibility=skill.compatibility,
        allowed_tools=skill.allowed_tools,
        teacher_id=skill.teacher_id,
        forked_from_id=skill.forked_from_id,
        is_active=skill.is_active,
        is_system=skill.is_system,
        version=skill.version,
        avg_rating=skill.avg_rating,
        rating_count=skill.rating_count,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
    )


def _skill_to_detail(skill: Skill) -> SkillDetailOut:
    return SkillDetailOut(
        id=skill.id,
        slug=skill.slug,
        description=skill.description,
        instructions_md=skill.instructions_md,
        metadata=skill.metadata,
        license=skill.license,
        compatibility=skill.compatibility,
        allowed_tools=skill.allowed_tools,
        teacher_id=skill.teacher_id,
        forked_from_id=skill.forked_from_id,
        is_active=skill.is_active,
        is_system=skill.is_system,
        version=skill.version,
        avg_rating=skill.avg_rating,
        rating_count=skill.rating_count,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=SkillListOut)
async def list_skills(
    q: str | None = Query(None, description="Text search in slug and description"),
    system_only: bool = Query(False, description="Only return system skills"),
    teacher_id: str | None = Query(None, description="Filter by teacher_id"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    _user_id: str = Depends(require_authenticated),
    repo: SkillRepository = Depends(get_skill_repo),
) -> SkillListOut:
    """List skills with optional search and filtering.

    Returns ``count`` as the **total** number of matching skills (before
    pagination) so clients can compute page counts correctly.
    """
    if q:
        skills = await repo.search_by_text(q, limit=limit + offset)
    elif teacher_id:
        skills = await repo.list_by_teacher(teacher_id)
    elif system_only:
        skills = await repo.list_all(system_only=True)
    else:
        skills = await repo.list_all(system_only=False)

    # Total count BEFORE pagination
    total = len(skills)

    # Apply pagination
    paginated = skills[offset : offset + limit]
    summaries = [_skill_to_summary(s) for s in paginated]

    return SkillListOut(count=total, skills=summaries)


@router.get("/suggest", response_model=SkillListOut)
async def suggest_skills(
    context: str = Query(..., min_length=1, description="Learning context description"),
    limit: int = Query(5, ge=1, le=20),
    _user_id: str = Depends(require_authenticated),
    repo: SkillRepository = Depends(get_skill_repo),
) -> SkillListOut:
    """Suggest skills relevant to a learning context.

    Uses text search to find skills matching the context description.
    If vector embeddings are available, uses similarity search instead.
    """
    skills = await repo.search_by_text(context, limit=limit)
    summaries = [_skill_to_summary(s) for s in skills]
    return SkillListOut(count=len(summaries), skills=summaries)


@router.get("/{slug}", response_model=SkillDetailOut)
async def get_skill(
    slug: str,
    _user_id: str = Depends(require_authenticated),
    repo: SkillRepository = Depends(get_skill_repo),
) -> SkillDetailOut:
    """Get full skill detail including instructions."""
    skill = await repo.get_by_slug(slug)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill '{slug}' not found.")
    return _skill_to_detail(skill)


@router.post("", response_model=SkillDetailOut, status_code=201)
async def create_skill(
    body: SkillCreateIn,
    user_id: str = Depends(require_teacher_or_admin),
    repo: SkillRepository = Depends(get_skill_repo),
) -> SkillDetailOut:
    """Create a new skill.

    Requires teacher or admin role. The skill is owned by the
    authenticated user (teacher_id set from JWT).
    """
    # Check for slug conflict
    existing = await repo.get_by_slug(body.slug)
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Skill with slug '{body.slug}' already exists.",
        )

    skill = Skill(
        slug=body.slug,
        description=body.description or body.title,
        instructions_md=body.instructions_md,
        metadata=body.metadata_json,
        license=body.license,
        compatibility=body.compatibility,
        allowed_tools=body.allowed_tools,
    )

    await repo.create(skill, teacher_id=user_id)
    _log.info("skill.created", slug=body.slug, teacher_id=user_id)

    # Retrieve the created skill to return full detail
    created = await repo.get_by_slug(body.slug)
    if created is None:
        # Should not happen, but defensive
        raise HTTPException(status_code=500, detail="Skill creation failed.")
    return _skill_to_detail(created)


@router.put("/{slug}", response_model=SkillDetailOut)
async def update_skill(
    slug: str,
    body: SkillUpdateIn,
    user_id: str = Depends(require_teacher_or_admin),
    repo: SkillRepository = Depends(get_skill_repo),
) -> SkillDetailOut:
    """Update an existing skill.

    Only the owner or an admin can update a skill. Creates a new
    version automatically.
    """
    skill = await repo.get_by_slug(slug)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill '{slug}' not found.")

    # Ownership check: only owner or super_admin
    role = get_current_user_role()
    if role != UserRole.SUPER_ADMIN and skill.teacher_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Only the skill owner or an admin can update this skill.",
        )

    await repo.update(
        slug,
        instructions_md=body.instructions_md,
        description=body.description,
        metadata=body.metadata_json,
        change_summary=body.change_summary,
    )
    _log.info("skill.updated", slug=slug, teacher_id=user_id)

    updated = await repo.get_by_slug(slug)
    if updated is None:
        raise HTTPException(status_code=500, detail="Skill update failed.")
    return _skill_to_detail(updated)


@router.delete("/{slug}", status_code=204)
async def delete_skill(
    slug: str,
    user_id: str = Depends(require_teacher_or_admin),
    repo: SkillRepository = Depends(get_skill_repo),
) -> None:
    """Soft-delete a skill (set is_active=False).

    Only the owner or an admin can delete a skill.
    """
    skill = await repo.get_by_slug(slug)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill '{slug}' not found.")

    role = get_current_user_role()
    if role != UserRole.SUPER_ADMIN and skill.teacher_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Only the skill owner or an admin can delete this skill.",
        )

    await repo.soft_delete(slug)
    _log.info("skill.deleted", slug=slug, teacher_id=user_id)


@router.post("/{slug}/fork", response_model=SkillDetailOut, status_code=201)
async def fork_skill(
    slug: str,
    user_id: str = Depends(require_teacher_or_admin),
    repo: SkillRepository = Depends(get_skill_repo),
) -> SkillDetailOut:
    """Fork an existing skill to the authenticated teacher's collection.

    Creates a new skill with a reference to the original (forked_from_id).
    The forked slug follows the pattern ``{slug}-fork[-N]``.
    """
    try:
        forked_id = await repo.fork(slug, teacher_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    _log.info("skill.forked", source_slug=slug, teacher_id=user_id, forked_id=forked_id)

    # Look up by the returned ID — the slug may have a counter suffix
    # We search by teacher's skills and find by forked_from reference
    teacher_skills = await repo.list_by_teacher(user_id)
    forked = next((s for s in teacher_skills if s.id == forked_id), None)
    if forked is None:
        raise HTTPException(status_code=500, detail="Fork operation failed.")
    return _skill_to_detail(forked)


@router.post("/{slug}/rate", status_code=200)
async def rate_skill(
    slug: str,
    body: SkillRateIn,
    user_id: str = Depends(require_authenticated),
    repo: SkillRepository = Depends(get_skill_repo),
) -> dict[str, Any]:
    """Rate a skill (1-5). Upserts: re-rating updates the existing score."""
    skill = await repo.get_by_slug(slug)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill '{slug}' not found.")

    await repo.rate(slug, user_id=user_id, score=body.score, comment=body.comment)
    _log.info("skill.rated", slug=slug, user_id=user_id, score=body.score)

    # Return updated rating info
    updated = await repo.get_by_slug(slug)
    return {
        "slug": slug,
        "score": body.score,
        "avg_rating": updated.avg_rating if updated else 0.0,
        "rating_count": updated.rating_count if updated else 0,
    }
