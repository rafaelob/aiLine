"""Setup Wizard API router -- thin routing layer.

Business logic lives in setup_service.py; schemas in setup_schemas.py.
This file contains only the FastAPI route definitions.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Header, HTTPException

from .setup_schemas import (
    SetupApplyOut,
    SetupConfig,
    SetupDefaultsOut,
    SetupStatusOut,
    ValidateKeyIn,
    ValidateKeyOut,
)
from .setup_service import (
    AGENT_MODELS,
    EMBEDDING_PROVIDERS,
    KEY_PREFIX_PATTERNS,
    LLM_PROVIDERS,
    LOCALES,
    LOCKED_AFTER_SETUP,
    build_env_content,
    enforce_locked_fields,
    env_file_path,
    is_setup_complete,
    require_setup_token,
    validate_provider_key,
)

_log = structlog.get_logger("ailine.api.setup")

router = APIRouter()


@router.get("/status", response_model=SetupStatusOut)
async def get_setup_status() -> SetupStatusOut:
    """Check whether the setup wizard has been completed."""
    path = env_file_path()
    has_env = path.exists()
    completed = is_setup_complete()
    locked = list(LOCKED_AFTER_SETUP) if completed else []

    _log.info("setup.status_checked", completed=completed, has_env=has_env)
    return SetupStatusOut(completed=completed, has_env=has_env, locked_fields=locked)


@router.get("/defaults", response_model=SetupDefaultsOut)
async def get_setup_defaults() -> SetupDefaultsOut:
    """Return available LLM/embedding providers, agent model defaults, and locales."""
    return SetupDefaultsOut(
        llm_providers=LLM_PROVIDERS,
        embedding_providers=EMBEDDING_PROVIDERS,
        agent_models=AGENT_MODELS,
        locales=LOCALES,
    )


@router.post("/validate", response_model=ValidateKeyOut)
async def validate_api_key(
    body: ValidateKeyIn,
    x_setup_token: str | None = Header(default=None),
) -> ValidateKeyOut:
    """Validate an API key by checking its prefix format."""
    require_setup_token(x_setup_token)

    provider = body.provider
    api_key = body.api_key

    if not api_key:
        return ValidateKeyOut(valid=False, error="API key is empty.")

    pattern = KEY_PREFIX_PATTERNS.get(provider)
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
async def apply_setup(
    config: SetupConfig,
    x_setup_token: str | None = Header(default=None),
) -> SetupApplyOut:
    """Apply the setup configuration by writing a .env file."""
    require_setup_token(x_setup_token)

    if is_setup_complete():
        raise HTTPException(
            status_code=409,
            detail=(
                "Setup already completed. To re-configure, "
                "delete the .env file and restart the application."
            ),
        )

    validate_provider_key(config)
    enforce_locked_fields(config)

    env_content = build_env_content(config)
    path = env_file_path()

    try:
        path.write_text(env_content, encoding="utf-8")
    except OSError as exc:
        _log.error("setup.env_write_failed", error=str(exc), path=str(path))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write .env file: {exc}",
        ) from exc

    _log.info(
        "setup.applied",
        env_path=str(path),
        llm_provider=config.llm_provider,
        embedding_provider=config.embedding_provider,
    )

    return SetupApplyOut(success=True, env_path=str(path))
