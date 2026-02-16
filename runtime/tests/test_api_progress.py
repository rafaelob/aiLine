"""Tests for the /progress API endpoints.

Covers:
- POST /progress/record — record student mastery progress
- GET  /progress/dashboard — class progress overview
- GET  /progress/student/{student_id} — student records

Verifies: success, invalid data (422), unauthenticated (401).
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

_AUTH_HEADERS = {"X-Teacher-ID": "teacher-progress-001"}


@pytest.fixture()
def app(settings: Settings, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AILINE_DEV_MODE", "true")
    # Reset the progress store singleton so tests start clean
    import ailine_runtime.shared.progress_store as ps

    ps._store = None
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
# POST /progress/record
# ---------------------------------------------------------------------------


async def test_record_progress_success(client: AsyncClient) -> None:
    """Record a valid progress entry and verify the response."""
    resp = await client.post(
        "/progress/record",
        json={
            "student_id": "student-001",
            "student_name": "Ana",
            "standard_code": "EF06MA01",
            "standard_description": "Fracoes",
            "mastery_level": "developing",
            "notes": "Progressing well.",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["student_id"] == "student-001"
    assert body["mastery_level"] == "developing"
    assert body["standard_code"] == "EF06MA01"
    assert body["session_count"] == 1
    assert "progress_id" in body


async def test_record_progress_update_existing(client: AsyncClient) -> None:
    """Recording progress for the same student+standard updates the entry."""
    payload = {
        "student_id": "student-002",
        "student_name": "Bruno",
        "standard_code": "EF06MA02",
        "mastery_level": "developing",
    }
    resp1 = await client.post("/progress/record", json=payload)
    assert resp1.status_code == 200
    assert resp1.json()["session_count"] == 1

    # Update to proficient
    payload["mastery_level"] = "proficient"
    resp2 = await client.post("/progress/record", json=payload)
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body2["mastery_level"] == "proficient"
    assert body2["session_count"] == 2


async def test_record_progress_invalid_mastery_level(client: AsyncClient) -> None:
    """Invalid mastery_level returns 422."""
    resp = await client.post(
        "/progress/record",
        json={
            "student_id": "student-001",
            "standard_code": "EF06MA01",
            "mastery_level": "invalid_level",
        },
    )
    assert resp.status_code == 422


async def test_record_progress_missing_required_fields(client: AsyncClient) -> None:
    """Missing required fields returns 422."""
    # Missing student_id
    resp = await client.post(
        "/progress/record",
        json={
            "standard_code": "EF06MA01",
            "mastery_level": "developing",
        },
    )
    assert resp.status_code == 422

    # Missing standard_code
    resp2 = await client.post(
        "/progress/record",
        json={
            "student_id": "student-001",
            "mastery_level": "developing",
        },
    )
    assert resp2.status_code == 422

    # Missing mastery_level
    resp3 = await client.post(
        "/progress/record",
        json={
            "student_id": "student-001",
            "standard_code": "EF06MA01",
        },
    )
    assert resp3.status_code == 422


async def test_record_progress_empty_student_id(client: AsyncClient) -> None:
    """Empty student_id fails validation (min_length=1)."""
    resp = await client.post(
        "/progress/record",
        json={
            "student_id": "",
            "standard_code": "EF06MA01",
            "mastery_level": "developing",
        },
    )
    assert resp.status_code == 422


async def test_record_progress_unauthenticated(
    unauthenticated_client: AsyncClient,
) -> None:
    """Unauthenticated request returns 401."""
    resp = await unauthenticated_client.post(
        "/progress/record",
        json={
            "student_id": "student-001",
            "standard_code": "EF06MA01",
            "mastery_level": "developing",
        },
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /progress/dashboard
# ---------------------------------------------------------------------------


async def test_dashboard_empty(client: AsyncClient) -> None:
    """Dashboard with no records returns empty summary."""
    resp = await client.get("/progress/dashboard")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_students"] == 0
    assert body["total_standards"] == 0
    assert body["teacher_id"] == "teacher-progress-001"


async def test_dashboard_with_records(client: AsyncClient) -> None:
    """Dashboard reflects recorded progress."""
    # Record two students on one standard
    await client.post(
        "/progress/record",
        json={
            "student_id": "s1",
            "student_name": "Ana",
            "standard_code": "EF06MA01",
            "mastery_level": "mastered",
        },
    )
    await client.post(
        "/progress/record",
        json={
            "student_id": "s2",
            "student_name": "Bruno",
            "standard_code": "EF06MA01",
            "mastery_level": "developing",
        },
    )

    resp = await client.get("/progress/dashboard")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_students"] == 2
    assert body["total_standards"] == 1
    assert body["mastery_distribution"]["mastered"] == 1
    assert body["mastery_distribution"]["developing"] == 1
    assert len(body["students"]) == 2
    assert len(body["standards"]) == 1


async def test_dashboard_unauthenticated(unauthenticated_client: AsyncClient) -> None:
    """Unauthenticated dashboard request returns 401."""
    resp = await unauthenticated_client.get("/progress/dashboard")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /progress/student/{student_id}
# ---------------------------------------------------------------------------


async def test_student_progress_success(client: AsyncClient) -> None:
    """Get progress records for a specific student."""
    await client.post(
        "/progress/record",
        json={
            "student_id": "s-detail",
            "student_name": "Carla",
            "standard_code": "EF06MA01",
            "mastery_level": "proficient",
        },
    )
    await client.post(
        "/progress/record",
        json={
            "student_id": "s-detail",
            "student_name": "Carla",
            "standard_code": "EF06MA02",
            "mastery_level": "developing",
        },
    )

    resp = await client.get("/progress/student/s-detail")
    assert resp.status_code == 200
    records = resp.json()
    assert len(records) == 2
    codes = {r["standard_code"] for r in records}
    assert codes == {"EF06MA01", "EF06MA02"}


async def test_student_progress_not_found(client: AsyncClient) -> None:
    """Student with no records returns 404."""
    resp = await client.get("/progress/student/nonexistent-student")
    assert resp.status_code == 404


async def test_student_progress_unauthenticated(
    unauthenticated_client: AsyncClient,
) -> None:
    """Unauthenticated request returns 401."""
    resp = await unauthenticated_client.get("/progress/student/any-student")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# All mastery levels
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "level",
    ["not_started", "developing", "proficient", "mastered"],
)
async def test_record_all_mastery_levels(client: AsyncClient, level: str) -> None:
    """All valid mastery levels are accepted."""
    resp = await client.post(
        "/progress/record",
        json={
            "student_id": f"student-{level}",
            "standard_code": "EF06MA01",
            "mastery_level": level,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["mastery_level"] == level
