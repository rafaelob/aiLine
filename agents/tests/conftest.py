"""Shared test fixtures for ailine_agents test suite.

Global guard: disables real model requests so tests never call LLM APIs.
A dummy ANTHROPIC_API_KEY is set so Pydantic AI can instantiate the provider
object without error (no real calls are made thanks to ALLOW_MODEL_REQUESTS).

live_llm tests temporarily re-enable ALLOW_MODEL_REQUESTS and use real keys.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import pydantic_ai.models
import pytest

from ailine_agents.deps import AgentDeps

# ------------------------------------------------------------------
# Load .env so live_llm tests pick up real API keys
# ------------------------------------------------------------------
try:
    from dotenv import load_dotenv

    _env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if _env_path.is_file():
        load_dotenv(_env_path, override=False)
except ImportError:
    pass

# ------------------------------------------------------------------
# Global safety: prevent any real LLM API requests during testing
# ------------------------------------------------------------------
pydantic_ai.models.ALLOW_MODEL_REQUESTS = False

# Set a dummy API key so the Anthropic provider can be instantiated.
# ALLOW_MODEL_REQUESTS=False prevents any actual HTTP calls.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-real")


@pytest.fixture()
def agent_deps() -> AgentDeps:
    """Minimal AgentDeps for unit testing (no real ports)."""
    return AgentDeps(
        teacher_id="test-teacher",
        run_id="test-run",
        subject="matematica",
    )


@pytest.fixture()
def mock_container() -> MagicMock:
    """A mock Container that satisfies AgentDepsFactory.from_container()."""
    container = MagicMock()
    container.llm = MagicMock()
    container.embeddings = MagicMock()
    container.vectorstore = MagicMock()
    container.event_bus = MagicMock()
    container.settings.default_variants = "standard_html,low_distraction_html"
    container.settings.max_refinement_iters = 2
    return container


@pytest.fixture()
def allow_model_requests():
    """Temporarily enable real model requests for live_llm tests."""
    pydantic_ai.models.ALLOW_MODEL_REQUESTS = True
    yield
    pydantic_ai.models.ALLOW_MODEL_REQUESTS = False


@pytest.fixture()
def live_agent_deps() -> AgentDeps:
    """AgentDeps for live_llm tests (real context)."""
    return AgentDeps(
        teacher_id="live-test-teacher",
        run_id="live-test-run",
        subject="Matematica",
    )
