"""Factory: Settings -> Pydantic AI Model instances per tier."""

from __future__ import annotations

from typing import Any

from pydantic_ai.models import Model


def build_pydantic_ai_models(settings: Any) -> dict[str, Model | None]:
    """Build tier-mapped Pydantic AI models from Settings.

    For MVP, all tiers map to the same provider/model.
    Post-MVP: configure per-tier models in Settings.
    """
    provider = settings.llm.provider
    model_name = settings.llm.model
    api_key = settings.llm.api_key or _resolve_key(settings, provider)

    primary = _build_model(provider, model_name, api_key)

    return {
        "cheap": primary,
        "middle": primary,
        "primary": primary,
    }


def _build_model(provider: str, model: str, api_key: str) -> Model | None:
    """Build a Pydantic AI Model from provider/model/key."""
    if not api_key and provider != "fake":
        return None

    if provider == "anthropic":
        from pydantic_ai.models.anthropic import AnthropicModel

        return AnthropicModel(model, api_key=api_key)

    if provider in ("openai", "openrouter"):
        from pydantic_ai.models.openai import OpenAIModel

        kwargs: dict[str, Any] = {"api_key": api_key}
        if provider == "openrouter":
            kwargs["base_url"] = "https://openrouter.ai/api/v1"
        return OpenAIModel(model, **kwargs)

    if provider == "gemini":
        from pydantic_ai.models.google import GoogleModel

        return GoogleModel(model, api_key=api_key)

    return None


def _resolve_key(settings: Any, provider: str) -> str:
    """Resolve API key from top-level settings."""
    mapping = {
        "anthropic": settings.anthropic_api_key,
        "openai": settings.openai_api_key,
        "gemini": settings.google_api_key,
        "openrouter": settings.openrouter_api_key,
    }
    return mapping.get(provider, "")
