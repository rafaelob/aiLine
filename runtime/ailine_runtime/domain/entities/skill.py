"""Skill-related domain entities for the Skills DB persistence layer (F-175).

Pure Pydantic models representing skills, their versions, and ratings.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Skill(BaseModel):
    """A persisted skill definition."""

    id: str = ""
    slug: str
    description: str = ""
    instructions_md: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)
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


class SkillVersion(BaseModel):
    """A version snapshot of a skill's instructions."""

    id: str = ""
    skill_id: str
    version: int
    instructions_md: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)
    change_summary: str = ""
    created_at: str = ""


class SkillRating(BaseModel):
    """A teacher's rating of a skill (1-5)."""

    id: str = ""
    skill_id: str
    user_id: str
    score: int
    comment: str = ""
    created_at: str = ""
