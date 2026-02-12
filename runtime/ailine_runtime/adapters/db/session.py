"""Async SQLAlchemy session factory.

Creates a configured async engine and session maker per ADR-052:
- pool_size=5, max_overflow=5
- pool_pre_ping=True for connection health
- expire_on_commit=False to avoid lazy-load issues after commit
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ...shared.config import DatabaseConfig


def create_engine(db_config: DatabaseConfig) -> AsyncEngine:
    """Create an async engine from database configuration.

    For SQLite (aiosqlite), pool arguments are not applicable and
    are therefore omitted.

    Args:
        db_config: Database configuration with url, pool_size, echo.

    Returns:
        Configured AsyncEngine.
    """
    is_sqlite = db_config.url.startswith("sqlite")
    kwargs: dict = {
        "echo": db_config.echo,
    }
    if not is_sqlite:
        kwargs.update(
            pool_size=db_config.pool_size,
            max_overflow=db_config.max_overflow,
            pool_pre_ping=True,
        )
    return create_async_engine(db_config.url, **kwargs)


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Build an async session factory bound to the given engine.

    Args:
        engine: The AsyncEngine to bind sessions to.

    Returns:
        An async_sessionmaker configured with expire_on_commit=False.
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
