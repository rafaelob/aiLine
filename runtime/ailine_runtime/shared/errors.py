from __future__ import annotations


class AiLineError(Exception):
    """Base exception for all AiLine errors."""

    def __init__(self, message: str, *, code: str = "AILINE_ERROR", details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


class PlanGenerationError(AiLineError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="PLAN_GENERATION_ERROR", **kwargs)


class ValidationError(AiLineError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="VALIDATION_ERROR", **kwargs)


class ProviderError(AiLineError):
    def __init__(self, message: str, *, provider: str = "", code: str = "PROVIDER_ERROR", **kwargs):
        super().__init__(message, code=code, details={"provider": provider, **(kwargs.get("details") or {})})


class RateLimitError(ProviderError):
    def __init__(self, message: str = "Rate limit exceeded", **kwargs):
        super().__init__(message, code="RATE_LIMIT_ERROR", **kwargs)


class NotFoundError(AiLineError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="NOT_FOUND", **kwargs)
