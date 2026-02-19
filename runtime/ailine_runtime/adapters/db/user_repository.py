"""PostgreSQL-backed user repository for auth endpoints.

Replaces the in-memory ``_users_store`` dict in auth.py with proper
database persistence via the UserRow ORM model.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from ailine_runtime.adapters.db.models import UserRow

_log = structlog.get_logger("ailine.db.user_repository")


def _ensure_id(row: UserRow) -> None:
    """Assign a UUID v7 if the row has no id (SQLAlchemy defaults don't fire outside a session)."""
    if row.id is None:
        row.id = str(uuid7())


@runtime_checkable
class UserRepository(Protocol):
    """Port for user persistence."""

    async def get_by_email(self, email: str) -> UserRow | None: ...
    async def get_by_id(self, user_id: str) -> UserRow | None: ...
    async def create(self, row: UserRow) -> None: ...


class PostgresUserRepository:
    """Async PostgreSQL-backed user repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> UserRow | None:
        stmt = select(UserRow).where(UserRow.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> UserRow | None:
        stmt = select(UserRow).where(UserRow.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, row: UserRow) -> None:
        self._session.add(row)
        await self._session.flush()


class InMemoryUserRepository:
    """In-memory user repository for dev/test usage.

    Wraps a dict keyed by email, matching the original auth.py behaviour.
    """

    def __init__(self) -> None:
        self._by_email: dict[str, UserRow] = {}
        self._by_id: dict[str, UserRow] = {}

    async def get_by_email(self, email: str) -> UserRow | None:
        return self._by_email.get(email)

    async def get_by_id(self, user_id: str) -> UserRow | None:
        return self._by_id.get(user_id)

    async def create(self, row: UserRow) -> None:
        _ensure_id(row)
        self._by_email[row.email] = row
        self._by_id[row.id] = row

    def seed_sync(self, row: UserRow) -> None:
        """Synchronous insert for startup seeding (before event loop)."""
        _ensure_id(row)
        self._by_email[row.email] = row
        self._by_id[row.id] = row

    def has_email(self, email: str) -> bool:
        """Synchronous check for startup seeding."""
        return email in self._by_email
