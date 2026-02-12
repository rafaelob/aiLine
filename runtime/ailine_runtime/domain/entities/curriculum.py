"""Curriculum-related domain entities.

Pure Pydantic models representing curriculum standards and objectives
across different educational systems (BNCC, CCSS, CCSS_ELA, NGSS, etc.).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

BloomLevel = Literal[
    "remember", "understand", "apply", "analyze", "evaluate", "create"
]


class CurriculumSystem(StrEnum):
    """Supported curriculum standard systems."""

    BNCC = "bncc"
    CCSS = "ccss"
    CCSS_ELA = "ccss_ela"
    NGSS = "ngss"


class CurriculumObjective(BaseModel):
    """A single curriculum objective from a recognized standard.

    Examples:
        - BNCC: code="EF06MA01", system="bncc", subject="Matematica", grade="6o ano"
        - CCSS: code="CCSS.MATH.CONTENT.6.NS.A.1", system="ccss", subject="Math", grade="Grade 6"
    """

    code: str = Field(
        ...,
        description="Standard code (e.g. EF06MA01, CCSS.MATH.CONTENT.6.NS.A.1)",
    )
    system: CurriculumSystem
    subject: str
    grade: str
    domain: str = ""
    description: str
    keywords: list[str] = Field(default_factory=list)
    bloom_level: BloomLevel | None = Field(
        None,
        description="Bloom's Taxonomy level: remember, understand, apply, analyze, evaluate, create",
    )
