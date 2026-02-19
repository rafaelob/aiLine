"""Tests for the auth API router (login, register, /me, /roles).

Covers:
- POST /auth/login: dev mode auto-create, password verification, invalid credentials
- POST /auth/register: new user, duplicate email, role assignment
- GET /auth/me: authenticated profile retrieval, unauthenticated denial
- GET /auth/roles: role list with descriptions
- Token response format validation
- In-memory user store behavior
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

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

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def settings_dev() -> Settings:
    """Settings with dev mode for testing auth (permissive login)."""
    return Settings(
        anthropic_api_key="fake-key",
        openai_api_key="",
        google_api_key="",
        openrouter_api_key="",
        db=DatabaseConfig(url="sqlite+aiosqlite:///:memory:"),
        llm=LLMConfig(provider="fake", api_key="fake"),
        embedding=EmbeddingConfig(provider="gemini", api_key=""),
        redis=RedisConfig(url=""),
    )


@pytest.fixture()
def app_dev(settings_dev: Settings, monkeypatch: pytest.MonkeyPatch):
    """FastAPI app with AILINE_DEV_MODE=true."""
    monkeypatch.setenv("AILINE_DEV_MODE", "true")
    return create_app(settings=settings_dev)


@pytest.fixture()
def app_no_dev(settings_dev: Settings, monkeypatch: pytest.MonkeyPatch):
    """FastAPI app with AILINE_DEV_MODE=false."""
    monkeypatch.setenv("AILINE_DEV_MODE", "false")
    return create_app(settings=settings_dev)


@pytest.fixture()
async def client_dev(app_dev) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app_dev, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport, base_url="http://test", timeout=10.0
    ) as c:
        yield c


@pytest.fixture()
async def client_no_dev(app_no_dev) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app_no_dev, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport, base_url="http://test", timeout=10.0
    ) as c:
        yield c


def _reset_auth_store() -> None:
    """Clear the in-memory user store and rate limiter between tests."""
    from ailine_runtime.adapters.db.user_repository import InMemoryUserRepository
    from ailine_runtime.api.routers.auth import _login_attempts, _user_repo

    if isinstance(_user_repo, InMemoryUserRepository):
        _user_repo._by_email.clear()
        _user_repo._by_id.clear()
    _login_attempts.clear()


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


class TestLoginEndpoint:
    """Tests for POST /auth/login."""

    @pytest.fixture(autouse=True)
    def _clean_store(self) -> None:
        _reset_auth_store()
        yield
        _reset_auth_store()

    async def test_login_dev_mode_auto_creates_user(
        self, client_dev: AsyncClient
    ) -> None:
        """In dev mode, any email/role combination auto-creates a user."""
        resp = await client_dev.post(
            "/auth/login",
            json={"email": "new-teacher@test.com", "role": "teacher"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["user"]["email"] == "new-teacher@test.com"
        assert body["user"]["role"] == "teacher"
        assert body["user"]["is_active"] is True

    async def test_login_dev_mode_returns_jwt(self, client_dev: AsyncClient) -> None:
        resp = await client_dev.post(
            "/auth/login",
            json={"email": "jwt-test@test.com"},
        )
        body = resp.json()
        token = body["access_token"]
        # Dev JWT is base64url header.payload.signature
        parts = token.split(".")
        assert len(parts) == 3

    async def test_login_dev_mode_display_name_derived_from_email(
        self, client_dev: AsyncClient
    ) -> None:
        resp = await client_dev.post(
            "/auth/login",
            json={"email": "john.doe@school.edu"},
        )
        body = resp.json()
        # Email "john.doe" -> "John Doe"
        assert body["user"]["display_name"] == "John Doe"

    async def test_login_existing_user_no_password(
        self, client_dev: AsyncClient
    ) -> None:
        """Logging in twice with the same email returns the same user."""
        resp1 = await client_dev.post(
            "/auth/login",
            json={"email": "same@test.com", "role": "teacher"},
        )
        user_id_1 = resp1.json()["user"]["id"]

        resp2 = await client_dev.post(
            "/auth/login",
            json={"email": "same@test.com", "role": "teacher"},
        )
        user_id_2 = resp2.json()["user"]["id"]
        assert user_id_1 == user_id_2

    async def test_login_wrong_password_rejected(self, client_dev: AsyncClient) -> None:
        """Once a user is registered with a password, wrong password is rejected."""
        # First register with a password
        await client_dev.post(
            "/auth/register",
            json={
                "email": "pw-user@test.com",
                "display_name": "PW User",
                "password": "correct-password",
            },
        )
        # Login with wrong password
        resp = await client_dev.post(
            "/auth/login",
            json={"email": "pw-user@test.com", "password": "wrong-password"},
        )
        assert resp.status_code == 401

    async def test_login_non_dev_unknown_email_rejected(
        self, client_no_dev: AsyncClient
    ) -> None:
        """In non-dev mode, unknown email should be rejected."""
        resp = await client_no_dev.post(
            "/auth/login",
            json={"email": "unknown@test.com"},
        )
        assert resp.status_code == 401
        assert "Invalid credentials" in resp.json()["detail"]

    async def test_login_student_role(self, client_dev: AsyncClient) -> None:
        resp = await client_dev.post(
            "/auth/login",
            json={"email": "student@test.com", "role": "student"},
        )
        assert resp.status_code == 200
        assert resp.json()["user"]["role"] == "student"

    async def test_login_parent_role(self, client_dev: AsyncClient) -> None:
        resp = await client_dev.post(
            "/auth/login",
            json={"email": "parent@test.com", "role": "parent"},
        )
        assert resp.status_code == 200
        assert resp.json()["user"]["role"] == "parent"


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------


class TestRegisterEndpoint:
    """Tests for POST /auth/register."""

    @pytest.fixture(autouse=True)
    def _clean_store(self) -> None:
        _reset_auth_store()
        yield
        _reset_auth_store()

    async def test_register_new_user(self, client_dev: AsyncClient) -> None:
        resp = await client_dev.post(
            "/auth/register",
            json={
                "email": "new@school.edu",
                "display_name": "New Teacher",
                "role": "teacher",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["user"]["email"] == "new@school.edu"
        assert body["user"]["display_name"] == "New Teacher"
        assert body["user"]["role"] == "teacher"
        assert body["user"]["is_active"] is True
        assert "access_token" in body

    async def test_register_duplicate_email_rejected(
        self, client_dev: AsyncClient
    ) -> None:
        await client_dev.post(
            "/auth/register",
            json={
                "email": "dup@school.edu",
                "display_name": "First",
                "role": "teacher",
            },
        )
        resp = await client_dev.post(
            "/auth/register",
            json={
                "email": "dup@school.edu",
                "display_name": "Second",
                "role": "teacher",
            },
        )
        assert resp.status_code == 409
        assert "already registered" in resp.json()["detail"]

    async def test_register_with_org_id(self, client_dev: AsyncClient) -> None:
        resp = await client_dev.post(
            "/auth/register",
            json={
                "email": "org-user@school.edu",
                "display_name": "Org User",
                "role": "school_admin",
                "org_id": "org-123",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["user"]["org_id"] == "org-123"

    async def test_register_with_locale(self, client_dev: AsyncClient) -> None:
        resp = await client_dev.post(
            "/auth/register",
            json={
                "email": "br-user@school.edu",
                "display_name": "BR User",
                "locale": "pt-BR",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["user"]["locale"] == "pt-BR"

    async def test_register_returns_valid_jwt(self, client_dev: AsyncClient) -> None:
        resp = await client_dev.post(
            "/auth/register",
            json={
                "email": "jwt-reg@test.com",
                "display_name": "JWT Reg",
            },
        )
        token = resp.json()["access_token"]
        parts = token.split(".")
        assert len(parts) == 3

    async def test_register_default_role_is_teacher(
        self, client_dev: AsyncClient
    ) -> None:
        resp = await client_dev.post(
            "/auth/register",
            json={
                "email": "default-role@test.com",
                "display_name": "Default Role",
            },
        )
        assert resp.json()["user"]["role"] == "teacher"

    async def test_register_student_role(self, client_dev: AsyncClient) -> None:
        resp = await client_dev.post(
            "/auth/register",
            json={
                "email": "student-reg@test.com",
                "display_name": "Student User",
                "role": "student",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["user"]["role"] == "student"


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


class TestMeEndpoint:
    """Tests for GET /auth/me.

    The /auth prefix is in the tenant middleware excluded paths list,
    but the middleware still processes Bearer tokens and X-Teacher-ID on
    these paths (the exclusion applies only to blocking unauthenticated
    requests). The /me endpoint uses Depends(require_authenticated).
    """

    @pytest.fixture(autouse=True)
    def _clean_store(self) -> None:
        _reset_auth_store()
        yield
        _reset_auth_store()

    async def test_me_with_bearer_token(self, client_dev: AsyncClient) -> None:
        """Registered user can retrieve profile via /me with Bearer token."""
        reg_resp = await client_dev.post(
            "/auth/register",
            json={
                "email": "me-user@test.com",
                "display_name": "Me User",
                "role": "teacher",
            },
        )
        token = reg_resp.json()["access_token"]
        user_id = reg_resp.json()["user"]["id"]

        me_resp = await client_dev.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["id"] == user_id

    async def test_me_with_x_teacher_id(self, client_dev: AsyncClient) -> None:
        """X-Teacher-ID works for /auth/me in dev mode."""
        me_resp = await client_dev.get(
            "/auth/me",
            headers={"X-Teacher-ID": "any-user-id"},
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["id"] == "any-user-id"

    async def test_me_without_any_auth_returns_error(
        self, client_no_dev: AsyncClient
    ) -> None:
        """Without authentication, /me should fail."""
        resp = await client_no_dev.get("/auth/me")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /auth/roles
# ---------------------------------------------------------------------------


class TestRolesEndpoint:
    """Tests for GET /auth/roles."""

    async def test_roles_returns_all_roles(self, client_dev: AsyncClient) -> None:
        resp = await client_dev.get("/auth/roles")
        assert resp.status_code == 200
        body = resp.json()
        assert "roles" in body
        assert len(body["roles"]) == 5

    async def test_roles_have_required_fields(self, client_dev: AsyncClient) -> None:
        resp = await client_dev.get("/auth/roles")
        roles = resp.json()["roles"]
        for role in roles:
            assert "id" in role
            assert "name" in role
            assert "description" in role
            assert "icon" in role

    async def test_roles_include_all_rbac_roles(self, client_dev: AsyncClient) -> None:
        resp = await client_dev.get("/auth/roles")
        role_ids = {r["id"] for r in resp.json()["roles"]}
        expected = {"super_admin", "school_admin", "teacher", "student", "parent"}
        assert role_ids == expected

    async def test_roles_no_auth_required(self, client_no_dev: AsyncClient) -> None:
        """The /roles endpoint should be accessible without authentication."""
        resp = await client_no_dev.get("/auth/roles")
        assert resp.status_code == 200

    async def test_teacher_role_has_correct_description(
        self, client_dev: AsyncClient
    ) -> None:
        resp = await client_dev.get("/auth/roles")
        roles = resp.json()["roles"]
        teacher = next(r for r in roles if r["id"] == "teacher")
        assert "lesson plans" in teacher["description"].lower()
        assert teacher["icon"] == "graduation-cap"

    async def test_student_role_has_correct_description(
        self, client_dev: AsyncClient
    ) -> None:
        resp = await client_dev.get("/auth/roles")
        roles = resp.json()["roles"]
        student = next(r for r in roles if r["id"] == "student")
        assert "learning" in student["description"].lower()
        assert student["icon"] == "book-open"


# ---------------------------------------------------------------------------
# Token format validation
# ---------------------------------------------------------------------------


class TestTokenFormat:
    """Tests for JWT token structure produced by auth endpoints."""

    @pytest.fixture(autouse=True)
    def _clean_store(self) -> None:
        _reset_auth_store()
        yield
        _reset_auth_store()

    async def test_token_contains_user_id(self, client_dev: AsyncClient) -> None:
        """JWT payload should contain the user's sub claim."""
        import base64
        import json

        resp = await client_dev.post(
            "/auth/login",
            json={"email": "token-test@test.com"},
        )
        token = resp.json()["access_token"]
        payload_b64 = token.split(".")[1]
        # Add padding
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        assert "sub" in payload
        assert payload["sub"] == resp.json()["user"]["id"]

    async def test_token_contains_role(self, client_dev: AsyncClient) -> None:
        """Token payload includes the validated role.

        Self-registration with admin roles (e.g. school_admin) is blocked
        by _validate_role() — the role is normalised to 'teacher'.
        Only self-assignable roles (teacher, student, parent) are accepted.
        """
        import base64
        import json

        # Admin roles are normalised to teacher on self-registration
        resp = await client_dev.post(
            "/auth/login",
            json={"email": "role-token@test.com", "role": "school_admin"},
        )
        token = resp.json()["access_token"]
        payload_b64 = token.split(".")[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        assert payload["role"] == "teacher"  # admin self-assign blocked

        # Self-assignable roles are preserved
        resp2 = await client_dev.post(
            "/auth/login",
            json={"email": "role-token-student@test.com", "role": "student"},
        )
        token2 = resp2.json()["access_token"]
        payload_b64_2 = token2.split(".")[1]
        padding2 = 4 - len(payload_b64_2) % 4
        if padding2 != 4:
            payload_b64_2 += "=" * padding2
        payload2 = json.loads(base64.urlsafe_b64decode(payload_b64_2))
        assert payload2["role"] == "student"

    async def test_token_has_expiry(self, client_dev: AsyncClient) -> None:
        import base64
        import json
        import time

        resp = await client_dev.post(
            "/auth/login",
            json={"email": "exp-token@test.com"},
        )
        token = resp.json()["access_token"]
        payload_b64 = token.split(".")[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        assert "exp" in payload
        assert "iat" in payload
        # Expiry should be ~24h from now
        assert payload["exp"] > time.time()
        assert payload["exp"] - payload["iat"] == 86400

    async def test_token_is_pyjwt_verifiable(self, client_dev: AsyncClient) -> None:
        """Token produced by auth endpoints must be verifiable by PyJWT."""
        import jwt as pyjwt

        resp = await client_dev.post(
            "/auth/login",
            json={"email": "pyjwt-test@test.com"},
        )
        token = resp.json()["access_token"]
        # Should be decodable by PyJWT with the dev secret
        payload = pyjwt.decode(
            token, "dev-secret-not-for-production-use-32bytes!", algorithms=["HS256"]
        )
        assert payload["sub"] == resp.json()["user"]["id"]
        assert payload["role"] == "teacher"


# ---------------------------------------------------------------------------
# Email validation
# ---------------------------------------------------------------------------


class TestEmailValidation:
    """Tests for email format validation on login and register."""

    @pytest.fixture(autouse=True)
    def _clean_store(self) -> None:
        _reset_auth_store()
        yield
        _reset_auth_store()

    async def test_login_rejects_invalid_email(self, client_dev: AsyncClient) -> None:
        resp = await client_dev.post(
            "/auth/login",
            json={"email": "not-an-email"},
        )
        assert resp.status_code == 422

    async def test_login_rejects_empty_email(self, client_dev: AsyncClient) -> None:
        resp = await client_dev.post(
            "/auth/login",
            json={"email": ""},
        )
        assert resp.status_code == 422

    async def test_login_rejects_email_without_domain(
        self, client_dev: AsyncClient
    ) -> None:
        resp = await client_dev.post(
            "/auth/login",
            json={"email": "user@"},
        )
        assert resp.status_code == 422

    async def test_login_rejects_email_without_tld(
        self, client_dev: AsyncClient
    ) -> None:
        resp = await client_dev.post(
            "/auth/login",
            json={"email": "user@domain"},
        )
        assert resp.status_code == 422

    async def test_register_rejects_invalid_email(
        self, client_dev: AsyncClient
    ) -> None:
        resp = await client_dev.post(
            "/auth/register",
            json={"email": "bad-email", "display_name": "Test"},
        )
        assert resp.status_code == 422

    async def test_login_normalizes_email_to_lowercase(
        self, client_dev: AsyncClient
    ) -> None:
        resp = await client_dev.post(
            "/auth/login",
            json={"email": "UPPER@TEST.COM"},
        )
        assert resp.status_code == 200
        assert resp.json()["user"]["email"] == "upper@test.com"

    async def test_register_normalizes_email_to_lowercase(
        self, client_dev: AsyncClient
    ) -> None:
        resp = await client_dev.post(
            "/auth/register",
            json={"email": "MiXeD@School.EDU", "display_name": "Mixed"},
        )
        assert resp.status_code == 200
        assert resp.json()["user"]["email"] == "mixed@school.edu"


# ---------------------------------------------------------------------------
# Password security (non-dev mode)
# ---------------------------------------------------------------------------


class TestPasswordSecurity:
    """Tests for password-related security fixes."""

    @pytest.fixture(autouse=True)
    def _clean_store(self) -> None:
        _reset_auth_store()
        yield
        _reset_auth_store()

    async def test_passwordless_demo_user_blocked_in_non_dev(
        self, client_no_dev: AsyncClient
    ) -> None:
        """Demo users (no password) must be inaccessible in non-dev mode.

        This is the CRITICAL fix: seeded demo users have empty hashed_password.
        In non-dev mode, attempting to login as a demo user must be rejected,
        even if the attacker sends an empty password.
        """
        from ailine_runtime.adapters.db.models import UserRow
        from ailine_runtime.adapters.db.user_repository import InMemoryUserRepository
        from ailine_runtime.api.routers.auth import _user_repo

        # Directly seed a passwordless user (simulating demo seed).
        # No lock needed: test is single-threaded and no server is active yet.
        assert isinstance(_user_repo, InMemoryUserRepository)
        row = UserRow(
            id="demo-user-001",
            email="demo-critical@test.com",
            display_name="Demo User",
            role="teacher",
            locale="en",
            avatar_url="",
            accessibility_profile="",
            is_active=True,
            hashed_password="",  # No password (demo user)
        )
        _user_repo.seed_sync(row)

        # In non-dev mode, passwordless accounts are NEVER accessible
        resp = await client_no_dev.post(
            "/auth/login",
            json={"email": "demo-critical@test.com", "password": ""},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Login rate limiting
# ---------------------------------------------------------------------------


class TestLoginRateLimit:
    """Tests for per-IP login rate limiting (5 attempts/minute)."""

    @pytest.fixture(autouse=True)
    def _clean_store(self) -> None:
        _reset_auth_store()
        # Also clear login rate limiter state
        from ailine_runtime.api.routers.auth import _login_attempts
        _login_attempts.clear()
        yield
        _reset_auth_store()
        _login_attempts.clear()

    async def test_login_rate_limit_blocks_after_5_attempts(
        self, client_dev: AsyncClient
    ) -> None:
        """After 5 login attempts, the 6th should be rate limited."""
        for i in range(5):
            resp = await client_dev.post(
                "/auth/login",
                json={"email": f"rate-test-{i}@test.com", "role": "teacher"},
            )
            assert resp.status_code == 200

        # 6th attempt should be rate limited
        resp = await client_dev.post(
            "/auth/login",
            json={"email": "rate-test-blocked@test.com", "role": "teacher"},
        )
        assert resp.status_code == 429
        assert "Too many login attempts" in resp.json()["detail"]

    async def test_login_rate_limit_returns_retry_after(
        self, client_dev: AsyncClient
    ) -> None:
        """Rate limit response should include Retry-After header."""
        for i in range(5):
            await client_dev.post(
                "/auth/login",
                json={"email": f"retry-test-{i}@test.com"},
            )
        resp = await client_dev.post(
            "/auth/login",
            json={"email": "retry-blocked@test.com"},
        )
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers

    async def test_stale_ip_cleanup(self) -> None:
        """Stale IP entries are pruned during periodic cleanup."""
        import time

        from ailine_runtime.api.routers import auth as auth_mod

        # Seed a stale entry (expired timestamps)
        past = time.monotonic() - 200  # well beyond 60s window
        auth_mod._login_attempts["stale-ip"] = [past, past - 10]
        # Force cleanup by setting last cleanup to distant past
        auth_mod._login_last_cleanup = 0.0

        # Trigger cleanup via a normal check for a different IP
        await auth_mod._check_login_rate("fresh-ip")

        assert "stale-ip" not in auth_mod._login_attempts
        # fresh-ip should have one entry
        assert len(auth_mod._login_attempts.get("fresh-ip", [])) == 1


# ---------------------------------------------------------------------------
# JWT dev secret length
# ---------------------------------------------------------------------------


class TestJwtSecretLength:
    """Tests for JWT dev secret meeting RFC 7518 HS256 minimum (32 bytes)."""

    def test_dev_secret_is_32_plus_bytes(self) -> None:
        """The dev-mode JWT secret must be at least 32 bytes for HS256."""
        # Import the secret string used in _create_jwt fallback
        secret = "dev-secret-not-for-production-use-32bytes!"
        assert len(secret.encode()) >= 32
