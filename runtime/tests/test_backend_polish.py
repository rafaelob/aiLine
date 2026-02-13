"""Tests for backend architecture polish features.

Covers:
- Path metric normalization (high-cardinality prevention)
- JWT verified decode (HS256 with exp/iss validation)
- Container validation (structured ValidationResult)
"""

from __future__ import annotations

import base64
import json
import os
import time
from unittest.mock import patch

import pytest

from ailine_runtime.api.app import normalize_metric_path
from ailine_runtime.api.middleware.tenant_context import (
    _unverified_jwt_decode,
    _verified_jwt_decode,
)
from ailine_runtime.shared.config import Settings
from ailine_runtime.shared.container import Container, ValidationResult


# ---------------------------------------------------------------------------
# Path normalization tests
# ---------------------------------------------------------------------------


class TestNormalizeMetricPath:
    def test_uuid_v4_replaced(self) -> None:
        path = "/plans/550e8400-e29b-41d4-a716-446655440000"
        assert normalize_metric_path(path) == "/plans/:id"

    def test_uuid_v7_replaced(self) -> None:
        path = "/tutors/0192d4e0-b4ff-7f9e-8a1c-4b2e3d5f6a7b"
        assert normalize_metric_path(path) == "/tutors/:id"

    def test_numeric_id_replaced(self) -> None:
        path = "/materials/123"
        assert normalize_metric_path(path) == "/materials/:id"

    def test_multiple_ids_replaced(self) -> None:
        path = "/tutors/550e8400-e29b-41d4-a716-446655440000/sessions/99"
        assert normalize_metric_path(path) == "/tutors/:id/sessions/:id"

    def test_static_path_unchanged(self) -> None:
        path = "/health/ready"
        assert normalize_metric_path(path) == "/health/ready"

    def test_root_path(self) -> None:
        assert normalize_metric_path("/") == "/"

    def test_metrics_path_unchanged(self) -> None:
        assert normalize_metric_path("/metrics") == "/metrics"

    def test_plans_generate_unchanged(self) -> None:
        assert normalize_metric_path("/plans/generate") == "/plans/generate"

    def test_mixed_uuid_and_text(self) -> None:
        path = "/curriculum/550e8400-e29b-41d4-a716-446655440000/lessons"
        assert normalize_metric_path(path) == "/curriculum/:id/lessons"

    def test_empty_string(self) -> None:
        assert normalize_metric_path("") == ""

    def test_large_numeric_id(self) -> None:
        path = "/materials/9999999999"
        assert normalize_metric_path(path) == "/materials/:id"

    def test_alphanumeric_slug_not_replaced(self) -> None:
        """Slugs like 'abc123' should NOT be replaced (not pure numeric)."""
        path = "/demo/abc123"
        assert normalize_metric_path(path) == "/demo/abc123"


# ---------------------------------------------------------------------------
# JWT decode tests
# ---------------------------------------------------------------------------


def _make_jwt_hs256(payload: dict, secret: str = "test-secret") -> str:
    """Create a HS256-signed JWT for testing (requires PyJWT)."""
    try:
        import jwt as pyjwt

        return pyjwt.encode(payload, secret, algorithm="HS256")
    except ImportError:
        pytest.skip("PyJWT not installed")


def _make_unsigned_jwt(payload: dict) -> str:
    """Create an unsigned JWT (alg: none) for testing unverified decode."""
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "none"}).encode()
    ).rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).rstrip(b"=").decode()
    return f"{header}.{body}."


class TestUnverifiedJwtDecode:
    def test_extracts_sub_claim(self) -> None:
        token = _make_unsigned_jwt({"sub": "teacher-001"})
        assert _unverified_jwt_decode(token) == "teacher-001"

    def test_missing_sub_returns_none(self) -> None:
        token = _make_unsigned_jwt({"name": "John"})
        assert _unverified_jwt_decode(token) is None

    def test_malformed_token_returns_none(self) -> None:
        assert _unverified_jwt_decode("not-a-jwt") is None

    def test_empty_token_returns_none(self) -> None:
        assert _unverified_jwt_decode("") is None

    def test_single_dot_returns_none(self) -> None:
        assert _unverified_jwt_decode("header.") is None


class TestVerifiedJwtDecode:
    """Tests for _verified_jwt_decode (requires PyJWT)."""

    def test_valid_token_returns_sub(self) -> None:
        secret = "my-test-secret"
        payload = {
            "sub": "teacher-jwt-verified",
            "exp": int(time.time()) + 3600,
        }
        token = _make_jwt_hs256(payload, secret)
        result = _verified_jwt_decode(token, secret)
        assert result == "teacher-jwt-verified"

    def test_expired_token_returns_none(self) -> None:
        secret = "my-test-secret"
        payload = {
            "sub": "teacher-expired",
            "exp": int(time.time()) - 3600,  # expired 1 hour ago
        }
        token = _make_jwt_hs256(payload, secret)
        result = _verified_jwt_decode(token, secret)
        assert result is None

    def test_wrong_secret_returns_none(self) -> None:
        payload = {
            "sub": "teacher-wrong-secret",
            "exp": int(time.time()) + 3600,
        }
        token = _make_jwt_hs256(payload, "correct-secret")
        result = _verified_jwt_decode(token, "wrong-secret")
        assert result is None

    def test_issuer_mismatch_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AILINE_JWT_ISSUER", "expected-issuer")
        secret = "my-test-secret"
        payload = {
            "sub": "teacher-iss",
            "exp": int(time.time()) + 3600,
            "iss": "wrong-issuer",
        }
        token = _make_jwt_hs256(payload, secret)
        result = _verified_jwt_decode(token, secret)
        assert result is None

    def test_issuer_match_succeeds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AILINE_JWT_ISSUER", "ailine-auth")
        secret = "my-test-secret"
        payload = {
            "sub": "teacher-iss-ok",
            "exp": int(time.time()) + 3600,
            "iss": "ailine-auth",
        }
        token = _make_jwt_hs256(payload, secret)
        result = _verified_jwt_decode(token, secret)
        assert result == "teacher-iss-ok"

    def test_missing_exp_returns_none(self) -> None:
        """Tokens without exp claim should be rejected."""
        secret = "my-test-secret"
        try:
            import jwt as pyjwt

            # Manually encode without exp to bypass PyJWT's own checks
            token = pyjwt.encode({"sub": "teacher-no-exp"}, secret, algorithm="HS256")
            result = _verified_jwt_decode(token, secret)
            assert result is None
        except ImportError:
            pytest.skip("PyJWT not installed")

    def test_pyjwt_not_installed_returns_none(self) -> None:
        """When PyJWT is not importable, should return None and log warning."""
        with patch.dict("sys.modules", {"jwt": None}):
            result = _verified_jwt_decode("some.token.here", "secret")
            assert result is None


