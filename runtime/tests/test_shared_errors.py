"""Tests for shared.errors -- domain exception hierarchy."""

from __future__ import annotations

from ailine_runtime.shared.errors import (
    AiLineError,
    NotFoundError,
    PlanGenerationError,
    ProviderError,
    RateLimitError,
    ValidationError,
)


class TestAiLineError:
    def test_base_error(self):
        err = AiLineError("something broke", code="TEST_ERR", details={"key": "val"})
        assert str(err) == "something broke"
        assert err.code == "TEST_ERR"
        assert err.message == "something broke"
        assert err.details == {"key": "val"}

    def test_defaults(self):
        err = AiLineError("oops")
        assert err.code == "AILINE_ERROR"
        assert err.details == {}

    def test_is_exception(self):
        assert issubclass(AiLineError, Exception)


class TestPlanGenerationError:
    def test_code(self):
        err = PlanGenerationError("plan failed")
        assert err.code == "PLAN_GENERATION_ERROR"
        assert isinstance(err, AiLineError)


class TestValidationError:
    def test_code(self):
        err = ValidationError("bad input")
        assert err.code == "VALIDATION_ERROR"
        assert isinstance(err, AiLineError)


class TestProviderError:
    def test_code_and_provider(self):
        err = ProviderError("timeout", provider="anthropic")
        assert err.code == "PROVIDER_ERROR"
        assert err.details["provider"] == "anthropic"
        assert isinstance(err, AiLineError)


class TestRateLimitError:
    def test_default_message(self):
        err = RateLimitError()
        assert "Rate limit" in str(err)
        assert err.code == "RATE_LIMIT_ERROR"
        assert isinstance(err, ProviderError)


class TestNotFoundError:
    def test_code(self):
        err = NotFoundError("missing resource")
        assert err.code == "NOT_FOUND"
        assert isinstance(err, AiLineError)
