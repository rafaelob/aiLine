"""CurriculumProvider adapter for Brazilian BNCC standards.

Loads objectives from ``data/curriculum/bncc.json`` and provides
search, lookup-by-code, and list-standards operations that satisfy
the ``CurriculumProvider`` port protocol.
"""

from __future__ import annotations

import structlog

from ...domain.entities.curriculum import CurriculumObjective
from .loader import keyword_matches, load_objectives_from_json, text_matches

logger = structlog.get_logger(__name__)


class BNCCProvider:
    """CurriculumProvider implementation for Brazilian BNCC standards."""

    def __init__(self) -> None:
        self._objectives: list[CurriculumObjective] = []
        self._loaded = False

    # ------------------------------------------------------------------
    # Lazy loading — defers I/O until first access
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._objectives = load_objectives_from_json("bncc.json")
        self._loaded = True
        logger.info("bncc_provider.loaded", count=len(self._objectives))

    # ------------------------------------------------------------------
    # Port: CurriculumProvider
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        *,
        grade: str | None = None,
        subject: str | None = None,
        system: str | None = None,
        bloom_level: str | None = None,
    ) -> list[CurriculumObjective]:
        """Search BNCC objectives matching *query* with optional filters.

        The query is matched against code, description, and keywords.
        Filters (grade, subject, bloom_level) are applied as additional constraints.
        """
        self._ensure_loaded()

        # If system filter is set and not bncc, return empty
        if system and system.lower() != "bncc":
            return []

        results: list[CurriculumObjective] = []
        for obj in self._objectives:
            if not _matches_query(query, obj):
                continue
            if grade and not text_matches(grade, obj.grade):
                continue
            if subject and not text_matches(subject, obj.subject):
                continue
            if bloom_level and obj.bloom_level != bloom_level.lower():
                continue
            results.append(obj)
        return results

    async def get_by_code(self, code: str) -> CurriculumObjective | None:
        """Return the objective with an exact code match, or None."""
        self._ensure_loaded()
        for obj in self._objectives:
            if obj.code == code:
                return obj
        return None

    async def list_standards(self, *, system: str | None = None) -> list[str]:
        """Return all BNCC standard codes, optionally filtered by system."""
        self._ensure_loaded()
        if system and system.lower() != "bncc":
            return []
        return [obj.code for obj in self._objectives]


def _matches_query(query: str, obj: CurriculumObjective) -> bool:
    """Check if *query* appears in any searchable field of the objective."""
    q = query.lower()
    if q in obj.code.lower():
        return True
    if q in obj.description.lower():
        return True
    if q in obj.domain.lower():
        return True
    if q in obj.subject.lower():
        return True
    return keyword_matches(query, obj)
