"""Tests for the HITL Tutor Transcript and Flag endpoints.

Covers:
- GET  /tutors/{tutor_id}/sessions/{session_id}/transcript — get full transcript
- POST /tutors/{tutor_id}/sessions/{session_id}/flag — flag a turn

Verifies: success, turn_index out of range (422), session not found (404),
tutor not found (404), session/tutor mismatch (400), unauthenticated (401).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.api.app import create_app
from ailine_runtime.domain.entities.tutor import (
    LearnerProfile,
    TutorAgentSpec,
    TutorMaterialsScope,
    TutorMessage,
    TutorPersona,
    TutorSession,
)
from ailine_runtime.shared.config import Settings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TEACHER_ID = "teacher-tutor-test-001"
_AUTH_HEADERS = {"X-Teacher-ID": _TEACHER_ID}
_TUTOR_ID = "tutor-transcript-001"
_SESSION_ID = "session-transcript-001"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tutor_spec(
    tutor_id: str = _TUTOR_ID,
    teacher_id: str = _TEACHER_ID,
) -> TutorAgentSpec:
    """Create a minimal TutorAgentSpec for testing."""
    return TutorAgentSpec(
        tutor_id=tutor_id,
        created_at=datetime.now(UTC).isoformat(),
        teacher_id=teacher_id,
        subject="Matematica",
        grade="6o ano",
        standard="BNCC",
        style="socratic",
        tone="calmo, paciente",
        student_profile=LearnerProfile(name="Aluno Teste"),
        materials_scope=TutorMaterialsScope(
            teacher_id=teacher_id,
            subject="Matematica",
        ),
        persona=TutorPersona(
            system_prompt="Voce e um tutor de matematica.",
            response_contract="json",
        ),
    )


def _make_session(
    session_id: str = _SESSION_ID,
    tutor_id: str = _TUTOR_ID,
    messages: list[TutorMessage] | None = None,
) -> TutorSession:
    """Create a TutorSession with sample messages."""
    now = datetime.now(UTC).isoformat()
    default_messages = [
        TutorMessage(role="user", content="O que sao fracoes?", created_at=now),
        TutorMessage(
            role="assistant",
            content="Fracoes representam partes de um todo.",
            created_at=now,
        ),
        TutorMessage(role="user", content="Me de um exemplo.", created_at=now),
        TutorMessage(
            role="assistant",
            content="Imagine uma pizza dividida em 8 fatias.",
            created_at=now,
        ),
    ]
    return TutorSession(
        session_id=session_id,
        tutor_id=tutor_id,
        created_at=now,
        messages=messages if messages is not None else default_messages,
    )


def _persist_tutor_spec(store_dir: Path, spec: TutorAgentSpec) -> None:
    """Write a TutorAgentSpec to the local store."""
    tutors_dir = store_dir / "tutors"
    tutors_dir.mkdir(parents=True, exist_ok=True)
    path = tutors_dir / f"{spec.tutor_id}.json"
    path.write_text(spec.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")


def _persist_session(store_dir: Path, session: TutorSession) -> None:
    """Write a TutorSession to the local store."""
    sessions_dir = store_dir / "tutor_sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    path = sessions_dir / f"{session.session_id}.json"
    path.write_text(session.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def local_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up a temporary local store with test data."""
    store_dir = tmp_path / "local_store"
    store_dir.mkdir()
    monkeypatch.setenv("AILINE_LOCAL_STORE", str(store_dir))

    # Reset review store singleton
    import ailine_runtime.shared.review_store as rs

    rs._store = None

    return store_dir


@pytest.fixture()
def app(settings: Settings, monkeypatch: pytest.MonkeyPatch, local_store: Path):
    monkeypatch.setenv("AILINE_DEV_MODE", "true")
    return create_app(settings=settings)


@pytest.fixture()
def seeded_store(local_store: Path) -> Path:
    """Persist a tutor spec and session to the local store."""
    spec = _make_tutor_spec()
    _persist_tutor_spec(local_store, spec)

    session = _make_session()
    _persist_session(local_store, session)

    return local_store


@pytest.fixture()
async def client(app, seeded_store: Path) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers=_AUTH_HEADERS,
    ) as c:
        yield c


@pytest.fixture()
async def unauthenticated_client(app, seeded_store: Path) -> AsyncGenerator[AsyncClient, None]:
    """Client without authentication headers."""
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# GET /tutors/{tutor_id}/sessions/{session_id}/transcript
# ---------------------------------------------------------------------------


async def test_transcript_success(client: AsyncClient) -> None:
    """Get transcript for a valid tutor session."""
    resp = await client.get(f"/tutors/{_TUTOR_ID}/sessions/{_SESSION_ID}/transcript")
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == _SESSION_ID
    assert body["tutor_id"] == _TUTOR_ID
    assert len(body["messages"]) == 4
    assert body["messages"][0]["role"] == "user"
    assert body["messages"][1]["role"] == "assistant"
    assert isinstance(body["flags"], list)
    assert "created_at" in body


async def test_transcript_tutor_not_found(client: AsyncClient) -> None:
    """Transcript for a non-existent tutor returns 404."""
    resp = await client.get(f"/tutors/nonexistent-tutor/sessions/{_SESSION_ID}/transcript")
    assert resp.status_code == 404


async def test_transcript_session_not_found(client: AsyncClient) -> None:
    """Transcript for a non-existent session returns 404."""
    resp = await client.get(f"/tutors/{_TUTOR_ID}/sessions/nonexistent-session/transcript")
    assert resp.status_code == 404


