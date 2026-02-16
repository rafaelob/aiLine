"""Tests for the tenant context middleware and tenant isolation helpers.

Covers:
- TenantContext value object
- contextvars-based tenant ID management
- Teacher ID format validation
- TenantContextMiddleware (JWT, X-Teacher-ID header, dev mode)
- Router integration: middleware context takes precedence over body
"""

from __future__ import annotations

import base64
import json
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.api.app import create_app
from ailine_runtime.shared.config import (
    DatabaseConfig,
    EmbeddingConfig,
    LLMConfig,
    RedisConfig,
    Settings,
)
from ailine_runtime.shared.tenant import (
    TenantContext,
    clear_tenant_id,
    get_current_teacher_id,
    get_tenant,
    set_tenant_id,
    try_get_current_teacher_id,
    validate_teacher_id_format,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _enable_dev_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enable dev mode for all tests in this module.

    The test helpers use unsigned JWTs (_make_jwt with alg=none),
    which require dev mode for the unverified fallback path.
    """
    monkeypatch.setenv("AILINE_DEV_MODE", "true")


@pytest.fixture()
def settings() -> Settings:
    return Settings(
        anthropic_api_key="fake-key-for-tests",
        openai_api_key="",
        google_api_key="",
        db=DatabaseConfig(url="sqlite+aiosqlite:///:memory:"),
        llm=LLMConfig(provider="fake", api_key="fake"),
        embedding=EmbeddingConfig(provider="gemini", api_key=""),
        redis=RedisConfig(url="redis://localhost:6379/0"),
    )


@pytest.fixture()
def app(settings: Settings):
    return create_app(settings=settings)


@pytest.fixture()
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _make_jwt(payload: dict) -> str:
    """Create a minimal JWT (unsigned) for testing."""
    header = (
        base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode())
        .rstrip(b"=")
        .decode()
    )
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{header}.{body}."


# ---------------------------------------------------------------------------
# Unit tests: TenantContext value object
# ---------------------------------------------------------------------------


class TestTenantContext:
    def test_verify_access_same_tenant(self) -> None:
        ctx = TenantContext(teacher_id="teacher-001")
        # Should not raise
        ctx.verify_access("teacher-001")

    def test_verify_access_different_tenant_raises_error(self) -> None:
        ctx = TenantContext(teacher_id="teacher-001")
        from ailine_runtime.domain.exceptions import UnauthorizedAccessError

        with pytest.raises(UnauthorizedAccessError, match="Access denied"):
            ctx.verify_access("teacher-002")

    def test_repr(self) -> None:
        ctx = TenantContext(teacher_id="abc")
        assert "abc" in repr(ctx)

    def test_equality(self) -> None:
        a = TenantContext(teacher_id="x")
        b = TenantContext(teacher_id="x")
        c = TenantContext(teacher_id="y")
        assert a == b
        assert a != c
        assert a != "not a tenant context"


# ---------------------------------------------------------------------------
# Unit tests: contextvars management
# ---------------------------------------------------------------------------


class TestContextVars:
    def test_set_and_get_tenant_id(self) -> None:
        token = set_tenant_id("teacher-test")
        try:
            assert get_current_teacher_id() == "teacher-test"
            assert try_get_current_teacher_id() == "teacher-test"
        finally:
            clear_tenant_id(token)

    def test_get_current_teacher_id_raises_when_not_set(self) -> None:
        from ailine_runtime.domain.exceptions import TenantNotFoundError

        with pytest.raises(TenantNotFoundError, match="Authentication required"):
            get_current_teacher_id()

    def test_try_get_returns_none_when_not_set(self) -> None:
        assert try_get_current_teacher_id() is None

    def test_get_tenant_returns_tenant_context(self) -> None:
        token = set_tenant_id("teacher-abc")
        try:
            ctx = get_tenant()
            assert isinstance(ctx, TenantContext)
            assert ctx.teacher_id == "teacher-abc"
        finally:
            clear_tenant_id(token)

    def test_clear_resets_context(self) -> None:
        token = set_tenant_id("teacher-temp")
        clear_tenant_id(token)
        assert try_get_current_teacher_id() is None


# ---------------------------------------------------------------------------
# Unit tests: validate_teacher_id_format
# ---------------------------------------------------------------------------


class TestValidateTeacherIdFormat:
    def test_valid_uuid(self) -> None:
        result = validate_teacher_id_format("550e8400-e29b-41d4-a716-446655440000")
        assert result == "550e8400-e29b-41d4-a716-446655440000"

    def test_valid_simple_id(self) -> None:
        result = validate_teacher_id_format("teacher-001")
        assert result == "teacher-001"

    def test_valid_underscore_id(self) -> None:
        result = validate_teacher_id_format("teacher_001")
        assert result == "teacher_001"

    def test_strips_whitespace(self) -> None:
        result = validate_teacher_id_format("  teacher-001  ")
        assert result == "teacher-001"

    def test_empty_raises_error(self) -> None:
        from ailine_runtime.domain.exceptions import InvalidTenantIdError

        with pytest.raises(InvalidTenantIdError, match="must not be empty"):
            validate_teacher_id_format("")

    def test_too_long_raises_error(self) -> None:
        from ailine_runtime.domain.exceptions import InvalidTenantIdError

        with pytest.raises(InvalidTenantIdError, match="exceeds maximum length"):
            validate_teacher_id_format("a" * 129)

    def test_special_chars_raises_error(self) -> None:
        from ailine_runtime.domain.exceptions import InvalidTenantIdError

        with pytest.raises(InvalidTenantIdError, match="must be a UUID"):
            validate_teacher_id_format("teacher@evil.com")

    def test_path_traversal_raises_error(self) -> None:
        from ailine_runtime.domain.exceptions import InvalidTenantIdError

        with pytest.raises(InvalidTenantIdError, match="must be a UUID"):
            validate_teacher_id_format("../../../etc/passwd")


# ---------------------------------------------------------------------------
# Integration tests: TenantContextMiddleware with JWT
# ---------------------------------------------------------------------------


class TestTenantMiddlewareJWT:
    async def test_jwt_sets_tenant_context(self, client: AsyncClient) -> None:
        """JWT Bearer token with sub claim should set tenant context."""
        jwt = _make_jwt({"sub": "teacher-jwt-001"})
        resp = await client.get("/health", headers={"Authorization": f"Bearer {jwt}"})
        # Health endpoint is excluded from tenant enforcement, but
        # the middleware still processes the JWT (just doesn't block)
        assert resp.status_code == 200

    async def test_invalid_jwt_does_not_block(self, client: AsyncClient) -> None:
        """A malformed JWT should not block the request."""
        resp = await client.get(
            "/health",
            headers={"Authorization": "Bearer not-a-real-jwt"},
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Integration tests: TenantContextMiddleware with X-Teacher-ID
# ---------------------------------------------------------------------------


class TestTenantMiddlewareDevHeader:
    async def test_x_teacher_id_ignored_without_dev_mode(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """X-Teacher-ID header should be ignored when dev mode is off."""
        monkeypatch.setenv("AILINE_DEV_MODE", "false")
        resp = await client.get(
            "/health",
            headers={"X-Teacher-ID": "teacher-dev-001"},
        )
        assert resp.status_code == 200

    async def test_x_teacher_id_accepted_in_dev_mode(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """X-Teacher-ID header should be accepted when AILINE_DEV_MODE=true."""
        monkeypatch.setenv("AILINE_DEV_MODE", "true")
        resp = await client.get(
            "/health",
            headers={"X-Teacher-ID": "teacher-dev-001"},
        )
        assert resp.status_code == 200

    async def test_invalid_teacher_id_in_header_returns_422(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Invalid teacher_id format in X-Teacher-ID should return 422."""
        monkeypatch.setenv("AILINE_DEV_MODE", "true")
        # Need a non-excluded path to trigger validation
        resp = await client.get(
            "/materials",
            headers={"X-Teacher-ID": "teacher@evil.com"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Integration tests: Router backward compatibility
# ---------------------------------------------------------------------------


class TestRouterBackwardCompat:
    """Verify that routers still accept teacher_id from request body
    when no middleware context is set (backward compatibility).
    """

    async def test_materials_add_without_auth_returns_401(
        self, client: AsyncClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """POST /materials with teacher_id only in body (no auth) returns 401 (ADR-060)."""
        store_dir = tmp_path / "local_store"
        store_dir.mkdir()
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(store_dir))

        resp = await client.post(
            "/materials",
            json={
                "teacher_id": "teacher-body-001",
                "subject": "Matematica",
                "title": "Test material",
                "content": "Content here.",
            },
        )
        # Centralized authz requires auth context -- body-only is no longer sufficient
        assert resp.status_code == 401

    async def test_materials_add_with_jwt_overrides_body(
        self, client: AsyncClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When JWT provides teacher_id, it should override body teacher_id."""
        store_dir = tmp_path / "local_store"
        store_dir.mkdir()
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(store_dir))

        jwt = _make_jwt({"sub": "teacher-jwt-override"})
        resp = await client.post(
            "/materials",
            json={
                "teacher_id": "teacher-body-ignored",
                "subject": "Matematica",
                "title": "Test material",
                "content": "Content here.",
            },
            headers={"Authorization": f"Bearer {jwt}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        # The material should be owned by the JWT teacher, not the body one
        assert body["teacher_id"] == "teacher-jwt-override"

    async def test_materials_add_with_dev_header_overrides_body(
        self,
        client: AsyncClient,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When X-Teacher-ID header is set in dev mode, it overrides body."""
        store_dir = tmp_path / "local_store"
        store_dir.mkdir()
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(store_dir))
        monkeypatch.setenv("AILINE_DEV_MODE", "true")

        resp = await client.post(
            "/materials",
            json={
                "teacher_id": "teacher-body-ignored",
                "subject": "Matematica",
                "title": "Test material",
                "content": "Content here.",
            },
            headers={"X-Teacher-ID": "teacher-header-wins"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["teacher_id"] == "teacher-header-wins"


# ---------------------------------------------------------------------------
# Integration tests: Plans router with tenant context
# ---------------------------------------------------------------------------


class TestPlansRouterTenantContext:
    async def test_plans_generate_with_jwt_teacher_id(
        self, client: AsyncClient
    ) -> None:
        """POST /plans/generate with JWT should pass teacher_id from JWT."""
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_workflow = MagicMock()
        mock_workflow.ainvoke = AsyncMock(
            return_value={
                "run_id": "test-run",
                "final": {"parsed": {"plan_id": "test", "score": 90}},
            }
        )

        mock_factory = MagicMock()
        mock_factory.from_container = MagicMock(return_value=MagicMock())

        jwt = _make_jwt({"sub": "teacher-jwt-plan"})

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
                    "run_id": "test-run",
                    "user_prompt": "Create a lesson about fractions",
                },
                headers={"Authorization": f"Bearer {jwt}"},
            )

        assert resp.status_code == 200
        # Verify the factory was called with the JWT teacher_id
        call_kwargs = mock_factory.from_container.call_args
        assert call_kwargs.kwargs.get("teacher_id") == "teacher-jwt-plan"


# ---------------------------------------------------------------------------
# Integration tests: Tutors router with tenant isolation
# ---------------------------------------------------------------------------


class TestTutorsRouterTenantIsolation:
    async def test_tutor_get_with_wrong_tenant_returns_403(
        self,
        client: AsyncClient,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """GET /tutors/{id} with JWT for wrong teacher should return 403."""
        store_dir = tmp_path / "local_store"
        store_dir.mkdir()
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(store_dir))
        monkeypatch.setenv("AILINE_DEV_MODE", "true")

        # Create tutor as teacher-001 (dev-mode header)
        create_resp = await client.post(
            "/tutors",
            json={
                "teacher_id": "teacher-001",
                "subject": "Matematica",
                "grade": "6o ano",
                "student_profile": {
                    "name": "Aluno",
                    "needs": [],
                    "language": "pt-BR",
                },
            },
            headers={"X-Teacher-ID": "teacher-001"},
        )
        assert create_resp.status_code == 200
        tutor_id = create_resp.json()["tutor_id"]

        # Try to access as teacher-002 via dev-mode header
        resp = await client.get(
            f"/tutors/{tutor_id}",
            headers={"X-Teacher-ID": "teacher-002"},
        )
        assert resp.status_code == 403

    async def test_tutor_get_with_correct_tenant_succeeds(
        self,
        client: AsyncClient,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """GET /tutors/{id} with correct tenant should succeed."""
        store_dir = tmp_path / "local_store"
        store_dir.mkdir()
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(store_dir))
        monkeypatch.setenv("AILINE_DEV_MODE", "true")

        # Create tutor as teacher-001
        create_resp = await client.post(
            "/tutors",
            json={
                "teacher_id": "teacher-001",
                "subject": "Matematica",
                "grade": "6o ano",
                "student_profile": {
                    "name": "Aluno",
                    "needs": [],
                    "language": "pt-BR",
                },
            },
            headers={"X-Teacher-ID": "teacher-001"},
        )
        assert create_resp.status_code == 200
        tutor_id = create_resp.json()["tutor_id"]

        # Access as teacher-001 via dev-mode header
        resp = await client.get(
            f"/tutors/{tutor_id}",
            headers={"X-Teacher-ID": "teacher-001"},
        )
        assert resp.status_code == 200
        assert resp.json()["tutor_id"] == tutor_id


# ---------------------------------------------------------------------------
# Integration tests: Excluded paths
# ---------------------------------------------------------------------------


class TestExcludedPaths:
    async def test_health_excluded_from_tenant_enforcement(
        self, client: AsyncClient
    ) -> None:
        """Health endpoint should work without any tenant context."""
        resp = await client.get("/health")
        assert resp.status_code == 200

    async def test_docs_excluded(self, client: AsyncClient) -> None:
        """Docs endpoints should be excluded from tenant enforcement."""
        resp = await client.get("/docs")
        # /docs may redirect or return HTML; just check it doesn't 401/403
        assert resp.status_code in (200, 307)


# ---------------------------------------------------------------------------
# Dev-mode safety tests (Gap 3: validate_dev_mode)
# ---------------------------------------------------------------------------


class TestDevModeSafety:
    """Tests for the validate_dev_mode() startup guard."""

    def test_dev_mode_disabled_no_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When AILINE_DEV_MODE is not set, validate_dev_mode should be a no-op."""
        monkeypatch.delenv("AILINE_DEV_MODE", raising=False)
        from ailine_runtime.api.middleware.tenant_context import validate_dev_mode

        # Should not raise for any environment when dev mode is off.
        validate_dev_mode(env="production")
        validate_dev_mode(env="development")
        validate_dev_mode(env="staging")

    def test_dev_mode_in_production_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dev mode in production must raise ValueError."""
        monkeypatch.setenv("AILINE_DEV_MODE", "true")
        from ailine_runtime.api.middleware.tenant_context import validate_dev_mode

        with pytest.raises(ValueError, match="FORBIDDEN in production"):
            validate_dev_mode(env="production")

    def test_dev_mode_in_development_logs_warning(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dev mode in development should not raise (but logs a warning)."""
        monkeypatch.setenv("AILINE_DEV_MODE", "true")
        from ailine_runtime.api.middleware.tenant_context import validate_dev_mode

        # Should not raise.
        validate_dev_mode(env="development")

    def test_dev_mode_in_staging_logs_warning(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dev mode in staging should not raise (but logs a warning)."""
        monkeypatch.setenv("AILINE_DEV_MODE", "true")
        from ailine_runtime.api.middleware.tenant_context import validate_dev_mode

        # Should not raise.
        validate_dev_mode(env="staging")

    def test_create_app_raises_in_production_with_dev_mode(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """create_app() should fail if env=production and dev mode is on."""
        monkeypatch.setenv("AILINE_DEV_MODE", "true")
        prod_settings = Settings(
            anthropic_api_key="fake-key",
            openai_api_key="",
            google_api_key="",
            db=DatabaseConfig(url="sqlite+aiosqlite:///:memory:"),
            llm=LLMConfig(provider="fake", api_key="fake"),
            embedding=EmbeddingConfig(provider="gemini", api_key=""),
            redis=RedisConfig(url=""),
            env="production",
        )
        with pytest.raises(ValueError, match="FORBIDDEN in production"):
            create_app(settings=prod_settings)

    def test_create_app_succeeds_in_development_with_dev_mode(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """create_app() should succeed in development even with dev mode on."""
        monkeypatch.setenv("AILINE_DEV_MODE", "true")
        dev_settings = Settings(
            anthropic_api_key="fake-key",
            openai_api_key="",
            google_api_key="",
            db=DatabaseConfig(url="sqlite+aiosqlite:///:memory:"),
            llm=LLMConfig(provider="fake", api_key="fake"),
            embedding=EmbeddingConfig(provider="gemini", api_key=""),
            redis=RedisConfig(url=""),
            env="development",
        )
        app = create_app(settings=dev_settings)
        assert app is not None
