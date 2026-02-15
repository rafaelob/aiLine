"""SmartRouter adapter -- routes requests to the best-fit LLM provider.

Implements ADR-049: Weighted complexity scoring with rebalanced weights
(0.25/0.25/0.25/0.15/0.10) to determine the cheapest adequate provider.

Thresholds (ADR-049):
  - score <= 0.40  -> cheap tier (e.g. Haiku, GPT-4o-mini, Gemini Flash)
  - 0.41 <= score <= 0.70 -> middle tier (e.g. Sonnet, GPT-4o, Gemini Pro)
  - score >= 0.71  -> primary tier (e.g. Opus, GPT-5.2, Gemini Ultra)

Supports two routing modes:
  - "weighted" (default): score-based complexity classification
  - "rules": hard override rules evaluated before scoring

Observability:
  - Every routing decision is captured as a RouteMetrics entry
  - In-memory ring buffer (default 100) for recent metrics retrieval
  - Structured logging of routing decisions, latency, and fallback attempts

Types and pure scoring functions live in routing_types.py. This module
re-exports them for backward compatibility.
"""

from __future__ import annotations

import re
import time
from collections import deque
from collections.abc import AsyncIterator
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from ...domain.ports.llm import ChatLLM, WebSearchResult
from ...shared.observability import get_logger
from ...shared.tracing import trace_llm_call

# Re-export types and functions so existing imports keep working
from .routing_types import (
    DEFAULT_METRICS_CAPACITY,
    TIER_CHEAP_MAX,
    TIER_MIDDLE_MAX,
    W_HISTORY,
    W_INTENT,
    W_STRUCTURED,
    W_TOKENS,
    W_TOOLS,
    RouteDecision,
    RouteFeatures,
    RouteMetrics,
    RoutingRule,
    ScoreBreakdown,
    SmartRouterConfig,
    compute_route,
    estimate_tokens,
    score_history,
    score_intent,
    score_structured,
    score_tokens,
    score_tools,
)

__all__ = [
    "DEFAULT_METRICS_CAPACITY",
    "TIER_CHEAP_MAX",
    "TIER_MIDDLE_MAX",
    "W_HISTORY",
    "W_INTENT",
    "W_STRUCTURED",
    "W_TOKENS",
    "W_TOOLS",
    "RouteDecision",
    "RouteFeatures",
    "RouteMetrics",
    "RoutingRule",
    "ScoreBreakdown",
    "SmartRouterAdapter",
    "SmartRouterConfig",
    "compute_route",
]

_log = get_logger("ailine.adapters.llm.smart_router")


