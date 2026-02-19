"""Pydantic schemas for the Setup Wizard API.

Separated from setup_router.py for maintainability.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class SetupStatusOut(BaseModel):
    """Response for GET /setup/status."""

    completed: bool
    has_env: bool
    locked_fields: list[str]


class SetupDefaultsOut(BaseModel):
    """Response for GET /setup/defaults."""

    llm_providers: list[dict[str, Any]]
    embedding_providers: list[dict[str, Any]]
    agent_models: dict[str, dict[str, str]]
    locales: list[dict[str, str]]


class ValidateKeyIn(BaseModel):
    """Request body for POST /setup/validate."""

    provider: str
    api_key: str
    type: Literal["llm", "embedding"]


class ValidateKeyOut(BaseModel):
    """Response for POST /setup/validate."""

    valid: bool
    error: str | None = None


class SetupConfig(BaseModel):
    """Full first-run configuration payload for POST /setup/apply."""

    locale: str = "en"

    # LLM provider
    llm_provider: str
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    openrouter_api_key: str = ""

    # Embedding (locked after first setup)
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int

    # Agent models (pydantic-ai format: "provider:model")
    planner_model: str = "anthropic:claude-opus-4-6"
    executor_model: str = "google-gla:gemini-3-flash-preview"
    qg_model: str = "anthropic:claude-sonnet-4-5"
    tutor_model: str = "anthropic:claude-sonnet-4-5"

    # Database
    db_url: str = "postgresql+asyncpg://ailine:ailine_dev@localhost:5411/ailine"

    # Redis
    redis_url: str = "redis://:ailine_redis_dev@localhost:6311/0"

    # Ports
    db_host_port: int = Field(default=5411, ge=1024, le=65535)
    redis_host_port: int = Field(default=6311, ge=1024, le=65535)
    api_host_port: int = Field(default=8011, ge=1024, le=65535)
    frontend_host_port: int = Field(default=3011, ge=1024, le=65535)

    # Media (optional)
    elevenlabs_api_key: str = ""

    # Security
    jwt_secret: str = ""
    cors_origins: str = ""

    # Demo / Dev
    demo_mode: bool = False
    dev_mode: bool = False

    @field_validator("llm_provider")
    @classmethod
    def _validate_llm_provider(cls, v: str) -> str:
        allowed = {"anthropic", "openai", "gemini", "openrouter"}
        if v not in allowed:
            msg = f"llm_provider must be one of {sorted(allowed)}, got '{v}'"
            raise ValueError(msg)
        return v

    @field_validator("embedding_provider")
    @classmethod
    def _validate_embedding_provider(cls, v: str) -> str:
        allowed = {"gemini", "openai"}
        if v not in allowed:
            msg = f"embedding_provider must be one of {sorted(allowed)}, got '{v}'"
            raise ValueError(msg)
        return v

    @field_validator("embedding_dimensions")
    @classmethod
    def _validate_embedding_dimensions(cls, v: int) -> int:
        if v < 1 or v > 4096:
            msg = "embedding_dimensions must be between 1 and 4096"
            raise ValueError(msg)
        return v

    @field_validator("db_url")
    @classmethod
    def _validate_db_url(cls, v: str) -> str:
        """Validate that the database URL uses an allowed scheme."""
        allowed_prefixes = ("postgresql", "sqlite")
        if not any(v.startswith(prefix) for prefix in allowed_prefixes):
            msg = f"db_url must start with one of {allowed_prefixes}, got: {v[:30]!r}"
            raise ValueError(msg)
        _reject_suspicious_chars(v, "db_url")
        return v

    @field_validator("redis_url")
    @classmethod
    def _validate_redis_url(cls, v: str) -> str:
        """Validate that the Redis URL uses an allowed scheme."""
        if not (v.startswith("redis://") or v.startswith("rediss://")):
            msg = "redis_url must start with 'redis://' or 'rediss://'"
            raise ValueError(msg)
        _reject_suspicious_chars(v, "redis_url")
        return v


class SetupApplyOut(BaseModel):
    """Response for POST /setup/apply."""

    success: bool
    env_path: str


def _reject_suspicious_chars(url: str, label: str) -> None:
    """Reject URLs containing characters that suggest injection attempts."""
    suspicious = re.compile(r"[;`$|&<>{}()\[\]]")
    if suspicious.search(url):
        msg = f"{label} contains suspicious characters"
        raise ValueError(msg)
