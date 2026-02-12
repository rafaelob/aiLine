"""Port: curriculum standards providers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..entities.curriculum import CurriculumObjective


@runtime_checkable
class CurriculumProvider(Protocol):
    """Protocol for curriculum standards providers."""

    async def search(
        self,
        query: str,
        *,
        grade: str | None = None,
        subject: str | None = None,
        system: str | None = None,
    ) -> list[CurriculumObjective]: ...

    async def get_by_code(self, code: str) -> CurriculumObjective | None: ...

    async def list_standards(self, *, system: str | None = None) -> list[str]: ...