class SmartRouterAdapter:
    """Routes LLM requests to the cheapest adequate provider.

    Satisfies the ``ChatLLM`` protocol. Captures telemetry for every
    routing decision in an in-memory ring buffer.

    Graceful degradation:
        When the provider selected for a tier is unavailable (not configured),
        the router falls back through the chain: primary -> middle -> cheap.
        At least one provider must be present at construction time. If a
        call to a provider raises an exception, the caller receives the
        error directly (no automatic retry across tiers) -- retries are
        handled upstream by the LangGraph ``RetryPolicy``.
    """

    def __init__(self, config: SmartRouterConfig) -> None:
        self._config = config
        self._cheap: ChatLLM | None = config.cheap_provider
        self._middle: ChatLLM | None = config.middle_provider
        self._primary: ChatLLM | None = config.primary_provider
        # Fallback chain: primary -> middle -> cheap
        self._fallback: ChatLLM = self._primary or self._middle or self._cheap  # type: ignore[assignment]  # validated below
        if self._fallback is None:
            msg = "SmartRouter requires at least one provider"
            raise ValueError(msg)
        self._metrics: deque[RouteMetrics] = deque(
            maxlen=config.metrics_capacity,
        )

    @property
    def model_name(self) -> str:
        return f"smart-router({self._fallback.model_name})"

    @property
    def capabilities(self) -> dict[str, Any]:
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

    # --- Feature extraction and routing ---

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
            token_score=score_tokens(messages),
            structured_score=score_structured(kwargs),
            tool_score=score_tools(kwargs),
            history_score=score_history(messages),
            intent_score=score_intent(messages),
            rule_tier=rule_tier,
        )

    def _route_and_resolve(
        self,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> tuple[RouteDecision, RouteFeatures, ChatLLM, bool]:
        """Compute route, resolve provider, detect fallback.

        Returns (decision, features, provider, is_fallback).
        """
        features = self._extract_features(messages, **kwargs)
        decision = compute_route(features)
        tier = decision.tier

        tier_provider = self._get_tier_provider(tier)
        is_fallback = tier_provider is None
        if is_fallback:
            _log.warning(
                "smart_router.fallback",
                requested_tier=tier,
                fallback_provider=self._fallback.model_name,
                reason=f"no provider configured for tier '{tier}'",
            )

        provider: ChatLLM = tier_provider if tier_provider is not None else self._fallback
        return decision, features, provider, is_fallback

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

    # --- Provider resolution ---

    def _get_tier_provider(self, tier: str) -> ChatLLM | None:
        """Get the exact provider for a tier, or None if missing."""
        if tier == "cheap":
            return self._cheap
        if tier == "middle":
            return self._middle
        if tier == "primary":
            return self._primary
        return None

    def _get_provider(self, tier: str) -> ChatLLM:
        """Get the provider for a tier, with fallback."""
        provider = self._get_tier_provider(tier)
        return provider if provider is not None else self._fallback

    # --- Telemetry ---

    def _record_metrics(
        self,
        decision: RouteDecision,
        features: RouteFeatures,
        provider_name: str,
        latency_ms: float,
        token_estimate: int,
        *,
        is_fallback: bool = False,
    ) -> RouteMetrics:
        """Create and store a RouteMetrics entry."""
        metrics = RouteMetrics(
            timestamp=time.monotonic(),
            tier=decision.tier,
            score=decision.score,
            provider_name=provider_name,
            latency_ms=latency_ms,
            token_estimate=token_estimate,
            features=features,
            score_breakdown=decision.score_breakdown,
            is_fallback=is_fallback,
            wall_time_iso=datetime.now(UTC).isoformat(),
        )
        self._metrics.append(metrics)
        return metrics

    def _log_route_decision(
        self,
        event: str,
        decision: RouteDecision,
        features: RouteFeatures,
        provider_name: str,
        *,
        is_fallback: bool = False,
    ) -> None:
        """Structured log of the routing decision with all feature scores."""
        breakdown = asdict(decision.score_breakdown) if decision.score_breakdown else None
        _log.info(
            event,
            tier=decision.tier,
            score=round(decision.score, 4),
            provider=provider_name,
            is_fallback=is_fallback,
            reason=decision.reason or None,
            features=asdict(features),
            score_breakdown=breakdown,
        )

    def _log_latency(
        self,
        event: str,
        provider_name: str,
        latency_ms: float,
    ) -> None:
        """Log provider call latency."""
        _log.info(
            event,
            provider=provider_name,
            latency_ms=round(latency_ms, 2),
        )

    def get_recent_metrics(self, n: int | None = None) -> list[RouteMetrics]:
        """Return the last *n* routing decisions (default: all in buffer).

        The ring buffer holds at most ``metrics_capacity`` entries
        (default 100). Oldest entries are evicted automatically.
        """
        items = list(self._metrics)
        if n is not None:
            return items[-n:]
        return items

    # --- ChatLLM protocol methods ---

    async def generate(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str:
        decision, features, provider, is_fallback = self._route_and_resolve(messages, **kwargs)
        provider_name: str = provider.model_name
        self._log_route_decision(
            "smart_router.route",
            decision,
            features,
            provider_name,
            is_fallback=is_fallback,
        )
        token_est = estimate_tokens(messages)

        with trace_llm_call(
            provider=provider_name,
            model=provider_name,
            tier=decision.tier,
        ) as span_data:
            t0 = time.monotonic()
            result = await provider.generate(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            latency_ms = (time.monotonic() - t0) * 1000
            span_data["latency_ms"] = latency_ms
            span_data["tokens_in"] = token_est

        self._log_latency("smart_router.generate_done", provider_name, latency_ms)
        self._record_metrics(
            decision,
            features,
            provider_name,
            latency_ms,
            token_est,
            is_fallback=is_fallback,
        )
        return result

    async def stream(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        decision, features, provider, is_fallback = self._route_and_resolve(messages, **kwargs)
        provider_name: str = provider.model_name
        self._log_route_decision(
            "smart_router.route_stream",
            decision,
            features,
            provider_name,
            is_fallback=is_fallback,
        )
        token_est = estimate_tokens(messages)

        # Note: trace_llm_call is a sync context manager so we cannot wrap
        # it around an async generator that yields across iterations.
        # Instead, record the trace attributes after iteration completes.
        t0 = time.monotonic()
        error_occurred: Exception | None = None
        try:
            async for chunk in provider.stream(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            ):
                yield chunk
        except Exception as exc:
            error_occurred = exc
            raise
        finally:
            latency_ms = (time.monotonic() - t0) * 1000
            # Record OTel span for streaming (post-hoc since we cannot hold
            # a sync context manager open across async yields).
            with trace_llm_call(
                provider=provider_name,
                model=provider_name,
                tier=decision.tier,
            ) as span_data:
                span_data["latency_ms"] = latency_ms
                span_data["tokens_in"] = token_est
                if error_occurred is not None:
                    span_data["error"] = str(error_occurred)

            self._log_latency("smart_router.stream_done", provider_name, latency_ms)
            self._record_metrics(
                decision,
                features,
                provider_name,
                latency_ms,
                token_est,
                is_fallback=is_fallback,
            )

    async def generate_with_search(
        self,
        query: str,
        *,
        max_results: int = 5,
        **kwargs: Any,
    ) -> WebSearchResult:
        """Route web search to the first provider that supports it."""
        for provider in [self._primary, self._middle, self._cheap]:
            if provider is not None and getattr(provider, "capabilities", {}).get("web_search", False):
                return await provider.generate_with_search(query, max_results=max_results, **kwargs)
        return WebSearchResult(
            text="Web search not available in any configured provider.",
            sources=[],
        )

    # --- Backward-compatible static scoring methods ---
    # These delegate to module-level functions in routing_types.py
    # but keep the SmartRouterAdapter._score_* API for existing callers.

    _score_tokens = staticmethod(score_tokens)
    _score_structured = staticmethod(score_structured)
    _score_tools = staticmethod(score_tools)
    _score_history = staticmethod(score_history)
    _score_intent = staticmethod(score_intent)
    _estimate_tokens = staticmethod(estimate_tokens)

    # --- Rule checking ---

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
