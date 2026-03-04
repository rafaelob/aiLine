"""Postgres-backed skill repository implementation (F-175).

Translates between domain ``Skill`` entities and ``SkillRow`` ORM models.
All writes go through the async session; reads use the ``select`` API.

Two implementations:
- ``PostgresSkillRepository``: bound to a single session (unit-of-work style).
- ``SessionFactorySkillRepository``: creates a session per method call,
  suitable for long-lived DI singletons (e.g., app-startup wiring).
"""

from __future__ import annotations

from collections.abc import Callable

import structlog
from sqlalchemy import func, select, text, update
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from ailine_runtime.adapters.db.models import (
    SkillRatingRow,
    SkillRow,
    SkillVersionRow,
)
from ailine_runtime.domain.entities.skill import Skill

_log = structlog.get_logger("ailine.db.skill_repository")


def _row_to_skill(row: SkillRow) -> Skill:
    """Map an ORM SkillRow to a domain Skill entity."""
    return Skill(
        id=row.id,
        slug=row.slug,
        description=row.description,
        instructions_md=row.instructions_md,
        metadata=row.metadata_json or {},
        license=row.license,
        compatibility=row.compatibility,
        allowed_tools=row.allowed_tools,
        teacher_id=row.teacher_id,
        forked_from_id=row.forked_from_id,
        is_active=row.is_active,
        is_system=row.is_system,
        version=row.version,
        avg_rating=row.avg_rating,
        rating_count=row.rating_count,
        created_at=str(row.created_at) if row.created_at else "",
        updated_at=str(row.updated_at) if row.updated_at else "",
    )


