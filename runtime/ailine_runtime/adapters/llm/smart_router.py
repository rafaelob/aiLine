"""SmartRouter adapter — routes requests to the best-fit LLM provider.

Implements ADR-049: Weighted complexity scoring with rebalanced weights
(0.25/0.25/0.25/0.15/0.10) to determine the cheapest adequate provider.

Thresholds (ADR-049):
  - score <= 0.40  -> cheap tier (e.g. Haiku, GPT-4o-mini, Gemini Flash)
  - 0.41 <= score <= 0.70 -> middle tier (e.g. Sonnet, GPT-4o, Gemini Pro)
  - score >= 0.71  -> primary tier (e.g. Opus, GPT-5.2, Gemini Ultra)

Supports two routing modes:
  - "weighted" (default): score-based complexity classification
  - "rules": hard override rules evaluated before scoring
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from ...domain.ports.llm import WebSearchResult
from ...shared.observability import get_logger

_log = get_logger("ailine.adapters.llm.smart_router")

# Dimension weights (ADR-049 rebalanced)
W_TOKENS = 0.25
W_STRUCTURED = 0.25
W_TOOLS = 0.25
W_HISTORY = 0.15
W_INTENT = 0.10

# Tier thresholds
TIER_CHEAP_MAX = 0.40
TIER_MIDDLE_MAX = 0.70


@dataclass(frozen=True)
class RouteFeatures:
    """Input features for the routing decision function."""

    token_score: float
    structured_score: float
    tool_score: float
    history_score: float
    intent_score: float
    rule_tier: str | None = None  # Hard override from rules


@dataclass(frozen=True)
class RouteDecision:
    """Output of the routing decision: tier name and computed score."""

    tier: str  # "cheap", "middle", or "primary"
    score: float
    reason: str = ""


def compute_route(features: RouteFeatures) -> RouteDecision:
    """Pure, stateless routing decision based on feature scores.

    ADR-049: Weighted complexity scoring with rebalanced weights
    (0.25/0.25/0.25/0.15/0.10). Thresholds:
    - score <= 0.40  -> cheap tier
    - 0.41-0.70      -> middle tier
    - score >= 0.71  -> primary tier

    If a rule_tier hard override is provided, it takes precedence.
    """
    if features.rule_tier is not None:
        return RouteDecision(
            tier=features.rule_tier,
            score=0.0,
            reason="rule_override",
        )

    score = (
        W_TOKENS * features.token_score
        + W_STRUCTURED * features.structured_score
        + W_TOOLS * features.tool_score
        + W_HISTORY * features.history_score
        + W_INTENT * features.intent_score
    )
    score = min(1.0, max(0.0, score))

    if score <= TIER_CHEAP_MAX:
        tier = "cheap"
    elif score <= TIER_MIDDLE_MAX:
        tier = "middle"
    else:
        tier = "primary"

    return RouteDecision(tier=tier, score=score)


@dataclass(frozen=True)
class RoutingRule:
    """Hard override rule evaluated before scoring."""

    pattern: str  # regex applied to the last user message
    tier: str  # "cheap", "middle", or "primary"
    reason: str = ""


@dataclass
class SmartRouterConfig:
    """Configuration for the SmartRouter."""

    cheap_provider: Any = None  # ChatLLM instance for cheap tier
    middle_provider: Any = None  # ChatLLM instance for middle tier
    primary_provider: Any = None  # ChatLLM instance for primary tier
    mode: str = "weighted"  # "weighted" or "rules"
    rules: list[RoutingRule] = field(default_factory=list)
    cache_ttl_seconds: int = 300  # 5 min default


class SmartRouterAdapter:
    """Routes LLM requests to the cheapest adequate provider.

    Satisfies the ``ChatLLM`` protocol.
    """

    def __init__(self, config: SmartRouterConfig) -> None:
        self._config = config
        self._cheap = config.cheap_provider
        self._middle = config.middle_provider
        self._primary = config.primary_provider
        # Fallback chain: primary -> middle -> cheap
        self._fallback = self._primary or self._middle or self._cheap
        if self._fallback is None:
            msg = "SmartRouter requires at least one provider"
            raise ValueError(msg)
        self._cache: dict[str, tuple[str, float]] = {}  # sig -> (tier, timestamp)

    @property
    def model_name(self) -> str:
        return f"smart-router({self._fallback.model_name})"

    @property
    def capabilities(self) -> dict[str, Any]:
        # web_search is available if any underlying provider supports it
        has_search = any(
            getattr(p, "capabilities", {}).get("web_search", False)
            for p in [self._cheap, self._middle, self._primary]
            if p is not None
        )
        return {
            "provider": "smart-router",
            "streaming": True,
            "tool_use": True,
            "vision": False,
            "web_search": has_search,
            "routing_mode": self._config.mode,
        }

    def _extract_features(
        self,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> RouteFeatures:
        """Extract scoring features from messages and kwargs."""
        rule_tier: str | None = None
        if self._config.mode == "rules" or self._config.rules:
            rule_tier = self._check_rules(messages)

        return RouteFeatures(
            token_score=self._score_tokens(messages),
            structured_score=self._score_structured(kwargs),
            tool_score=self._score_tools(kwargs),
            history_score=self._score_history(messages),
            intent_score=self._score_intent(messages),
            rule_tier=rule_tier,
        )

    def score_complexity(self, messages: list[dict[str, Any]], **kwargs: Any) -> float:
        """Score request complexity on [0, 1] scale."""
        features = self._extract_features(messages, **kwargs)
        decision = compute_route(features)
        return decision.score

    def classify_tier(
        self,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> str:
        """Classify request into a tier: cheap, middle, or primary."""
        features = self._extract_features(messages, **kwargs)
        decision = compute_route(features)
        return decision.tier

    def _get_provider(self, tier: str) -> Any:
        """Get the provider for a tier, with fallback."""
        if tier == "cheap" and self._cheap:
            return self._cheap
        if tier == "middle" and self._middle:
            return self._middle
        if tier == "primary" and self._primary:
            return self._primary
        return self._fallback

    async def generate(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str:
        tier = self.classify_tier(messages, **kwargs)
        provider = self._get_provider(tier)
        _log.info(
            "smart_router.route",
            tier=tier,
            provider=provider.model_name,
        )
        return await provider.generate(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def stream(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        tier = self.classify_tier(messages, **kwargs)
        provider = self._get_provider(tier)
        _log.info(
            "smart_router.route_stream",
            tier=tier,
            provider=provider.model_name,
        )
        async for chunk in provider.stream(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            yield chunk

    async def generate_with_search(
        self,
        query: str,
        *,
        max_results: int = 5,
        **kwargs: Any,
    ) -> WebSearchResult:
        """Route web search to the first provider that supports it."""
        for provider in [self._primary, self._middle, self._cheap]:
            if provider is not None and getattr(provider, "capabilities", {}).get(
                "web_search", False
            ):
                return await provider.generate_with_search(
                    query, max_results=max_results, **kwargs
                )
        return WebSearchResult(
            text="Web search not available in any configured provider.",
            sources=[],
        )

    # --- Scoring functions ---

    @staticmethod
    def _score_tokens(messages: list[dict[str, Any]]) -> float:
        """Estimate token complexity from total character length."""
        if not messages:
            return 0.0
        total_chars = sum(len(str(m.get("content", ""))) for m in messages)
        if total_chars > 8000:
            return 1.0
        if total_chars > 4000:
            return 0.7
        if total_chars > 2000:
            return 0.4
        return 0.1

    @staticmethod
    def _score_structured(kwargs: dict[str, Any]) -> float:
        """Score based on whether structured output is requested."""
        if "response_format" in kwargs or "structured_output" in kwargs:
            return 1.0
        if kwargs.get("json_mode"):
            return 0.6
        return 0.0

    @staticmethod
    def _score_tools(kwargs: dict[str, Any]) -> float:
        """Score based on tool/function calling requirements."""
        tools = kwargs.get("tools") or []
        if len(tools) > 5:
            return 1.0
        if len(tools) > 0:
            return 0.6
        return 0.0

    @staticmethod
    def _score_history(messages: list[dict[str, Any]]) -> float:
        """Score based on conversation history length."""
        turns = len(messages)
        if turns > 20:
            return 1.0
        if turns > 10:
            return 0.6
        if turns > 4:
            return 0.3
        return 0.0

    @staticmethod
    def _score_intent(messages: list[dict[str, Any]]) -> float:
        """Score based on detected complexity signals in the prompt."""
        if not messages:
            return 0.0
        last_content = str(messages[-1].get("content", ""))
        complexity_signals = [
            r"(?:analis|compar|avali|sintetiz|critic)",  # high-order thinking
            r"(?:multi|complex|detalhad|aprofundad)",  # complexity markers
            r"(?:curricul|BNCC|standard|alignment)",  # curriculum alignment
            r"(?:acessibilid|inclusiv|adapt|TEA|TDAH)",  # accessibility
        ]
        matches = sum(
            1
            for pattern in complexity_signals
            if re.search(pattern, last_content, re.IGNORECASE)
        )
        if matches >= 3:
            return 1.0
        if matches >= 2:
            return 0.6
        if matches >= 1:
            return 0.3
        return 0.0

    def _check_rules(self, messages: list[dict[str, Any]]) -> str | None:
        """Check hard override rules. Returns tier or None."""
        if not messages:
            return None
        last_content = str(messages[-1].get("content", ""))
        for rule in self._config.rules:
            if re.search(rule.pattern, last_content, re.IGNORECASE):
                _log.info(
                    "smart_router.rule_match",
                    pattern=rule.pattern,
                    tier=rule.tier,
                    reason=rule.reason,
                )
                return rule.tier
        return None
