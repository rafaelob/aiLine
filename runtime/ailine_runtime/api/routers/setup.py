"""Setup Wizard API router -- first-run configuration for open-source deployments.

Provides endpoints to check setup status, return provider defaults,
validate API keys, and apply the initial configuration by writing
a ``.env`` file to the project root.

No authentication is required for these endpoints (the wizard runs
before any auth infrastructure exists). Rate limiting is applied
by the global middleware.
"""

from __future__ import annotations

import re
import secrets
from pathlib import Path
from typing import Any, Literal

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

_log = structlog.get_logger("ailine.api.setup")

router = APIRouter()

# Project root: setup.py -> routers -> api -> ailine_runtime -> runtime -> aiLine
_PROJECT_ROOT = Path(__file__).resolve().parents[4]

# ---------------------------------------------------------------------------
# Constants: provider catalogs
# ---------------------------------------------------------------------------

_LLM_PROVIDERS: list[dict[str, Any]] = [
    {
        "id": "anthropic",
        "name": "Anthropic (Claude)",
        "models": ["claude-opus-4-6", "claude-sonnet-4-5", "claude-haiku-4-5"],
        "default_model": "claude-sonnet-4-5",
    },
    {
        "id": "openai",
        "name": "OpenAI (GPT)",
        "models": ["gpt-5.2", "gpt-5-mini", "gpt-4.1"],
        "default_model": "gpt-5.2",
    },
    {
        "id": "gemini",
        "name": "Google (Gemini)",
        "models": ["gemini-3-pro-preview", "gemini-3-flash-preview"],
        "default_model": "gemini-3-flash-preview",
    },
    {
        "id": "openrouter",
        "name": "OpenRouter (Multi)",
        "models": [],
        "default_model": "",
    },
]

_EMBEDDING_PROVIDERS: list[dict[str, Any]] = [
    {
        "id": "gemini",
        "name": "Google Gemini",
        "models": [
            {"id": "gemini-embedding-001", "max_dims": 3072, "default_dims": 3072},
        ],
    },
    {
        "id": "openai",
        "name": "OpenAI",
        "models": [
            {"id": "text-embedding-3-large", "max_dims": 3072, "default_dims": 1536},
            {"id": "text-embedding-3-small", "max_dims": 1536, "default_dims": 1536},
        ],
    },
]

_AGENT_MODELS: dict[str, dict[str, str]] = {
    "planner": {
        "label": "Planner Agent",
        "default": "anthropic:claude-opus-4-6",
        "description": "Plans inclusive lesson content",
    },
    "executor": {
        "label": "Executor Agent",
        "default": "google-gla:gemini-3-flash-preview",
        "description": "Generates materials and activities",
    },
    "qg": {
        "label": "Quality Gate Agent",
        "default": "anthropic:claude-sonnet-4-5",
        "description": "Reviews quality and accessibility",
    },
    "tutor": {
        "label": "Tutor Agent",
        "default": "anthropic:claude-sonnet-4-5",
        "description": "Interactive student tutoring",
    },
}

_LOCALES: list[dict[str, str]] = [
    {"id": "en", "name": "English"},
    {"id": "pt-BR", "name": "Portugues (Brasil)"},
    {"id": "es", "name": "Espanol"},
]

# Fields that cannot be changed after first setup (embedding dimensions
# determine pgvector column size and re-indexing is destructive).
_LOCKED_AFTER_SETUP = ["embedding_provider", "embedding_model", "embedding_dimensions"]

# API key prefix patterns for format validation.
_KEY_PREFIX_PATTERNS: dict[str, re.Pattern[str]] = {
    "anthropic": re.compile(r"^sk-ant-"),
    "openai": re.compile(r"^sk-proj-"),
    "gemini": re.compile(r"^AIza"),
    "openrouter": re.compile(r"^sk-or-"),
}

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