# ---------------------------------------------------------------------------
# JWT integration via _extract_teacher_id_from_jwt
# ---------------------------------------------------------------------------


class TestExtractTeacherIdFromJwt:
    """Integration tests for the main JWT extraction function."""

    def test_unverified_mode_no_secret(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without AILINE_JWT_SECRET, unverified decode is used."""
        monkeypatch.delenv("AILINE_JWT_SECRET", raising=False)
        from ailine_runtime.api.middleware.tenant_context import (
            _extract_teacher_id_from_jwt,
        )

        token = _make_unsigned_jwt({"sub": "teacher-unverified"})
        assert _extract_teacher_id_from_jwt(token) == "teacher-unverified"

    def test_verified_mode_valid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """With AILINE_JWT_SECRET, verified decode is used."""
        secret = "integration-test-secret"
        monkeypatch.setenv("AILINE_JWT_SECRET", secret)
        monkeypatch.delenv("AILINE_JWT_ISSUER", raising=False)
        from ailine_runtime.api.middleware.tenant_context import (
            _extract_teacher_id_from_jwt,
        )

        payload = {
            "sub": "teacher-verified",
            "exp": int(time.time()) + 3600,
        }
        token = _make_jwt_hs256(payload, secret)
        assert _extract_teacher_id_from_jwt(token) == "teacher-verified"

    def test_verified_mode_expired_rejects(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """With AILINE_JWT_SECRET, expired tokens are rejected (no fallback)."""
        secret = "integration-test-secret"
        monkeypatch.setenv("AILINE_JWT_SECRET", secret)
        monkeypatch.delenv("AILINE_JWT_ISSUER", raising=False)
        from ailine_runtime.api.middleware.tenant_context import (
            _extract_teacher_id_from_jwt,
        )

        payload = {
            "sub": "teacher-expired",
            "exp": int(time.time()) - 3600,
        }
        token = _make_jwt_hs256(payload, secret)
        # Should NOT fall through to unverified decode
        assert _extract_teacher_id_from_jwt(token) is None


# ---------------------------------------------------------------------------
# Container validation tests
# ---------------------------------------------------------------------------


class TestContainerValidation:
    def test_validate_returns_validation_result(self) -> None:
        settings = Settings(
            llm={"provider": "fake", "api_key": ""},
            redis={"url": ""},
        )
        container = Container.build(settings)
        result = container.validate()
        assert isinstance(result, ValidationResult)
        assert result.ok is True
        assert result.missing_critical == []

    def test_validate_reports_missing_optional(self) -> None:
        settings = Settings(
            llm={"provider": "fake", "api_key": ""},
            embedding={"provider": "gemini", "api_key": ""},
            redis={"url": ""},
        )
        container = Container.build(settings)
        result = container.validate()
        assert result.ok is True
        # vectorstore and embeddings should be in missing_optional
        assert "vectorstore" in result.missing_optional
        assert "embeddings" in result.missing_optional

    def test_validate_production_raises_without_llm(self) -> None:
        """Production mode should raise if llm is None."""
        settings = Settings(
            llm={"provider": "fake", "api_key": ""},
            redis={"url": ""},
            env="production",
        )
        # Build with fake llm first, then force llm to None
        container = Container.build(settings)
        # Create a new container with llm=None to test production validation
        container_no_llm = Container(
            settings=Settings(env="production"),
            llm=None,
            event_bus=container.event_bus,
        )
        with pytest.raises(ValueError, match="missing critical ports"):
            container_no_llm.validate()

    def test_validate_dev_mode_no_raise_without_llm(self) -> None:
        """Development mode should NOT raise even if llm is None."""
        settings = Settings(env="development")
        container_no_llm = Container(
            settings=settings,
            llm=None,
            event_bus=None,
        )
        result = container_no_llm.validate()
        assert result.ok is False
        assert "llm" in result.missing_critical
        assert "event_bus" in result.missing_critical

    def test_validation_result_tuple_unpacking(self) -> None:
        """ValidationResult should support tuple unpacking."""
        result = ValidationResult(ok=True, missing_critical=[], missing_optional=["ocr"])
        ok, critical, optional = result
        assert ok is True
        assert critical == []
        assert optional == ["ocr"]
