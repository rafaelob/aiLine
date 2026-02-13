"""Unified CurriculumProvider that delegates to BNCC and US providers.

Implements the ``CurriculumProvider`` port by combining results from
both the BNCC and US (CCSS + NGSS) providers.  Also exposes grade
mapping between Brazilian and US systems.
"""

from __future__ import annotations

from typing import Any

import structlog

from ...domain.entities.curriculum import CurriculumObjective
from .bncc_provider import BNCCProvider
from .loader import load_grade_mapping
from .us_provider import USProvider

logger = structlog.get_logger(__name__)


class UnifiedCurriculumProvider:
    """Combines BNCC + US providers and adds cross-system grade mapping.

    This is the primary adapter wired into the DI container.  It fans
    out every search/lookup to both underlying providers and merges the
    results.
    """

    def __init__(
        self,
        *,
        bncc: BNCCProvider | None = None,
        us: USProvider | None = None,
    ) -> None:
        self._bncc = bncc or BNCCProvider()
        self._us = us or USProvider()
        self._grade_mapping: dict[str, Any] | None = None

    # ------------------------------------------------------------------
    # Grade mapping
    # ------------------------------------------------------------------

    def _ensure_grade_mapping(self) -> dict[str, Any]:
        if self._grade_mapping is None:
            self._grade_mapping = load_grade_mapping()
        return self._grade_mapping

    def get_grade_mapping(self) -> dict[str, Any]:
        """Return the full grade mapping dict (BR <-> US)."""
        return self._ensure_grade_mapping()

    def translate_grade(self, grade: str) -> str | None:
        """Translate a grade label between BR and US systems.

        Args:
            grade: A Brazilian grade (e.g. "6o ano") or US grade (e.g. "Grade 6").

        Returns:
            The equivalent grade in the other system, or None if not found.
        """
        mapping = self._ensure_grade_mapping()
        g = grade.lower().replace("º", "o")

        for entry in mapping["mappings"]:
            if g == str(entry["br"]).lower().replace("º", "o"):
                return str(entry["us"])
            if g == str(entry["us"]).lower():
                return str(entry["br"])

        # Check kindergarten
        kg = mapping.get("kindergarten", {})
        if kg:
            if g == str(kg["br"]).lower().replace("º", "o"):
                return str(kg["us"])
            if g == str(kg["us"]).lower():
                return str(kg["br"])

        return None

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
        """Search across all curriculum systems.

        Delegates to BNCC and/or US providers based on the optional
        *system* filter and merges results.
        """
        results: list[CurriculumObjective] = []

        if system is None or system.lower() == "bncc":
            results.extend(
                await self._bncc.search(
                    query, grade=grade, subject=subject, system=system,
                    bloom_level=bloom_level,
                )
            )

        if system is None or system.lower() in ("ccss", "ccss_ela", "ngss"):
            results.extend(
                await self._us.search(
                    query, grade=grade, subject=subject, system=system,
                    bloom_level=bloom_level,
                )
            )

        return results

    async def get_by_code(self, code: str) -> CurriculumObjective | None:
        """Look up an objective by exact code in any system."""
        result = await self._bncc.get_by_code(code)
        if result is not None:
            return result
        return await self._us.get_by_code(code)

    async def list_standards(self, *, system: str | None = None) -> list[str]:
        """List all standard codes, optionally filtered by system."""
        codes: list[str] = []

        if system is None or system.lower() == "bncc":
            codes.extend(await self._bncc.list_standards(system=system))

        if system is None or system.lower() in ("ccss", "ccss_ela", "ngss"):
            codes.extend(await self._us.list_standards(system=system))

        return codes