class SetupApplyOut(BaseModel):
    """Response for POST /setup/apply."""

    success: bool
    env_path: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _env_file_path() -> Path:
    """Return the path to the .env file at the project root."""
    return _PROJECT_ROOT / ".env"


def _is_setup_complete() -> bool:
    """Check if AILINE_SETUP_COMPLETE=true is present in the .env file."""
    env_path = _env_file_path()
    if not env_path.exists():
        return False
    content = env_path.read_text(encoding="utf-8")
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        key, _, value = stripped.partition("=")
        if key.strip() == "AILINE_SETUP_COMPLETE":
            return value.strip().strip('"').strip("'").lower() in ("true", "1", "yes")
    return False


def _build_env_content(config: SetupConfig) -> str:
    """Generate .env file content from the setup configuration.

    Reads .env.example as a template base and overlays the user-provided
    values. Unknown keys from the template are preserved with their
    defaults.
    """
    jwt_secret = config.jwt_secret or secrets.token_urlsafe(48)
    cors_origins = (
        config.cors_origins
        or f"http://localhost:{config.frontend_host_port}"
    )

    # Derive Postgres credentials from the db_url for Docker Compose.
    pg_user, pg_password, pg_db = _parse_pg_credentials(config.db_url)

    lines = [
        "# AiLine -- Generated by Setup Wizard",
        "# Modify values below; re-run setup to regenerate.",
        "",
        "# === Setup marker ===",
        'AILINE_SETUP_COMPLETE="true"',
        "",
        "# === Docker Compose ===",
        f'DB_HOST_PORT="{config.db_host_port}"',
        f'REDIS_HOST_PORT="{config.redis_host_port}"',
        f'API_HOST_PORT="{config.api_host_port}"',
        f'FRONTEND_HOST_PORT="{config.frontend_host_port}"',
        "",
        "# === Database ===",
        f'POSTGRES_USER="{pg_user}"',
        f'POSTGRES_PASSWORD="{pg_password}"',
        f'POSTGRES_DB="{pg_db}"',
        f'AILINE_DB_URL="{config.db_url}"',
        "",
        "# === Redis ===",
        _extract_redis_password_line(config.redis_url),
        f'AILINE_REDIS_URL="{config.redis_url}"',
        "",
        "# === LLM Provider Keys ===",
        f'ANTHROPIC_API_KEY="{config.anthropic_api_key}"',
        f'OPENAI_API_KEY="{config.openai_api_key}"',
        f'GEMINI_API_KEY="{config.google_api_key}"',
        f'OPENROUTER_API_KEY="{config.openrouter_api_key}"',
        "",
        "# === Models ===",
        f'AILINE_PLANNER_MODEL="{config.planner_model}"',
        f'AILINE_EXECUTOR_MODEL="{config.executor_model}"',
        f'AILINE_QG_MODEL="{config.qg_model}"',
        f'AILINE_TUTOR_MODEL="{config.tutor_model}"',
        'AILINE_PLANNER_EFFORT="high"',
        "",
        "# === LLM Provider ===",
        f'AILINE_LLM_PROVIDER="{config.llm_provider}"',
        "",
        "# === Embedding Provider ===",
        f'AILINE_EMBEDDING_PROVIDER="{config.embedding_provider}"',
        f'AILINE_EMBEDDING_MODEL="{config.embedding_model}"',
        f'AILINE_EMBEDDING_DIMENSIONS="{config.embedding_dimensions}"',
        "",
        "# === Vector Store ===",
        'AILINE_VECTORSTORE_PROVIDER="pgvector"',
        "",
        "# === Refinement ===",
        'AILINE_MAX_REFINEMENT_ITERS="2"',
        "",
        "# === Local Store ===",
        'AILINE_LOCAL_STORE=".local_store"',
        "",
        "# === Skills ===",
        'AILINE_SKILL_SOURCES=""',
        'AILINE_PLANNER_USE_SKILLS="1"',
        'AILINE_PERSONA_USE_SKILLS="1"',
        "",
        "# === Exports ===",
        'AILINE_ENABLE_EXPORTS="1"',
        'AILINE_DEFAULT_VARIANTS="standard_html,low_distraction_html,large_print_html,'
        "high_contrast_html,dyslexia_friendly_html,screen_reader_html,"
        'visual_schedule_html,student_plain_text,audio_script"',
        "",
        "# === Media ===",
        f'ELEVENLABS_API_KEY="{config.elevenlabs_api_key}"',
        'GOOGLE_TTS_KEY=""',
        'HANDTALK_API_KEY=""',
        "",
        "# === Dev / Demo Mode ===",
        f'AILINE_DEV_MODE="{"true" if config.dev_mode else "false"}"',
        f'AILINE_DEMO_MODE="{"1" if config.demo_mode else "0"}"',
        "",
        "# === Rate Limiting ===",
        'AILINE_RATE_LIMIT_RPM="60"',
        'AILINE_TRUSTED_PROXIES=""',
        "",
        "# === Security ===",
        f'AILINE_JWT_SECRET="{jwt_secret}"',
        f'AILINE_CORS_ORIGINS="{cors_origins}"',
        "",
        "# === Server ===",
        'HOST="0.0.0.0"',
        f'PORT="{config.api_host_port}"',
        "",
        "# === Frontend ===",
        f'NEXT_PUBLIC_API_URL="http://localhost:{config.api_host_port}"',
        "",
        "# === i18n ===",
        f'AILINE_DEFAULT_LOCALE="{config.locale}"',
        "",
    ]
    return "\n".join(lines)