class PostgresSkillRepository:
    """Async PostgreSQL-backed skill repository.

    Uses the same session-per-request pattern as the other repositories.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- CRUD ---

    async def get_by_slug(
        self, slug: str, *, teacher_id: str | None = None
    ) -> Skill | None:
        """Look up a skill by slug.

        When ``teacher_id`` is given, searches teacher-owned skills first,
        then falls back to system skills (teacher_id IS NULL).
        Without ``teacher_id``, prefers system skills but falls back to
        any single matching skill (avoids MultipleResultsFound).
        """
        if teacher_id is not None:
            # Try teacher-owned first (unique due to uq_skills_teacher_slug)
            stmt = select(SkillRow).where(
                SkillRow.slug == slug,
                SkillRow.teacher_id == teacher_id,
                SkillRow.is_active.is_(True),
            )
            result = await self._session.execute(stmt)
            row = result.scalar_one_or_none()
            if row is not None:
                return _row_to_skill(row)

        # Prefer system skill (teacher_id IS NULL)
        stmt = select(SkillRow).where(
            SkillRow.slug == slug,
            SkillRow.teacher_id.is_(None),
            SkillRow.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is not None:
            return _row_to_skill(row)

        # Fallback: return any single match (use .first() to avoid
        # MultipleResultsFound when multiple teachers share the slug)
        stmt = select(SkillRow).where(
            SkillRow.slug == slug,
            SkillRow.is_active.is_(True),
        ).limit(1)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _row_to_skill(row) if row else None

    async def list_all(
        self, *, active_only: bool = True, system_only: bool = False
    ) -> list[Skill]:
        stmt = select(SkillRow)
        if active_only:
            stmt = stmt.where(SkillRow.is_active.is_(True))
        if system_only:
            stmt = stmt.where(SkillRow.is_system.is_(True))
        stmt = stmt.order_by(SkillRow.slug)
        result = await self._session.execute(stmt)
        return [_row_to_skill(r) for r in result.scalars().all()]

    async def create(
        self,
        skill: Skill,
        *,
        teacher_id: str | None = None,
        is_system: bool = False,
    ) -> str:
        row = SkillRow(
            slug=skill.slug,
            description=skill.description,
            instructions_md=skill.instructions_md,
            metadata_json=skill.metadata or {},
            license=skill.license,
            compatibility=skill.compatibility,
            allowed_tools=skill.allowed_tools,
            teacher_id=teacher_id,
            is_system=is_system,
            version=1,
        )
        self._session.add(row)
        await self._session.flush()

        # Create initial version snapshot
        v1 = SkillVersionRow(
            skill_id=row.id,
            version=1,
            instructions_md=skill.instructions_md,
            metadata_json=skill.metadata or {},
            change_summary="Initial version",
        )
        self._session.add(v1)
        await self._session.flush()
        return row.id

    async def update(
        self,
        slug: str,
        *,
        teacher_id: str | None = None,
        instructions_md: str | None = None,
        description: str | None = None,
        metadata: dict[str, str] | None = None,
        change_summary: str = "",
    ) -> None:
        stmt = select(SkillRow).where(
            SkillRow.slug == slug, SkillRow.is_active.is_(True)
        )
        if teacher_id is not None:
            stmt = stmt.where(SkillRow.teacher_id == teacher_id)
        else:
            stmt = stmt.where(SkillRow.teacher_id.is_(None))
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return

        new_version = row.version + 1
        if instructions_md is not None:
            row.instructions_md = instructions_md
        if description is not None:
            row.description = description
        if metadata is not None:
            row.metadata_json = metadata
        row.version = new_version

        version_row = SkillVersionRow(
            skill_id=row.id,
            version=new_version,
            instructions_md=row.instructions_md,
            metadata_json=row.metadata_json or {},
            change_summary=change_summary,
        )
        self._session.add(version_row)
        await self._session.flush()

    async def soft_delete(self, slug: str, *, teacher_id: str | None = None) -> None:
        stmt = update(SkillRow).where(SkillRow.slug == slug)
        if teacher_id is not None:
            stmt = stmt.where(SkillRow.teacher_id == teacher_id)
        else:
            stmt = stmt.where(SkillRow.teacher_id.is_(None))
        stmt = stmt.values(is_active=False)
        await self._session.execute(stmt)
        await self._session.flush()

    # --- Search ---

    async def search_by_text(
        self, query: str, *, limit: int = 10
    ) -> list[Skill]:
        # Escape LIKE wildcards to prevent query amplification.
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        stmt = (
            select(SkillRow)
            .where(
                SkillRow.is_active.is_(True),
                (SkillRow.slug.ilike(pattern, escape="\\"))
                | (SkillRow.description.ilike(pattern, escape="\\")),
            )
            .limit(limit)
            .order_by(SkillRow.slug)
        )
        result = await self._session.execute(stmt)
        return [_row_to_skill(r) for r in result.scalars().all()]

    async def search_similar(
        self, embedding: list[float], *, limit: int = 5
    ) -> list[Skill]:
        """pgvector cosine distance search -- requires Postgres.

        Falls back to empty list on non-Postgres backends or when the
        pgvector extension is not available.
        """
        try:
            sql = text(
                "SELECT id FROM skills "
                "WHERE is_active = true AND embedding IS NOT NULL "
                "ORDER BY embedding <=> cast(:emb AS vector) LIMIT :lim"
            )
            result = await self._session.execute(
                sql, {"emb": str(embedding), "lim": limit}
            )
            ids = [row[0] for row in result.fetchall()]
            if not ids:
                return []
            stmt = select(SkillRow).where(SkillRow.id.in_(ids))
            rows_result = await self._session.execute(stmt)
            return [_row_to_skill(r) for r in rows_result.scalars().all()]
        except (OperationalError, IntegrityError) as exc:
            _log.debug("skill.search_similar_unavailable", error=str(exc))
            return []

    # --- Teacher-specific ---

    async def list_by_teacher(self, teacher_id: str) -> list[Skill]:
        stmt = (
            select(SkillRow)
            .where(
                SkillRow.teacher_id == teacher_id,
                SkillRow.is_active.is_(True),
            )
            .order_by(SkillRow.slug)
        )
        result = await self._session.execute(stmt)
        return [_row_to_skill(r) for r in result.scalars().all()]

    async def fork(
        self, source_slug: str, *, teacher_id: str, source_teacher_id: str | None = None
    ) -> str:
        # Try source_teacher_id-scoped lookup first, fallback to system skill
        if source_teacher_id is not None:
            stmt = select(SkillRow).where(
                SkillRow.slug == source_slug,
                SkillRow.teacher_id == source_teacher_id,
                SkillRow.is_active.is_(True),
            )
            result = await self._session.execute(stmt)
            source = result.scalar_one_or_none()
        else:
            source = None

        if source is None:
            # Fallback to system skill (teacher_id IS NULL)
            stmt = select(SkillRow).where(
                SkillRow.slug == source_slug,
                SkillRow.teacher_id.is_(None),
                SkillRow.is_active.is_(True),
            )
            result = await self._session.execute(stmt)
            source = result.scalar_one_or_none()
        if source is None:
            msg = f"Skill '{source_slug}' not found or inactive"
            raise ValueError(msg)

        # Generate a unique forked slug with counter suffix on collision
        base_slug = f"{source.slug}-fork"
        forked_slug = base_slug
        counter = 1
        while True:
            check = select(SkillRow).where(
                SkillRow.slug == forked_slug,
                SkillRow.teacher_id == teacher_id,
            )
            exists = (await self._session.execute(check)).scalar_one_or_none()
            if exists is None:
                break
            counter += 1
            forked_slug = f"{base_slug}-{counter}"

        forked = SkillRow(
            slug=forked_slug,
            description=source.description,
            instructions_md=source.instructions_md,
            metadata_json=source.metadata_json or {},
            license=source.license,
            compatibility=source.compatibility,
            allowed_tools=source.allowed_tools,
            teacher_id=teacher_id,
            forked_from_id=source.id,
            is_system=False,
            version=1,
        )
        self._session.add(forked)
        await self._session.flush()

        v1 = SkillVersionRow(
            skill_id=forked.id,
            version=1,
            instructions_md=source.instructions_md,
            metadata_json=source.metadata_json or {},
            change_summary=f"Forked from {source.slug}",
        )
        self._session.add(v1)
        await self._session.flush()
        return forked.id

    # --- Ratings ---

    async def rate(
        self,
        slug: str,
        *,
        user_id: str,
        score: int,
        comment: str = "",
        teacher_id: str | None = None,
    ) -> None:
        # Resolve skill ID — filter by teacher_id to avoid ambiguity
        stmt = select(SkillRow).where(SkillRow.slug == slug)
        if teacher_id is not None:
            stmt = stmt.where(SkillRow.teacher_id == teacher_id)
        else:
            stmt = stmt.where(SkillRow.teacher_id.is_(None))
        result = await self._session.execute(stmt)
        skill_row = result.scalar_one_or_none()
        if skill_row is None:
            return

        # Check for existing rating
        existing_stmt = select(SkillRatingRow).where(
            SkillRatingRow.skill_id == skill_row.id,
            SkillRatingRow.user_id == user_id,
        )
        existing_result = await self._session.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()

        if existing:
            existing.score = score
            existing.comment = comment
        else:
            rating = SkillRatingRow(
                skill_id=skill_row.id,
                user_id=user_id,
                score=score,
                comment=comment,
            )
            self._session.add(rating)
        await self._session.flush()

        # Recalculate avg_rating and rating_count
        avg_stmt = select(
            func.avg(SkillRatingRow.score),
            func.count(SkillRatingRow.id),
        ).where(SkillRatingRow.skill_id == skill_row.id)
        avg_result = await self._session.execute(avg_stmt)
        avg_row = avg_result.one()
        skill_row.avg_rating = float(avg_row[0]) if avg_row[0] else 0.0
        skill_row.rating_count = avg_row[1]
        await self._session.flush()

    # --- Embedding ---

    async def update_embedding(
        self, slug: str, embedding: list[float], *, teacher_id: str | None = None
    ) -> None:
        try:
            if teacher_id is not None:
                sql = text(
                    "UPDATE skills SET embedding = cast(:emb AS vector) "
                    "WHERE slug = :slug AND teacher_id = :tid"
                )
                await self._session.execute(
                    sql, {"emb": str(embedding), "slug": slug, "tid": teacher_id}
                )
            else:
                sql = text(
                    "UPDATE skills SET embedding = cast(:emb AS vector) "
                    "WHERE slug = :slug AND teacher_id IS NULL"
                )
                await self._session.execute(
                    sql, {"emb": str(embedding), "slug": slug}
                )
            await self._session.flush()
        except (OperationalError, IntegrityError) as exc:
            _log.warning(
                "skill.update_embedding_failed", slug=slug, error=str(exc)
            )


class SessionFactorySkillRepository:
    """Skill repository that creates a session per method call.

    Wraps ``PostgresSkillRepository`` with automatic session lifecycle
    management. Suitable for long-lived DI singletons wired at startup.
    """

    def __init__(self, session_factory: Callable[..., AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_slug(
        self, slug: str, *, teacher_id: str | None = None
    ) -> Skill | None:
        async with self._session_factory() as session:
            repo = PostgresSkillRepository(session)
            return await repo.get_by_slug(slug, teacher_id=teacher_id)

    async def list_all(
        self, *, active_only: bool = True, system_only: bool = False
    ) -> list[Skill]:
        async with self._session_factory() as session:
            repo = PostgresSkillRepository(session)
            return await repo.list_all(active_only=active_only, system_only=system_only)

    async def create(
        self,
        skill: Skill,
        *,
        teacher_id: str | None = None,
        is_system: bool = False,
    ) -> str:
        async with self._session_factory() as session:
            repo = PostgresSkillRepository(session)
            result = await repo.create(skill, teacher_id=teacher_id, is_system=is_system)
            await session.commit()
            return result

    async def update(
        self,
        slug: str,
        *,
        teacher_id: str | None = None,
        instructions_md: str | None = None,
        description: str | None = None,
        metadata: dict[str, str] | None = None,
        change_summary: str = "",
    ) -> None:
        async with self._session_factory() as session:
            repo = PostgresSkillRepository(session)
            await repo.update(
                slug,
                teacher_id=teacher_id,
                instructions_md=instructions_md,
                description=description,
                metadata=metadata,
                change_summary=change_summary,
            )
            await session.commit()

    async def soft_delete(self, slug: str, *, teacher_id: str | None = None) -> None:
        async with self._session_factory() as session:
            repo = PostgresSkillRepository(session)
            await repo.soft_delete(slug, teacher_id=teacher_id)
            await session.commit()

    async def search_by_text(
        self, query: str, *, limit: int = 10
    ) -> list[Skill]:
        async with self._session_factory() as session:
            repo = PostgresSkillRepository(session)
            return await repo.search_by_text(query, limit=limit)

    async def search_similar(
        self, embedding: list[float], *, limit: int = 5
    ) -> list[Skill]:
        async with self._session_factory() as session:
            repo = PostgresSkillRepository(session)
            return await repo.search_similar(embedding, limit=limit)

    async def list_by_teacher(self, teacher_id: str) -> list[Skill]:
        async with self._session_factory() as session:
            repo = PostgresSkillRepository(session)
            return await repo.list_by_teacher(teacher_id)

    async def fork(
        self, source_slug: str, *, teacher_id: str, source_teacher_id: str | None = None
    ) -> str:
        async with self._session_factory() as session:
            repo = PostgresSkillRepository(session)
            result = await repo.fork(
                source_slug, teacher_id=teacher_id, source_teacher_id=source_teacher_id
            )
            await session.commit()
            return result

    async def rate(
        self,
        slug: str,
        *,
        user_id: str,
        score: int,
        comment: str = "",
        teacher_id: str | None = None,
    ) -> None:
        async with self._session_factory() as session:
            repo = PostgresSkillRepository(session)
            await repo.rate(
                slug, user_id=user_id, score=score, comment=comment, teacher_id=teacher_id
            )
            await session.commit()

    async def update_embedding(
        self, slug: str, embedding: list[float], *, teacher_id: str | None = None
    ) -> None:
        async with self._session_factory() as session:
            repo = PostgresSkillRepository(session)
            try:
                await repo.update_embedding(slug, embedding, teacher_id=teacher_id)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
