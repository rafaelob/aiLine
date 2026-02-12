"""SmartRouter tier -> Pydantic AI Model bridge.

Maps the SmartRouter's routing decision (cheap/middle/primary tier)
to concrete Pydantic AI Model instances for agent.run(model=...).
"""

from __future__ import annotations

from typing import Any

from pydantic_ai.models import Model

from .providers import build_pydantic_ai_models


class PydanticAIModelSelector:
    """Maps SmartRouter tier decisions to Pydantic AI Model instances.

    Usage in a LangGraph node::

        selector = PydanticAIModelSelector.from_settings(settings)
        model = selector.select_model(messages, tier_override="primary")
        result = await agent.run(prompt, model=model, deps=deps)
    """

    def __init__(
        self,
        *,
        cheap: Model | None = None,
        middle: Model | None = None,
        primary: Model | None = None,
    ) -> None:
        self._tiers: dict[str, Model | None] = {
            "cheap": cheap,
            "middle": middle,
            "primary": primary,
        }
        self._fallback = primary or middle or cheap
        if self._fallback is None:
            msg = "At least one Pydantic AI model tier must be provided"
            raise ValueError(msg)

    def select_model(
        self,
        *,
        tier: str = "primary",
    ) -> Model:
        """Select the Pydantic AI model for the given tier."""
        model = self._tiers.get(tier) or self._fallback
        assert model is not None
        return model

    @classmethod
    def from_settings(cls, settings: Any) -> PydanticAIModelSelector:
        """Build from Settings, creating Pydantic AI model instances."""
        models = build_pydantic_ai_models(settings)
        return cls(**models)
