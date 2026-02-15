"""Tests for the /plans API endpoints.

The plan generation pipeline requires a LangGraph workflow, which depends
on several subsystems. For unit-level API tests we verify request validation
and basic endpoint reachability. The full pipeline E2E test is in a separate
file and requires @pytest.mark.live_llm or the full Docker stack.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.api.app import create_app
from ailine_runtime.shared.config import Settings


@pytest.fixture()
def app(settings: Settings, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AILINE_DEV_MODE", "true")
    return create_app(settings=settings)


@pytest.fixture()
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-Teacher-ID": "teacher-001"},
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# POST /plans/generate -- validation tests
# ---------------------------------------------------------------------------


async def test_plans_generate_missing_body(client: AsyncClient) -> None:
    resp = await client.post("/plans/generate")
    assert resp.status_code == 422


async def test_plans_generate_missing_run_id(client: AsyncClient) -> None:
    resp = await client.post(
        "/plans/generate",
        json={"user_prompt": "Create a lesson about fractions"},
    )
    assert resp.status_code == 422


async def test_plans_generate_missing_user_prompt(client: AsyncClient) -> None:
    resp = await client.post(
        "/plans/generate",
        json={"run_id": "test-run-001"},
    )
    assert resp.status_code == 422


async def test_plans_generate_accepts_valid_payload(client: AsyncClient) -> None:
    """Verify the endpoint accepts a valid payload.

    Note: The actual pipeline execution may fail due to missing workflow
    dependencies in test mode. We verify the payload is accepted (not 422)
    and tolerate runtime errors (500) in this isolated test.
    """
    resp = await client.post(
        "/plans/generate",
        json={
            "run_id": "test-run-001",
            "user_prompt": "Crie um plano sobre fracoes para 5o ano",
            "teacher_id": "teacher-001",
            "subject": "Matematica",
        },
    )
    # Either success or internal error (pipeline deps), but not validation error
    assert resp.status_code != 422


async def test_plans_generate_successful_execution(client: AsyncClient) -> None:
    """Cover line 44: successful workflow execution returns final_state."""
    from unittest.mock import AsyncMock, MagicMock, patch

    mock_workflow = MagicMock()
    mock_workflow.ainvoke = AsyncMock(
        return_value={
            "run_id": "test-run-success",
            "final": {"parsed": {"plan_id": "test", "score": 90}},
        }
    )

    mock_factory = MagicMock()
    mock_factory.from_container = MagicMock(return_value=MagicMock())

    with (
        patch(
            "ailine_runtime.api.routers.plans.build_plan_workflow",
            return_value=mock_workflow,
        ),
        patch(
            "ailine_runtime.api.routers.plans.AgentDepsFactory",
            mock_factory,
        ),
    ):
        resp = await client.post(
            "/plans/generate",
            json={
                "run_id": "test-run-success",
                "user_prompt": "Crie um plano sobre fracoes",
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["run_id"] == "test-run-success"
    assert "final" in body


async def test_plans_generate_with_accessibility_profile(client: AsyncClient) -> None:
    """Verify the endpoint accepts accessibility profile in the payload."""
    resp = await client.post(
        "/plans/generate",
        json={
            "run_id": "test-run-002",
            "user_prompt": "Plano inclusivo sobre ecossistemas",
            "teacher_id": "teacher-001",
            "class_accessibility_profile": {
                "needs": {"autism": True, "adhd": True},
                "ui_prefs": {"low_distraction": True},
            },
            "learner_profiles": [
                {"name": "Aluno A", "needs": ["visual"], "strengths": ["auditivo"]},
            ],
        },
    )
    assert resp.status_code != 422
