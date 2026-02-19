"""Business logic for the Setup Wizard (env generation, validation).

Separated from setup_router.py for maintainability.
"""

from __future__ import annotations

import hmac
import os
import re
import secrets
from pathlib import Path
from typing import Any

import structlog
from fastapi import HTTPException

from .setup_schemas import SetupConfig

_log = structlog.get_logger("ailine.api.setup")

# Project root: setup_service.py -> routers -> api -> ailine_runtime -> runtime -> aiLine
_PROJECT_ROOT = Path(__file__).resolve().parents[4]


# ---------------------------------------------------------------------------
# Setup Token
# ---------------------------------------------------------------------------

_SETUP_TOKEN: str | None = None


def _get_or_create_setup_token() -> str:
    """Return the current setup token, creating one on first call."""
    global _SETUP_TOKEN
    if _SETUP_TOKEN is not None:
        return _SETUP_TOKEN

    env_token = os.getenv("AILINE_SETUP_TOKEN", "").strip()
    if env_token:
        _SETUP_TOKEN = env_token
    else:
        _SETUP_TOKEN = secrets.token_urlsafe(32)
        import sys
        print(
            f"\n{'=' * 60}\n"
            f"  AILINE SETUP TOKEN: {_SETUP_TOKEN}\n"
            f"  Use this in the X-Setup-Token header for /setup/apply\n"
            f"{'=' * 60}\n",
            file=sys.stderr,
            flush=True,
        )
        _log.info("setup_token_generated", msg="Setup token printed to stderr")
    return _SETUP_TOKEN


def require_setup_token(x_setup_token: str | None) -> None:
    """Validate the setup token for write endpoints."""
    if is_setup_complete():
        raise HTTPException(
            status_code=409,
            detail=(
                "Setup is already complete. To reconfigure, manually edit "
                "the .env file or remove AILINE_SETUP_COMPLETE."
            ),
        )

    expected = _get_or_create_setup_token()
    if not x_setup_token or not hmac.compare_digest(x_setup_token, expected):
        raise HTTPException(
            status_code=403,
            detail=(
                "Invalid or missing setup token. Provide the token shown "
                "in the server console via the X-Setup-Token header."
            ),
        )


# ---------------------------------------------------------------------------
# Provider catalogs
# ---------------------------------------------------------------------------

LLM_PROVIDERS: list[dict[str, Any]] = [
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

EMBEDDING_PROVIDERS: list[dict[str, Any]] = [
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

AGENT_MODELS: dict[str, dict[str, str]] = {
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

LOCALES: list[dict[str, str]] = [
    {"id": "en", "name": "English"},
    {"id": "pt-BR", "name": "Portugues (Brasil)"},
    {"id": "es", "name": "Espanol"},
]

# Fields locked after first setup
LOCKED_AFTER_SETUP = ["embedding_provider", "embedding_model", "embedding_dimensions"]

# API key prefix patterns for format validation
KEY_PREFIX_PATTERNS: dict[str, re.Pattern[str]] = {
    "anthropic": re.compile(r"^sk-ant-"),
    "openai": re.compile(r"^sk-proj-"),
    "gemini": re.compile(r"^AIza"),
    "openrouter": re.compile(r"^sk-or-"),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def env_file_path() -> Path:
    """Return the path to the .env file at the project root."""
    return _PROJECT_ROOT / ".env"


def is_setup_complete() -> bool:
    """Check if AILINE_SETUP_COMPLETE=true is present in the .env file."""
    path = env_file_path()
    if not path.exists():
        return False
    content = path.read_text(encoding="utf-8")
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        key, _, value = stripped.partition("=")
        if key.strip() == "AILINE_SETUP_COMPLETE":
            return value.strip().strip('"').strip("'").lower() in ("true", "1", "yes")
    return False


def build_env_content(config: SetupConfig) -> str:
    """Generate .env file content from the setup configuration."""
    jwt_secret = config.jwt_secret or secrets.token_urlsafe(48)
    cors_origins = (
        config.cors_origins
        or f"http://localhost:{config.frontend_host_port}"
    )

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
        f'GOOGLE_API_KEY="{config.google_api_key}"',
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
    """Extract user, password, and database name from a PostgreSQL URL."""
    from urllib.parse import unquote, urlparse

    try:
        parsed = urlparse(db_url)
        user = unquote(parsed.username or "")
        password = unquote(parsed.password or "")
        db_name = (parsed.path or "").lstrip("/") or ""
        if user and password and db_name:
            return user, password, db_name
    except Exception:
        pass
    return "ailine", "ailine_dev", "ailine"


def _extract_redis_password_line(redis_url: str) -> str:
    """Generate the REDIS_PASSWORD env line from a Redis URL."""
    match = re.search(r"redis://(?::([^@]+)@)?", redis_url)
    password = match.group(1) if match and match.group(1) else ""
    return f'REDIS_PASSWORD="{password}"'


def validate_provider_key(config: SetupConfig) -> None:
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


def enforce_locked_fields(config: SetupConfig) -> None:
    """When re-running setup, ensure locked embedding fields match."""
    path = env_file_path()
    if not path.exists():
        return

    existing: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
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
