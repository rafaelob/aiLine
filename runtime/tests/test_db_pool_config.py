"""Tests for FINDING-23: DB pool max_overflow configurable via settings."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from ailine_runtime.adapters.db.session import create_engine
from ailine_runtime.shared.config import DatabaseConfig


class TestDBPoolConfig:
    def test_default_pool_size(self):
        config = DatabaseConfig()
        assert config.pool_size == 10
        assert config.max_overflow == 10

    def test_custom_max_overflow(self):
        config = DatabaseConfig(max_overflow=20)
        assert config.max_overflow == 20

    def test_max_overflow_passed_to_engine(self):
        """Non-SQLite engine receives max_overflow from config."""
        config = DatabaseConfig(
            url="postgresql+asyncpg://user:pass@localhost/db",
            pool_size=3,
            max_overflow=7,
            echo=False,
        )
        mock_engine = MagicMock()
        with patch(
            "ailine_runtime.adapters.db.session.create_async_engine",
            return_value=mock_engine,
        ) as mock_create:
            create_engine(config)

        mock_create.assert_called_once_with(
            "postgresql+asyncpg://user:pass@localhost/db",
            echo=False,
            pool_size=3,
            max_overflow=7,
            pool_pre_ping=True,
        )

    def test_sqlite_ignores_pool_args(self):
        """SQLite engine does not receive pool_size or max_overflow."""
        config = DatabaseConfig(
            url="sqlite+aiosqlite:///:memory:",
            pool_size=10,
            max_overflow=20,
        )
        engine = create_engine(config)
        assert engine is not None
