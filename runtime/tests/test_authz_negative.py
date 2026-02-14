"""Negative authorization tests (ADR-060).

Verifies that:
1. Unauthenticated requests to protected endpoints return 401.
2. Cross-tenant access is denied (403) or returns empty results.
3. Vector store tenant isolation prevents data leakage.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ailine_runtime.adapters.vectorstores.inmemory_store import InMemoryVectorStore
from ailine_runtime.api.app import create_app
from ailine_runtime.app.authz import (
    AuthorizationError,
    can_observe,
    require_authenticated,
    require_tenant_access,
)
from ailine_runtime.shared.config import Settings
from ailine_runtime.shared.tenant import set_tenant_id

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_A = "teacher-alpha"
TENANT_B = "teacher-beta"


def _test_settings() -> Settings:
    return Settings(
        anthropic_api_key="",
        openai_api_key="",
        google_api_key="",
    )


@pytest.fixture()
def dev_mode_app(monkeypatch: pytest.MonkeyPatch):
    """Create a test app with dev mode enabled."""
    monkeypatch.setenv("AILINE_DEV_MODE", "true")
    app = create_app(_test_settings())
    yield app
    monkeypatch.delenv("AILINE_DEV_MODE", raising=False)


@pytest.fixture()
def no_auth_app(monkeypatch: pytest.MonkeyPatch):
    """Create a test app with dev mode OFF (no X-Teacher-ID bypass)."""
    monkeypatch.delenv("AILINE_DEV_MODE", raising=False)
    monkeypatch.setenv("AILINE_DEV_MODE", "false")
    app = create_app(_test_settings())
    yield app


# ---------------------------------------------------------------------------
# 1. Unauthenticated access returns 401
# ---------------------------------------------------------------------------


class TestUnauthenticatedAccess:
    """Endpoints requiring auth must return 401 when no tenant context."""

    def test_traces_recent_unauthenticated(self, no_auth_app) -> None:
        """GET /traces/recent without auth returns 401."""
        with TestClient(no_auth_app) as client:
            resp = client.get("/traces/recent")
            assert resp.status_code == 401

    def test_traces_by_id_unauthenticated(self, no_auth_app) -> None:
        """GET /traces/{run_id} without auth returns 401."""
        with TestClient(no_auth_app) as client:
            resp = client.get("/traces/some-run-id")
            assert resp.status_code == 401

    def test_observability_dashboard_unauthenticated(self, no_auth_app) -> None:
        """GET /observability/dashboard without auth returns 401."""
        with TestClient(no_auth_app) as client:
            resp = client.get("/observability/dashboard")
            assert resp.status_code == 401

    def test_materials_list_unauthenticated(self, no_auth_app) -> None:
        """GET /materials without auth returns 401."""
        with TestClient(no_auth_app) as client:
            resp = client.get("/materials")
            assert resp.status_code == 401

    def test_plans_generate_unauthenticated(self, no_auth_app) -> None:
        """POST /plans/generate without auth returns 401."""
        with TestClient(no_auth_app) as client:
            resp = client.post(
                "/plans/generate",
                json={"run_id": "r1", "user_prompt": "Test"},
            )
            assert resp.status_code == 401

    def test_rag_diagnostics_unauthenticated(self, no_auth_app) -> None:
        """GET /rag/diagnostics/recent without auth returns 401."""
        with TestClient(no_auth_app) as client:
            resp = client.get("/rag/diagnostics/recent")
            assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 2. Cross-tenant access denied
# ---------------------------------------------------------------------------


class TestCrossTenantAccess:
    """Tenant A must not access Tenant B's resources."""

    def test_tutor_get_cross_tenant_denied(
        self, dev_mode_app, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GET /tutors/{id} as wrong tenant returns 403."""
        mock_spec = MagicMock()
        mock_spec.teacher_id = TENANT_B
        mock_spec.model_dump.return_value = {"teacher_id": TENANT_B}

        with (
            patch(
                "ailine_runtime.api.routers.tutors.load_tutor_spec",
                return_value=mock_spec,
            ),
            TestClient(dev_mode_app) as client,
        ):
            resp = client.get(
                "/tutors/tutor-001",
                headers={"X-Teacher-ID": TENANT_A},
            )
            assert resp.status_code == 403

    def test_tutor_chat_cross_tenant_denied(
        self, dev_mode_app, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """POST /tutors/{id}/chat as wrong tenant returns 403."""
        mock_spec = MagicMock()
        mock_spec.teacher_id = TENANT_B

        with (
            patch(
                "ailine_runtime.api.routers.tutors.load_tutor_spec",
                return_value=mock_spec,
            ),
            TestClient(dev_mode_app) as client,
        ):
            resp = client.post(
                "/tutors/tutor-001/chat",
                json={"session_id": "s1", "message": "Hello"},
                headers={"X-Teacher-ID": TENANT_A},
            )
            assert resp.status_code == 403

    def test_materials_list_scoped_to_own_tenant(
        self, dev_mode_app, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GET /materials as Tenant A returns only Tenant A's materials."""
        called_with: dict = {}

        def spy_iter(*, teacher_id: str | None = None, subject: str | None = None):
            called_with["teacher_id"] = teacher_id
            return []

        with (
            patch(
                "ailine_runtime.api.routers.materials.iter_materials",
                side_effect=spy_iter,
            ),
            TestClient(dev_mode_app) as client,
        ):
            resp = client.get(
                "/materials",
                headers={"X-Teacher-ID": TENANT_A},
            )
            assert resp.status_code == 200
            assert called_with["teacher_id"] == TENANT_A


# ---------------------------------------------------------------------------
# 3. Centralized authz unit tests
# ---------------------------------------------------------------------------


class TestAuthzModule:
    """Unit tests for the centralized authz module."""

    def test_authorization_error_attributes(self) -> None:
        err = AuthorizationError("delete", "lesson plan")
        assert err.action == "delete"
        assert err.resource == "lesson plan"
        assert "delete" in str(err)
        assert "lesson plan" in str(err)

    def test_require_authenticated_raises_when_no_context(self) -> None:
        """require_authenticated raises TenantNotFoundError when no context."""
        from ailine_runtime.domain.exceptions import TenantNotFoundError

        with pytest.raises(TenantNotFoundError, match="Authentication required"):
            require_authenticated()

    def test_require_authenticated_returns_id(self) -> None:
        """require_authenticated returns teacher_id when context is set."""
        token = set_tenant_id("teacher-123")
        try:
            assert require_authenticated() == "teacher-123"
        finally:
            from ailine_runtime.shared.tenant import clear_tenant_id

            clear_tenant_id(token)

    def test_require_tenant_access_same_tenant(self) -> None:
        """require_tenant_access succeeds for same tenant."""
        token = set_tenant_id("teacher-123")
        try:
            ctx = require_tenant_access("teacher-123")
            assert ctx.teacher_id == "teacher-123"
        finally:
            from ailine_runtime.shared.tenant import clear_tenant_id

            clear_tenant_id(token)

    def test_require_tenant_access_different_tenant(self) -> None:
        """require_tenant_access raises UnauthorizedAccessError for different tenant."""
        from ailine_runtime.domain.exceptions import UnauthorizedAccessError

        token = set_tenant_id("teacher-123")
        try:
            with pytest.raises(UnauthorizedAccessError, match="Access denied"):
                require_tenant_access("teacher-other")
        finally:
            from ailine_runtime.shared.tenant import clear_tenant_id

            clear_tenant_id(token)

    def test_can_observe_returns_false_no_auth(self) -> None:
        """can_observe returns False when no auth context."""
        assert can_observe() is False

    def test_can_observe_returns_true_with_auth(self) -> None:
        """can_observe returns True when auth context is set."""
        token = set_tenant_id("teacher-123")
        try:
            assert can_observe() is True
        finally:
            from ailine_runtime.shared.tenant import clear_tenant_id

            clear_tenant_id(token)


# ---------------------------------------------------------------------------
# 4. Cross-tenant vector store isolation
# ---------------------------------------------------------------------------


class TestCrossTenantVectorIsolation:
    """InMemoryVectorStore must enforce tenant isolation."""

    @pytest.fixture()
    def store(self) -> InMemoryVectorStore:
        return InMemoryVectorStore()

    async def test_search_returns_only_own_tenant(self, store: InMemoryVectorStore) -> None:
        """Tenant A's search must not return Tenant B's embeddings."""
        embedding_a = [1.0, 0.0, 0.0]
        embedding_b = [0.9, 0.1, 0.0]

        await store.upsert(
            ids=["chunk-a1"],
            embeddings=[embedding_a],
            texts=["Content by Tenant A"],
            metadatas=[{"source": "a"}],
            tenant_id=TENANT_A,
        )
        await store.upsert(
            ids=["chunk-b1"],
            embeddings=[embedding_b],
            texts=["Content by Tenant B"],
            metadatas=[{"source": "b"}],
            tenant_id=TENANT_B,
        )

        # Search as Tenant A -- must only see chunk-a1
        results_a = await store.search(
            query_embedding=[1.0, 0.0, 0.0],
            k=10,
            tenant_id=TENANT_A,
        )
        assert len(results_a) == 1
        assert results_a[0].id == "chunk-a1"

        # Search as Tenant B -- must only see chunk-b1
        results_b = await store.search(
            query_embedding=[1.0, 0.0, 0.0],
            k=10,
            tenant_id=TENANT_B,
        )
        assert len(results_b) == 1
        assert results_b[0].id == "chunk-b1"

    async def test_search_without_tenant_returns_all(self, store: InMemoryVectorStore) -> None:
        """Search without tenant_id returns all chunks (backward compat)."""
        await store.upsert(
            ids=["c1"],
            embeddings=[[1.0, 0.0]],
            texts=["text1"],
            metadatas=[{}],
            tenant_id=TENANT_A,
        )
        await store.upsert(
            ids=["c2"],
            embeddings=[[0.9, 0.1]],
            texts=["text2"],
            metadatas=[{}],
            tenant_id=TENANT_B,
        )

        results = await store.search(
            query_embedding=[1.0, 0.0],
            k=10,
        )
        assert len(results) == 2

    async def test_tenant_isolation_with_many_chunks(self, store: InMemoryVectorStore) -> None:
        """Even with many chunks, only the correct tenant's data is returned."""
        for i in range(10):
            await store.upsert(
                ids=[f"a-{i}"],
                embeddings=[[float(i) / 10, 1.0 - float(i) / 10]],
                texts=[f"A content {i}"],
                metadatas=[{}],
                tenant_id=TENANT_A,
            )
        for i in range(5):
            await store.upsert(
                ids=[f"b-{i}"],
                embeddings=[[float(i) / 10, 1.0 - float(i) / 10]],
                texts=[f"B content {i}"],
                metadatas=[{}],
                tenant_id=TENANT_B,
            )

        results_a = await store.search(
            query_embedding=[0.5, 0.5], k=20, tenant_id=TENANT_A,
        )
        results_b = await store.search(
            query_embedding=[0.5, 0.5], k=20, tenant_id=TENANT_B,
        )

        assert len(results_a) == 10
        assert all(r.id.startswith("a-") for r in results_a)
        assert len(results_b) == 5
        assert all(r.id.startswith("b-") for r in results_b)