async def test_transcript_session_tutor_mismatch(
    client: AsyncClient,
    local_store: Path,
) -> None:
    """Transcript with session belonging to a different tutor returns 400."""
    # Create a session belonging to a different tutor
    other_session = _make_session(
        session_id="session-other-tutor",
        tutor_id="some-other-tutor",
    )
    _persist_session(local_store, other_session)

    resp = await client.get(f"/tutors/{_TUTOR_ID}/sessions/session-other-tutor/transcript")
    assert resp.status_code == 400


async def test_transcript_unauthenticated(unauthenticated_client: AsyncClient) -> None:
    """Unauthenticated transcript request returns 401."""
    resp = await unauthenticated_client.get(f"/tutors/{_TUTOR_ID}/sessions/{_SESSION_ID}/transcript")
    assert resp.status_code == 401


async def test_transcript_wrong_tenant(
    app,
    seeded_store: Path,
) -> None:
    """Teacher who does not own the tutor gets 403."""
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-Teacher-ID": "another-teacher"},
    ) as other_client:
        resp = await other_client.get(f"/tutors/{_TUTOR_ID}/sessions/{_SESSION_ID}/transcript")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /tutors/{tutor_id}/sessions/{session_id}/flag
# ---------------------------------------------------------------------------


async def test_flag_turn_success(client: AsyncClient) -> None:
    """Flag a valid turn in the conversation."""
    resp = await client.post(
        f"/tutors/{_TUTOR_ID}/sessions/{_SESSION_ID}/flag",
        json={"turn_index": 1, "reason": "Resposta pode ser confusa."},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == _SESSION_ID
    assert body["turn_index"] == 1
    assert body["reason"] == "Resposta pode ser confusa."
    assert body["teacher_id"] == _TEACHER_ID
    assert "flag_id" in body
    assert "created_at" in body


async def test_flag_turn_index_zero(client: AsyncClient) -> None:
    """Flagging the first turn (index 0) works."""
    resp = await client.post(
        f"/tutors/{_TUTOR_ID}/sessions/{_SESSION_ID}/flag",
        json={"turn_index": 0, "reason": ""},
    )
    assert resp.status_code == 200
    assert resp.json()["turn_index"] == 0


async def test_flag_turn_index_out_of_range(client: AsyncClient) -> None:
    """Flagging a turn_index beyond message count returns 422."""
    resp = await client.post(
        f"/tutors/{_TUTOR_ID}/sessions/{_SESSION_ID}/flag",
        json={"turn_index": 99, "reason": "This index does not exist."},
    )
    assert resp.status_code == 422


async def test_flag_negative_turn_index(client: AsyncClient) -> None:
    """Negative turn_index fails validation (ge=0)."""
    resp = await client.post(
        f"/tutors/{_TUTOR_ID}/sessions/{_SESSION_ID}/flag",
        json={"turn_index": -1, "reason": "Negative."},
    )
    assert resp.status_code == 422


async def test_flag_missing_turn_index(client: AsyncClient) -> None:
    """Missing turn_index field returns 422."""
    resp = await client.post(
        f"/tutors/{_TUTOR_ID}/sessions/{_SESSION_ID}/flag",
        json={"reason": "No turn_index."},
    )
    assert resp.status_code == 422


async def test_flag_tutor_not_found(client: AsyncClient) -> None:
    """Flag on a non-existent tutor returns 404."""
    resp = await client.post(
        f"/tutors/nonexistent-tutor/sessions/{_SESSION_ID}/flag",
        json={"turn_index": 0, "reason": "Test."},
    )
    assert resp.status_code == 404


async def test_flag_session_not_found(client: AsyncClient) -> None:
    """Flag on a non-existent session returns 404."""
    resp = await client.post(
        f"/tutors/{_TUTOR_ID}/sessions/nonexistent-session/flag",
        json={"turn_index": 0, "reason": "Test."},
    )
    assert resp.status_code == 404


async def test_flag_session_tutor_mismatch(
    client: AsyncClient,
    local_store: Path,
) -> None:
    """Flag with session belonging to a different tutor returns 400."""
    other_session = _make_session(
        session_id="session-mismatch-flag",
        tutor_id="some-other-tutor",
    )
    _persist_session(local_store, other_session)

    resp = await client.post(
        f"/tutors/{_TUTOR_ID}/sessions/session-mismatch-flag/flag",
        json={"turn_index": 0, "reason": "Test."},
    )
    assert resp.status_code == 400


async def test_flag_unauthenticated(unauthenticated_client: AsyncClient) -> None:
    """Unauthenticated flag request returns 401."""
    resp = await unauthenticated_client.post(
        f"/tutors/{_TUTOR_ID}/sessions/{_SESSION_ID}/flag",
        json={"turn_index": 0, "reason": "Test."},
    )
    assert resp.status_code == 401


async def test_flag_wrong_tenant(
    app,
    seeded_store: Path,
) -> None:
    """Teacher who does not own the tutor gets 403 on flag."""
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-Teacher-ID": "another-teacher"},
    ) as other_client:
        resp = await other_client.post(
            f"/tutors/{_TUTOR_ID}/sessions/{_SESSION_ID}/flag",
            json={"turn_index": 0, "reason": "Not my tutor."},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Transcript includes flags
# ---------------------------------------------------------------------------


async def test_transcript_includes_flags(client: AsyncClient) -> None:
    """After flagging a turn, the transcript includes the flag."""
    # Flag a turn
    await client.post(
        f"/tutors/{_TUTOR_ID}/sessions/{_SESSION_ID}/flag",
        json={"turn_index": 1, "reason": "Resposta imprecisa."},
    )

    # Get transcript
    resp = await client.get(f"/tutors/{_TUTOR_ID}/sessions/{_SESSION_ID}/transcript")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["flags"]) >= 1
    assert body["flags"][0]["turn_index"] == 1
    assert body["flags"][0]["reason"] == "Resposta imprecisa."
