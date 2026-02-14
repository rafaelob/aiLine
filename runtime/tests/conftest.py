"""Shared test fixtures for AiLine runtime tests.

Provides:
- In-memory aiosqlite engine and session factory for DB tests
- FakeChatLLM fixture for testing without API keys
- Settings fixture with safe test defaults
- Temporary local store for material/tutor persistence
- Marker registration for ``live_llm`` (ADR-051)
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ailine_runtime.adapters.db.models import Base
from ailine_runtime.adapters.llm.fake_llm import FakeChatLLM
from ailine_runtime.shared.config import (
    DatabaseConfig,
    EmbeddingConfig,
    LLMConfig,
    RedisConfig,
    Settings,
)

# ---------------------------------------------------------------------------
# Marker registration (mirrors pyproject.toml for IDE / plugin discovery)
# ---------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers and load .env for live_llm tests."""
    config.addinivalue_line(
        "markers",
        "live_llm: marks tests that require real LLM API keys (deselect with '-m \"not live_llm\"')",
    )
    # Load .env so live_llm tests can pick up real API keys.
    try:
        from dotenv import load_dotenv

        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        if env_path.is_file():
            load_dotenv(env_path, override=False)
    except ImportError:
        pass

# ---------------------------------------------------------------------------
# Database fixtures (aiosqlite in-memory)
# ---------------------------------------------------------------------------


@pytest.fixture()
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create an in-memory aiosqlite engine with all tables."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture()
def session_factory(async_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Build an async session factory bound to the test engine."""
    return async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture()
async def session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    """Provide a single async session, rolled back after the test."""
    async with session_factory() as sess:
        yield sess
        await sess.rollback()


# ---------------------------------------------------------------------------
# FakeLLM fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_llm() -> FakeChatLLM:
    """Return a FakeChatLLM for tests that need an LLM without API keys."""
    return FakeChatLLM()


@pytest.fixture()
def fake_llm_with_responses() -> FakeChatLLM:
    """Return a FakeChatLLM with custom canned responses."""
    return FakeChatLLM(
        responses=[
            '{"answer_markdown": "Resposta de teste.", '
            '"step_by_step": ["Passo 1"], '
            '"check_for_understanding": ["Entendeu?"]}'
        ]
    )


# ---------------------------------------------------------------------------
# Settings fixture (safe defaults for tests)
# ---------------------------------------------------------------------------


@pytest.fixture()
def settings() -> Settings:
    """Return Settings configured for testing (no real API calls)."""
    return Settings(
        anthropic_api_key="fake-key-for-tests",
        openai_api_key="",
        google_api_key="",
        db=DatabaseConfig(url="sqlite+aiosqlite:///:memory:"),
        llm=LLMConfig(provider="fake", api_key="fake"),
        embedding=EmbeddingConfig(provider="gemini", api_key=""),
        redis=RedisConfig(url=""),
    )


# ---------------------------------------------------------------------------
# Temporary local store (auto-cleaned)
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_local_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set AILINE_LOCAL_STORE to a temp directory that is cleaned up after test."""
    store_dir = tmp_path / "local_store"
    store_dir.mkdir()
    monkeypatch.setenv("AILINE_LOCAL_STORE", str(store_dir))
    return store_dir
