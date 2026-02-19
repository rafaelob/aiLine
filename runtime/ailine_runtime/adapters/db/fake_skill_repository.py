"""In-memory fake skill repository for unit tests (F-175).

Same interface as PostgresSkillRepository but backed by a dict.
"""

from __future__ import annotations

from uuid_utils import uuid7

from ailine_runtime.domain.entities.skill import Skill


class FakeSkillRepository:
    """In-memory skill repository for testing without a database."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
        self._ratings: dict[str, dict[str, int]] = {}  # slug -> {user_id: score}

    # --- CRUD ---

    async def get_by_slug(self, slug: str) -> Skill | None:
        skill = self._skills.get(slug)
        if skill and skill.is_active:
            return skill
        return None

    async def list_all(
        self, *, active_only: bool = True, system_only: bool = False
    ) -> list[Skill]:
        result = []
        for s in self._skills.values():
            if active_only and not s.is_active:
                continue
            if system_only and not s.is_system:
                continue
            result.append(s)
        return sorted(result, key=lambda s: s.slug)

    async def create(
        self,
        skill: Skill,
        *,
        teacher_id: str | None = None,
        is_system: bool = False,
    ) -> str:
        new_id = str(uuid7())
        stored = skill.model_copy(
            update={
                "id": new_id,
                "teacher_id": teacher_id,
                "is_system": is_system,
                "version": 1,
            }
        )
        self._skills[skill.slug] = stored
        return new_id

    async def update(
        self,
        slug: str,
        *,
        instructions_md: str | None = None,
        description: str | None = None,
        metadata: dict[str, str] | None = None,
        change_summary: str = "",
    ) -> None:
        skill = self._skills.get(slug)
        if skill is None or not skill.is_active:
            return
        updates: dict[str, object] = {"version": skill.version + 1}
        if instructions_md is not None:
            updates["instructions_md"] = instructions_md
        if description is not None:
            updates["description"] = description
        if metadata is not None:
            updates["metadata"] = metadata
        self._skills[slug] = skill.model_copy(update=updates)

    async def soft_delete(self, slug: str) -> None:
        skill = self._skills.get(slug)
        if skill:
            self._skills[slug] = skill.model_copy(update={"is_active": False})

    # --- Search ---

    async def search_by_text(
        self, query: str, *, limit: int = 10
    ) -> list[Skill]:
        q = query.lower()
        results = [
            s
            for s in self._skills.values()
            if s.is_active and (q in s.slug.lower() or q in s.description.lower())
        ]
        return sorted(results, key=lambda s: s.slug)[:limit]

    async def search_similar(
        self, embedding: list[float], *, limit: int = 5
    ) -> list[Skill]:
        # Fake: return all active skills (no vector math)
        return [s for s in self._skills.values() if s.is_active][:limit]

    # --- Teacher-specific ---

    async def list_by_teacher(self, teacher_id: str) -> list[Skill]:
        return sorted(
            [
                s
                for s in self._skills.values()
                if s.teacher_id == teacher_id and s.is_active
            ],
            key=lambda s: s.slug,
        )

    async def fork(self, source_slug: str, *, teacher_id: str) -> str:
        source = self._skills.get(source_slug)
        if source is None or not source.is_active:
            msg = f"Skill '{source_slug}' not found or inactive"
            raise ValueError(msg)

        # Generate unique forked slug with counter suffix on collision
        base_slug = f"{source.slug}-fork"
        forked_slug = base_slug
        counter = 1
        while forked_slug in self._skills:
            counter += 1
            forked_slug = f"{base_slug}-{counter}"

        new_id = str(uuid7())
        forked = source.model_copy(
            update={
                "id": new_id,
                "slug": forked_slug,
                "teacher_id": teacher_id,
                "forked_from_id": source.id,
                "is_system": False,
                "version": 1,
            }
        )
        self._skills[forked_slug] = forked
        return new_id

    # --- Ratings ---

    async def rate(
        self,
        slug: str,
        *,
        user_id: str,
        score: int,
        comment: str = "",
    ) -> None:
        skill = self._skills.get(slug)
        if skill is None:
            return
        if slug not in self._ratings:
            self._ratings[slug] = {}
        self._ratings[slug][user_id] = score

        ratings = self._ratings[slug]
        avg = sum(ratings.values()) / len(ratings)
        self._skills[slug] = skill.model_copy(
            update={
                "avg_rating": avg,
                "rating_count": len(ratings),
            }
        )

    # --- Embedding ---

    async def update_embedding(
        self, slug: str, embedding: list[float]
    ) -> None:
        # No-op for in-memory fake
        pass
