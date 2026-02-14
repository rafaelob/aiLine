"""Tests for the /tutors API endpoints.

Uses a temporary local store to avoid filesystem pollution.
Tests tutor creation, retrieval, session management, and chat.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

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
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-Teacher-ID": "teacher-001"},
    ) as c:
        yield c


def _tutor_payload() -> dict:
    return {
        "teacher_id": "teacher-001",
        "subject": "Matematica",
        "grade": "6o ano",
        "standard": "BNCC",
        "style": "socratic",
        "tone": "calmo, paciente",
        "student_profile": {
            "name": "Aluno Teste",
            "age": 12,
            "needs": ["adhd"],
            "strengths": ["visual"],
            "language": "pt-BR",
        },
    }


# ---------------------------------------------------------------------------
# POST /tutors (create)
# ---------------------------------------------------------------------------


async def test_create_tutor(client: AsyncClient, tmp_local_store: Path) -> None:
    resp = await client.post("/tutors", json=_tutor_payload())
    assert resp.status_code == 200
    body = resp.json()
    assert "tutor_id" in body
    assert body["teacher_id"] == "teacher-001"
    assert body["subject"] == "Matematica"
    assert body["persona"]["system_prompt"]  # non-empty persona


async def test_create_tutor_with_accessibility_profile(client: AsyncClient, tmp_local_store: Path) -> None:
    payload = _tutor_payload()
    payload["class_accessibility_profile"] = {
        "needs": {"autism": True, "adhd": True},
        "ui_prefs": {"low_distraction": True},
    }
    resp = await client.post("/tutors", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "tutor_id" in body


async def test_create_tutor_missing_required_fields(client: AsyncClient, tmp_local_store: Path) -> None:
    resp = await client.post("/tutors", json={"teacher_id": "t1"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /tutors/{tutor_id}
# ---------------------------------------------------------------------------


async def test_get_tutor_found(client: AsyncClient, tmp_local_store: Path) -> None:
    create_resp = await client.post("/tutors", json=_tutor_payload())
    tutor_id = create_resp.json()["tutor_id"]

    resp = await client.get(f"/tutors/{tutor_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["tutor_id"] == tutor_id


async def test_get_tutor_not_found(client: AsyncClient, tmp_local_store: Path) -> None:
    resp = await client.get("/tutors/nonexistent-id")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /tutors/{tutor_id}/sessions
# ---------------------------------------------------------------------------


async def test_create_session(client: AsyncClient, tmp_local_store: Path) -> None:
    create_resp = await client.post("/tutors", json=_tutor_payload())
    tutor_id = create_resp.json()["tutor_id"]

    resp = await client.post(f"/tutors/{tutor_id}/sessions")
    assert resp.status_code == 200
    body = resp.json()
    assert "session_id" in body
    assert body["session_id"]


async def test_create_session_tutor_not_found(client: AsyncClient, tmp_local_store: Path) -> None:
    resp = await client.post("/tutors/nonexistent-id/sessions")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /tutors/{tutor_id}/chat
# ---------------------------------------------------------------------------


async def test_tutor_chat(client: AsyncClient, tmp_local_store: Path) -> None:
    # Create tutor
    create_resp = await client.post("/tutors", json=_tutor_payload())
    tutor_id = create_resp.json()["tutor_id"]

    # Create session
    session_resp = await client.post(f"/tutors/{tutor_id}/sessions")
    session_id = session_resp.json()["session_id"]

    # Send chat message
    resp = await client.post(
        f"/tutors/{tutor_id}/chat",
        json={"session_id": session_id, "message": "O que sao fracoes?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "validated" in body
    assert "session_id" in body
    assert body["session_id"] == session_id
    # validated output contains structured TutorTurnOutput fields
    validated = body["validated"]
    assert "answer_markdown" in validated


async def test_tutor_chat_session_not_found(client: AsyncClient, tmp_local_store: Path) -> None:
    create_resp = await client.post("/tutors", json=_tutor_payload())
    tutor_id = create_resp.json()["tutor_id"]

    resp = await client.post(
        f"/tutors/{tutor_id}/chat",
        json={"session_id": "nonexistent-session", "message": "Oi"},
    )
    assert resp.status_code == 404


async def test_tutor_chat_session_wrong_tutor(client: AsyncClient, tmp_local_store: Path) -> None:
    # Create tutor A
    resp_a = await client.post("/tutors", json=_tutor_payload())
    tutor_a = resp_a.json()["tutor_id"]

    # Create tutor B
    payload_b = _tutor_payload()
    payload_b["subject"] = "Ciencias"
    resp_b = await client.post("/tutors", json=payload_b)
    tutor_b = resp_b.json()["tutor_id"]

    # Create session for tutor A
    session_resp = await client.post(f"/tutors/{tutor_a}/sessions")
    session_id = session_resp.json()["session_id"]

    # Try to chat with tutor B using tutor A's session
    resp = await client.post(
        f"/tutors/{tutor_b}/chat",
        json={"session_id": session_id, "message": "Oi"},
    )
    assert resp.status_code == 400
