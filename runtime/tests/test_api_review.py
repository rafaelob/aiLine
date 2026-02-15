"""Tests for the HITL Review endpoints in the /plans router.

Covers:
- POST /plans/{plan_id}/review — submit a teacher review
- GET  /plans/{plan_id}/review — get review status
- GET  /plans/pending-review — list pending reviews
- GET  /plans/{run_id}/scorecard — get transformation scorecard

Verifies: success, not found (404), invalid status (422), unauthenticated (401).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.api.app import create_app
from ailine_runtime.shared.config import Settings

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_TEACHER_ID = "teacher-review-001"
_AUTH_HEADERS = {"X-Teacher-ID": _TEACHER_ID}


@pytest.fixture()
def app(settings: Settings, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AILINE_DEV_MODE", "true")
    # Reset singletons so tests start clean
    import ailine_runtime.shared.review_store as rs
    import ailine_runtime.shared.trace_store as ts

    rs._store = None
    ts._store = None
    return create_app(settings=settings)


@pytest.fixture()
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers=_AUTH_HEADERS,
    ) as c:
        yield c


@pytest.fixture()
async def unauthenticated_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Client without authentication headers."""
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# POST /plans/{plan_id}/review — submit review
# ---------------------------------------------------------------------------


async def test_submit_review_approved(client: AsyncClient) -> None:
    """Submit an 'approved' review for a plan."""
    resp = await client.post(
        "/plans/plan-001/review",
        json={"status": "approved", "notes": "Looks great!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan_id"] == "plan-001"
    assert body["status"] == "approved"
    assert body["notes"] == "Looks great!"
    assert body["approved_at"] is not None
    assert body["teacher_id"] == _TEACHER_ID


async def test_submit_review_rejected(client: AsyncClient) -> None:
    """Submit a 'rejected' review for a plan."""
    resp = await client.post(
        "/plans/plan-002/review",
        json={"status": "rejected", "notes": "Needs more detail."},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "rejected"
    assert body["approved_at"] is not None


async def test_submit_review_needs_revision(client: AsyncClient) -> None:
    """Submit a 'needs_revision' review for a plan."""
    resp = await client.post(
        "/plans/plan-003/review",
        json={"status": "needs_revision", "notes": "Adjust step 3."},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "needs_revision"


async def test_submit_review_invalid_status(client: AsyncClient) -> None:
    """Invalid review status returns 422."""
    resp = await client.post(
        "/plans/plan-004/review",
        json={"status": "invalid_status", "notes": ""},
    )
    assert resp.status_code == 422


async def test_submit_review_missing_status(client: AsyncClient) -> None:
    """Missing required 'status' field returns 422."""
    resp = await client.post(
        "/plans/plan-005/review",
        json={"notes": "No status field."},
    )
    assert resp.status_code == 422


async def test_submit_review_update_existing(client: AsyncClient) -> None:
    """Submitting a review twice updates the existing review."""
    # First review
    resp1 = await client.post(
        "/plans/plan-010/review",
        json={"status": "needs_revision", "notes": "First pass."},
    )
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "needs_revision"

    # Update to approved
    resp2 = await client.post(
        "/plans/plan-010/review",
        json={"status": "approved", "notes": "Revised and approved."},
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "approved"
    assert resp2.json()["notes"] == "Revised and approved."


async def test_submit_review_unauthenticated(unauthenticated_client: AsyncClient) -> None:
    """Unauthenticated review submission returns 401."""
    resp = await unauthenticated_client.post(
        "/plans/plan-006/review",
        json={"status": "approved"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /plans/{plan_id}/review — get review status
# ---------------------------------------------------------------------------


async def test_get_review_success(client: AsyncClient) -> None:
    """Get review status for a plan with an existing review."""
    # Create a review first
    await client.post(
        "/plans/plan-020/review",
        json={"status": "approved", "notes": "LGTM"},
    )

    resp = await client.get("/plans/plan-020/review")
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan_id"] == "plan-020"
    assert body["status"] == "approved"


async def test_get_review_not_found(client: AsyncClient) -> None:
    """Get review for a plan with no review returns 404."""
    resp = await client.get("/plans/nonexistent-plan/review")
    assert resp.status_code == 404


async def test_get_review_unauthenticated(unauthenticated_client: AsyncClient) -> None:
    """Unauthenticated request returns 401."""
    resp = await unauthenticated_client.get("/plans/any-plan/review")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /plans/pending-review — list pending reviews
# ---------------------------------------------------------------------------


async def test_pending_review_empty(client: AsyncClient) -> None:
    """Pending reviews with no entries returns empty list."""
    resp = await client.get("/plans/pending-review")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_pending_review_with_entries(client: AsyncClient) -> None:
    """Pending reviews returns plans with pending_review or draft status."""
    # Create a review (auto-creates with pending_review status initially)
    from ailine_runtime.shared.review_store import get_review_store

    store = get_review_store()
    store.create_review("plan-pending-1", _TEACHER_ID)
    store.create_review("plan-pending-2", _TEACHER_ID)

    resp = await client.get("/plans/pending-review")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    plan_ids = {r["plan_id"] for r in body}
    assert "plan-pending-1" in plan_ids
    assert "plan-pending-2" in plan_ids


async def test_pending_review_excludes_approved(client: AsyncClient) -> None:
    """Approved reviews are not included in pending list."""
    from ailine_runtime.domain.entities.plan import ReviewStatus
    from ailine_runtime.shared.review_store import get_review_store

    store = get_review_store()
    store.create_review("plan-approved-1", _TEACHER_ID)
    store.update_review("plan-approved-1", ReviewStatus.APPROVED, "Done")

    resp = await client.get("/plans/pending-review")
    assert resp.status_code == 200
    # The approved plan should not appear
    plan_ids = {r["plan_id"] for r in resp.json()}
    assert "plan-approved-1" not in plan_ids


async def test_pending_review_unauthenticated(unauthenticated_client: AsyncClient) -> None:
    """Unauthenticated request returns 401."""
    resp = await unauthenticated_client.get("/plans/pending-review")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /plans/{run_id}/scorecard — get transformation scorecard
# ---------------------------------------------------------------------------


async def test_scorecard_success(client: AsyncClient) -> None:
    """Get scorecard for a completed run with a scorecard."""
    from ailine_runtime.shared.trace_store import get_trace_store

    trace_store = get_trace_store()
    await trace_store.get_or_create("run-scorecard-001", teacher_id=_TEACHER_ID)
    await trace_store.update_run(
        "run-scorecard-001",
        status="completed",
        scorecard={
            "quality_score": 92,
            "model_used": "gemini-3-pro-preview",
            "time_saved_estimate": "~2 hours",
        },
    )

    resp = await client.get("/plans/run-scorecard-001/scorecard")
    assert resp.status_code == 200
    body = resp.json()
    assert body["quality_score"] == 92
    assert body["model_used"] == "gemini-3-pro-preview"


async def test_scorecard_run_not_found(client: AsyncClient) -> None:
    """Scorecard for a non-existent run returns 404."""
    resp = await client.get("/plans/nonexistent-run/scorecard")
    assert resp.status_code == 404


async def test_scorecard_not_yet_available(client: AsyncClient) -> None:
    """Scorecard for a run without scorecard data returns 404."""
    from ailine_runtime.shared.trace_store import get_trace_store

    trace_store = get_trace_store()
    await trace_store.get_or_create("run-no-scorecard", teacher_id=_TEACHER_ID)

    resp = await client.get("/plans/run-no-scorecard/scorecard")
    assert resp.status_code == 404


async def test_scorecard_unauthenticated(unauthenticated_client: AsyncClient) -> None:
    """Unauthenticated request returns 401."""
    resp = await unauthenticated_client.get("/plans/any-run/scorecard")
    assert resp.status_code == 401