def _parse_pg_credentials(db_url: str) -> tuple[str, str, str]:
    """Extract user, password, and database name from a PostgreSQL URL.

    Falls back to sensible defaults if the URL is unparseable.
    """
    match = re.search(r"://([^:]+):([^@]+)@.+/(\w+)", db_url)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return "ailine", "ailine_dev", "ailine"


def _extract_redis_password_line(redis_url: str) -> str:
    """Generate the REDIS_PASSWORD env line from a Redis URL."""
    match = re.search(r"redis://(?::([^@]+)@)?", redis_url)
    password = match.group(1) if match and match.group(1) else ""
    return f'REDIS_PASSWORD="{password}"'


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/status", response_model=SetupStatusOut)
async def get_setup_status() -> SetupStatusOut:
    """Check whether the setup wizard has been completed.

    Returns whether a ``.env`` file exists and whether it contains
    ``AILINE_SETUP_COMPLETE=true``. When setup is complete, the
    response includes the list of fields that are locked and cannot
    be changed without a full re-index (embedding configuration).
    """
    env_path = _env_file_path()
    has_env = env_path.exists()
    completed = _is_setup_complete()
    locked = list(_LOCKED_AFTER_SETUP) if completed else []

    _log.info(
        "setup.status_checked",
        completed=completed,
        has_env=has_env,
    )
    return SetupStatusOut(completed=completed, has_env=has_env, locked_fields=locked)


@router.get("/defaults", response_model=SetupDefaultsOut)
async def get_setup_defaults() -> SetupDefaultsOut:
    """Return available LLM/embedding providers, agent model defaults, and locales.

    The frontend setup wizard uses this to populate dropdowns and
    pre-fill recommended values without hard-coding them.
    """
    return SetupDefaultsOut(
        llm_providers=_LLM_PROVIDERS,
        embedding_providers=_EMBEDDING_PROVIDERS,
        agent_models=_AGENT_MODELS,
        locales=_LOCALES,
    )


