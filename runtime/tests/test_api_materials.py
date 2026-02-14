"""Tests for the /materials API endpoints.

Uses a temporary local store to avoid polluting the filesystem.
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
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _auth(teacher_id: str) -> dict[str, str]:
    """Build dev-mode auth header for a given teacher."""
    return {"X-Teacher-ID": teacher_id}


# ---------------------------------------------------------------------------
# POST /materials
# ---------------------------------------------------------------------------


async def test_add_material(client: AsyncClient, tmp_local_store: Path) -> None:
    resp = await client.post(
        "/materials",
        json={
            "teacher_id": "teacher-001",
            "subject": "Matematica",
            "title": "Fracoes basicas",
            "content": "Texto sobre fracoes para 5o ano.",
            "tags": ["fracoes", "bncc"],
        },
        headers=_auth("teacher-001"),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["teacher_id"] == "teacher-001"
    assert body["subject"] == "Matematica"
    assert body["title"] == "Fracoes basicas"
    assert "material_id" in body
    assert body["material_id"]  # not empty


async def test_add_material_without_tags(client: AsyncClient, tmp_local_store: Path) -> None:
    resp = await client.post(
        "/materials",
        json={
            "teacher_id": "teacher-001",
            "subject": "Ciencias",
            "title": "Ecossistemas",
            "content": "Texto sobre ecossistemas.",
        },
        headers=_auth("teacher-001"),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["tags"] == []


async def test_add_material_missing_required_field(client: AsyncClient, tmp_local_store: Path) -> None:
    resp = await client.post(
        "/materials",
        json={
            "teacher_id": "teacher-001",
            # Missing subject, title, content
        },
        headers=_auth("teacher-001"),
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /materials
# ---------------------------------------------------------------------------


async def test_list_materials_empty(client: AsyncClient, tmp_local_store: Path) -> None:
    resp = await client.get("/materials", headers=_auth("teacher-001"))
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_materials_after_add(client: AsyncClient, tmp_local_store: Path) -> None:
    # Add a material (auth context determines teacher_id)
    await client.post(
        "/materials",
        json={
            "teacher_id": "teacher-002",
            "subject": "Historia",
            "title": "Revolucao Industrial",
            "content": "Texto sobre a revolucao industrial.",
            "tags": ["historia"],
        },
        headers=_auth("teacher-002"),
    )
    # List as same teacher
    resp = await client.get("/materials", headers=_auth("teacher-002"))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) >= 1
    assert any(m["title"] == "Revolucao Industrial" for m in body)


async def test_list_materials_filter_by_teacher(client: AsyncClient, tmp_local_store: Path) -> None:
    # Add materials for two teachers (auth context determines ownership)
    await client.post(
        "/materials",
        json={
            "teacher_id": "teacher-A",
            "subject": "Matematica",
            "title": "Material A",
            "content": "Content A",
        },
        headers=_auth("teacher-A"),
    )
    await client.post(
        "/materials",
        json={
            "teacher_id": "teacher-B",
            "subject": "Matematica",
            "title": "Material B",
            "content": "Content B",
        },
        headers=_auth("teacher-B"),
    )
    # List as teacher-A -- scoped via auth context
    resp = await client.get("/materials", headers=_auth("teacher-A"))
    assert resp.status_code == 200
    body = resp.json()
    assert all(m["teacher_id"] == "teacher-A" for m in body)


async def test_list_materials_filter_by_subject(client: AsyncClient, tmp_local_store: Path) -> None:
    await client.post(
        "/materials",
        json={
            "teacher_id": "teacher-C",
            "subject": "Portugues",
            "title": "Interpretacao",
            "content": "Texto interpretacao.",
        },
        headers=_auth("teacher-C"),
    )
    resp = await client.get(
        "/materials",
        params={"subject": "Portugues"},
        headers=_auth("teacher-C"),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) >= 1
    assert all(m["subject"] == "Portugues" for m in body)
