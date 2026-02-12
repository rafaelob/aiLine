"""Tests for the /materials API endpoints.

Uses a temporary local store to avoid polluting the filesystem.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.api.app import create_app
from ailine_runtime.shared.config import Settings


@pytest.fixture()
def app(settings: Settings):
    return create_app(settings=settings)


@pytest.fixture()
async def client(app) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


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
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /materials
# ---------------------------------------------------------------------------


async def test_list_materials_empty(client: AsyncClient, tmp_local_store: Path) -> None:
    resp = await client.get("/materials")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_materials_after_add(client: AsyncClient, tmp_local_store: Path) -> None:
    # Add a material
    await client.post(
        "/materials",
        json={
            "teacher_id": "teacher-002",
            "subject": "Historia",
            "title": "Revolucao Industrial",
            "content": "Texto sobre a revolucao industrial.",
            "tags": ["historia"],
        },
    )
    # List all
    resp = await client.get("/materials")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) >= 1
    assert any(m["title"] == "Revolucao Industrial" for m in body)


async def test_list_materials_filter_by_teacher(client: AsyncClient, tmp_local_store: Path) -> None:
    # Add materials for two teachers
    await client.post(
        "/materials",
        json={
            "teacher_id": "teacher-A",
            "subject": "Matematica",
            "title": "Material A",
            "content": "Content A",
        },
    )
    await client.post(
        "/materials",
        json={
            "teacher_id": "teacher-B",
            "subject": "Matematica",
            "title": "Material B",
            "content": "Content B",
        },
    )
    # Filter by teacher-A
    resp = await client.get("/materials", params={"teacher_id": "teacher-A"})
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
    )
    resp = await client.get("/materials", params={"teacher_id": "teacher-C", "subject": "Portugues"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) >= 1
    assert all(m["subject"] == "Portugues" for m in body)