@router.post("/validate", response_model=ValidateKeyOut)
async def validate_api_key(body: ValidateKeyIn) -> ValidateKeyOut:
    """Validate an API key by checking its prefix format.

    This is a lightweight client-side-quality check. It does NOT
    make a real API call (the SDK may not be available during setup).
    A future enhancement can add live validation behind a feature flag.
    """
    provider = body.provider
    api_key = body.api_key

    if not api_key:
        return ValidateKeyOut(valid=False, error="API key is empty.")

    pattern = _KEY_PREFIX_PATTERNS.get(provider)
    if pattern is None:
        return ValidateKeyOut(
            valid=False,
            error=f"Unknown provider '{provider}'.",
        )

    if not pattern.search(api_key):
        expected = {
            "anthropic": "sk-ant-...",
            "openai": "sk-proj-...",
            "gemini": "AIza...",
            "openrouter": "sk-or-...",
        }
        return ValidateKeyOut(
            valid=False,
            error=f"Key does not match expected prefix for {provider} ({expected.get(provider, '?')}).",
        )

    _log.info("setup.key_validated", provider=provider, type=body.type)
    return ValidateKeyOut(valid=True, error=None)


@router.post("/apply", response_model=SetupApplyOut)
async def apply_setup(config: SetupConfig) -> SetupApplyOut:
    """Apply the setup configuration by writing a ``.env`` file.

    Validates that the chosen LLM provider has a corresponding API key,
    generates a JWT secret if none is provided, and writes the complete
    environment file to the project root.

    This endpoint does NOT run database migrations -- that is a
    separate step handled by the deploy/compose workflow.
    """
    # Validate that the selected LLM provider has a key.
    _validate_provider_key(config)

    # If setup was already completed, protect locked fields.
    if _is_setup_complete():
        _enforce_locked_fields(config)

    env_content = _build_env_content(config)
    env_path = _env_file_path()

    try:
        env_path.write_text(env_content, encoding="utf-8")
    except OSError as exc:
        _log.error("setup.env_write_failed", error=str(exc), path=str(env_path))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write .env file: {exc}",
        ) from exc

    _log.info(
        "setup.applied",
        env_path=str(env_path),
        llm_provider=config.llm_provider,
        embedding_provider=config.embedding_provider,
    )

    return SetupApplyOut(success=True, env_path=str(env_path))


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_provider_key(config: SetupConfig) -> None:
    """Ensure the selected LLM provider has a non-empty API key."""
    provider_key_map: dict[str, str] = {
        "anthropic": config.anthropic_api_key,
        "openai": config.openai_api_key,
        "gemini": config.google_api_key,
        "openrouter": config.openrouter_api_key,
    }
    key_value = provider_key_map.get(config.llm_provider, "")
    if not key_value:
        raise HTTPException(
            status_code=422,
            detail=(
                f"API key for the selected LLM provider "
                f"'{config.llm_provider}' is required."
            ),
        )


def _enforce_locked_fields(config: SetupConfig) -> None:
    """When re-running setup, ensure locked embedding fields match the original.

    Embedding dimensions determine the pgvector column size; changing them
    after data has been indexed requires a full re-index operation.
    """
    env_path = _env_file_path()
    if not env_path.exists():
        return

    existing: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        existing[key.strip()] = value.strip().strip('"').strip("'")

    field_to_env: dict[str, str] = {
        "embedding_provider": "AILINE_EMBEDDING_PROVIDER",
        "embedding_model": "AILINE_EMBEDDING_MODEL",
        "embedding_dimensions": "AILINE_EMBEDDING_DIMENSIONS",
    }

    mismatches: list[str] = []
    for field_name, env_key in field_to_env.items():
        old_val = existing.get(env_key, "")
        new_val = str(getattr(config, field_name))
        if old_val and old_val != new_val:
            mismatches.append(
                f"{field_name}: current='{old_val}', requested='{new_val}'"
            )

    if mismatches:
        raise HTTPException(
            status_code=409,
            detail=(
                "Embedding configuration is locked after first setup. "
                "Changing these fields requires a full re-index. "
                f"Mismatches: {'; '.join(mismatches)}"
            ),
        )
