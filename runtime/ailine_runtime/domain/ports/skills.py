"""Port: skill repository protocol for persistence and retrieval."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ailine_runtime.domain.entities.skill import Skill


@runtime_checkable
class SkillRepository(Protocol):
    """Port for skill persistence and retrieval.

    Implementations may be backed by PostgreSQL (production) or
    an in-memory dict (testing).
    """

    # --- CRUD ---

    async def get_by_slug(self, slug: str) -> Skill | None:
        """Retrieve a single active skill by slug."""
        ...

    async def list_all(
        self, *, active_only: bool = True, system_only: bool = False
    ) -> list[Skill]:
        """List all skills, optionally filtered."""
        ...

    async def create(
        self,
        skill: Skill,
        *,
        teacher_id: str | None = None,
        is_system: bool = False,
    ) -> str:
        """Create a new skill. Returns the generated ID."""
        ...

    async def update(
        self,
        slug: str,
        *,
        instructions_md: str | None = None,
        description: str | None = None,
        metadata: dict[str, str] | None = None,
        change_summary: str = "",
    ) -> None:
        """Update a skill (creates a new version)."""
        ...

    async def soft_delete(self, slug: str) -> None:
        """Soft-delete a skill (set is_active=False)."""
        ...

    # --- Search ---

    async def search_by_text(
        self, query: str, *, limit: int = 10
    ) -> list[Skill]:
        """Full-text search in slug + description."""
        ...

    async def search_similar(
        self, embedding: list[float], *, limit: int = 5
    ) -> list[Skill]:
        """Vector similarity search using pgvector."""
        ...

    # --- Teacher-specific ---

    async def list_by_teacher(self, teacher_id: str) -> list[Skill]:
        """List skills created by a specific teacher."""
        ...

    async def fork(self, source_slug: str, *, teacher_id: str) -> str:
        """Fork a skill to a teacher's collection. Returns new skill ID."""
        ...

    # --- Ratings ---

    async def rate(
        self, slug: str, *, user_id: str, score: int, comment: str = ""
    ) -> None:
        """Rate a skill (1-5). Upserts on re-rating."""
        ...

    # --- Embedding ---

    async def update_embedding(
        self, slug: str, embedding: list[float]
    ) -> None:
        """Update the pgvector embedding for a skill."""
        ...
