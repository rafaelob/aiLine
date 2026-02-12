"""CurriculumProvider adapter for US standards (CCSS Math + NGSS Science).

Loads objectives from ``data/curriculum/ccss_math.json`` and
``data/curriculum/ngss.json``, combining them into a single provider
that satisfies the ``CurriculumProvider`` port protocol.
"""

from __future__ import annotations

import structlog

from ...domain.entities.curriculum import CurriculumObjective
from .loader import keyword_matches, load_objectives_from_json, text_matches

logger = structlog.get_logger(__name__)


class USProvider:
    """CurriculumProvider implementation for US standards (CCSS + NGSS)."""

    def __init__(self) -> None:
        self._objectives: list[CurriculumObjective] = []
        self._loaded = False

    # ------------------------------------------------------------------
    # Lazy loading
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        ccss = load_objectives_from_json("ccss_math.json")
        ccss_ela = load_objectives_from_json("ccss_ela.json")
        ngss = load_objectives_from_json("ngss.json")
        self._objectives = ccss + ccss_ela + ngss
        self._loaded = True
        logger.info(
            "us_provider.loaded",
            ccss_count=len(ccss),
            ccss_ela_count=len(ccss_ela),
            ngss_count=len(ngss),
            total=len(self._objectives),
        )

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
        """Search US objectives matching *query* with optional filters."""
        self._ensure_loaded()

        # System filter — allow ccss, ccss_ela, ngss, or omit for all
        allowed_systems = _resolve_systems(system)
        if allowed_systems is not None and not allowed_systems:
            return []

        results: list[CurriculumObjective] = []
        for obj in self._objectives:
            if allowed_systems and obj.system.value not in allowed_systems:
                continue
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
        """Return all US standard codes, optionally filtered by system."""
        self._ensure_loaded()
        allowed = _resolve_systems(system)
        if allowed is not None and not allowed:
            return []
        return [
            obj.code
            for obj in self._objectives
            if allowed is None or obj.system.value in allowed
        ]


def _resolve_systems(system: str | None) -> set[str] | None:
    """Resolve a system filter string into a set of allowed values.

    Returns None when no filter is needed (all US systems allowed).
    Returns an empty set when the requested system is not a US system.
    """
    if system is None:
        return None
    s = system.lower()
    if s in ("ccss", "ccss_ela", "ngss"):
        return {s}
    # Unknown system — not a US standard
    return set()


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
