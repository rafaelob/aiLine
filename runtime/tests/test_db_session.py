"""Tests for adapters.db.session -- engine and session factory creation."""

from __future__ import annotations

from ailine_runtime.adapters.db.session import create_engine, create_session_factory
from ailine_runtime.shared.config import DatabaseConfig


class TestCreateEngine:
    def test_sqlite_engine(self):
        config = DatabaseConfig(url="sqlite+aiosqlite:///:memory:", echo=False)
        engine = create_engine(config)
        assert engine is not None
        assert str(engine.url) == "sqlite+aiosqlite:///:memory:"

    def test_sqlite_no_pool_args(self):
        """SQLite should not receive pool_size/max_overflow kwargs."""
        config = DatabaseConfig(url="sqlite+aiosqlite:///:memory:", pool_size=5)
        engine = create_engine(config)
        # Should not raise -- pool args are skipped for SQLite
        assert engine is not None


class TestCreateEngineNonSqlite:
    def test_non_sqlite_url_includes_pool_args(self):
        """Non-SQLite URLs pass pool_size, max_overflow, pool_pre_ping (line 38)."""
        from unittest.mock import MagicMock, patch

        config = DatabaseConfig(
            url="postgresql+asyncpg://user:pass@localhost:5432/testdb",
            pool_size=5,
            echo=False,
        )

        mock_engine = MagicMock()
        with patch(
            "ailine_runtime.adapters.db.session.create_async_engine",
            return_value=mock_engine,
        ) as mock_create:
            result = create_engine(config)

        mock_create.assert_called_once_with(
            "postgresql+asyncpg://user:pass@localhost:5432/testdb",
            echo=False,
            pool_size=5,
            max_overflow=5,
            pool_pre_ping=True,
        )
        assert result is mock_engine


class TestCreateSessionFactory:
    def test_returns_sessionmaker(self):
        config = DatabaseConfig(url="sqlite+aiosqlite:///:memory:")
        engine = create_engine(config)
        factory = create_session_factory(engine)
        assert factory is not None
        assert callable(factory)
