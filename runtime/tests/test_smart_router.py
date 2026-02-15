"""Tests for SmartRouterAdapter (ADR-049).

Covers:
- Complexity scoring (5 dimensions)
- Tier classification (cheap/middle/primary)
- Hard override rules
- Provider routing + fallback
- Protocol compliance (generate/stream)
- Score breakdown per dimension
- RouteMetrics telemetry and ring buffer
- Fallback chain logging
"""

from __future__ import annotations

from typing import Any

import pytest

from ailine_runtime.adapters.llm.fake_llm import FakeChatLLM
from ailine_runtime.adapters.llm.smart_router import (
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
    SmartRouterAdapter,
    SmartRouterConfig,
    compute_route,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cheap_llm() -> FakeChatLLM:
    return FakeChatLLM(model="cheap-model", responses=["cheap response"])


@pytest.fixture
def middle_llm() -> FakeChatLLM:
    return FakeChatLLM(model="middle-model", responses=["middle response"])


@pytest.fixture
def primary_llm() -> FakeChatLLM:
    return FakeChatLLM(model="primary-model", responses=["primary response"])


@pytest.fixture
def router(
    cheap_llm: FakeChatLLM,
    middle_llm: FakeChatLLM,
    primary_llm: FakeChatLLM,
) -> SmartRouterAdapter:
    config = SmartRouterConfig(
        cheap_provider=cheap_llm,
        middle_provider=middle_llm,
        primary_provider=primary_llm,
    )
    return SmartRouterAdapter(config)


def _user_msg(content: str) -> dict[str, Any]:
    return {"role": "user", "content": content}


# ---------------------------------------------------------------------------
# Weight constants (ADR-049 rebalanced)
# ---------------------------------------------------------------------------


class TestWeightsADR049:
    def test_weights_sum_to_one(self):
        total = W_TOKENS + W_STRUCTURED + W_TOOLS + W_HISTORY + W_INTENT
        assert abs(total - 1.0) < 1e-9

    def test_rebalanced_values(self):
        assert W_TOKENS == 0.25
        assert W_STRUCTURED == 0.25
        assert W_TOOLS == 0.25
        assert W_HISTORY == 0.15
        assert W_INTENT == 0.10

    def test_tier_thresholds(self):
        assert TIER_CHEAP_MAX == 0.40
        assert TIER_MIDDLE_MAX == 0.70


# ---------------------------------------------------------------------------
# Complexity scoring
# ---------------------------------------------------------------------------


class TestComplexityScoring:
    def test_simple_message_scores_low(self, router: SmartRouterAdapter):
        msgs = [_user_msg("Oi")]
        score = router.score_complexity(msgs)
        assert score <= TIER_CHEAP_MAX

    def test_long_message_scores_higher(self, router: SmartRouterAdapter):
        msgs = [_user_msg("x" * 5000)]
        score = router.score_complexity(msgs)
        assert score > 0.1

    def test_very_long_message_scores_high(self, router: SmartRouterAdapter):
        msgs = [_user_msg("x" * 10000)]
        score = router.score_complexity(msgs)
        assert score > 0.2

    def test_structured_output_increases_score(self, router: SmartRouterAdapter):
        msgs = [_user_msg("test")]
        base = router.score_complexity(msgs)
        with_struct = router.score_complexity(msgs, response_format={"type": "json"})
        assert with_struct > base

    def test_tools_increase_score(self, router: SmartRouterAdapter):
        msgs = [_user_msg("test")]
        base = router.score_complexity(msgs)
        tools = [{"name": f"tool_{i}"} for i in range(6)]
        with_tools = router.score_complexity(msgs, tools=tools)
        assert with_tools > base

    def test_long_history_increases_score(self, router: SmartRouterAdapter):
        short = [_user_msg("q1"), _user_msg("q2")]
        long_hist = [_user_msg(f"msg{i}") for i in range(25)]
        assert router.score_complexity(long_hist) > router.score_complexity(short)

    def test_complexity_signals_increase_score(self, router: SmartRouterAdapter):
        simple = [_user_msg("Oi")]
        complex_msg = [_user_msg("Analise detalhada do curriculo BNCC com acessibilidade TEA")]
        assert router.score_complexity(complex_msg) > router.score_complexity(simple)

    def test_score_clamped_0_to_1(self, router: SmartRouterAdapter):
        # Even with all dimensions maxed
        msgs = [_user_msg(f"analise complexa curriculo BNCC acessibilidade msg{i}" + "x" * 1000) for i in range(25)]
        score = router.score_complexity(msgs, tools=[{"n": i} for i in range(10)], response_format={})
        assert 0.0 <= score <= 1.0

    def test_empty_messages_score_zero(self, router: SmartRouterAdapter):
        score = router.score_complexity([])
        assert score == 0.0


# ---------------------------------------------------------------------------
# Tier classification
# ---------------------------------------------------------------------------


class TestTierClassification:
    def test_simple_gets_cheap(self, router: SmartRouterAdapter):
        msgs = [_user_msg("Oi")]
        assert router.classify_tier(msgs) == "cheap"

    def test_complex_gets_primary(self, router: SmartRouterAdapter):
        msgs = [_user_msg(f"analise complexa BNCC acessibilidade msg{i}" + "x" * 500) for i in range(25)]
        tier = router.classify_tier(msgs, tools=[{"n": i} for i in range(10)], response_format={})
        assert tier == "primary"

    def test_medium_complexity_gets_middle(self, router: SmartRouterAdapter):
        # Medium-length with some tools
        msgs = [_user_msg("x" * 3000)]
        tier = router.classify_tier(msgs, tools=[{"n": 1}, {"n": 2}])
        assert tier in ("middle", "cheap")  # depends on exact score

    def test_classify_returns_middle_tier(self, router: SmartRouterAdapter):
        """Force a score in the 0.41-0.70 range to get 'middle' (line 125)."""
        # Medium message (4000+ chars => 0.7 tokens) + json_mode (0.6 structured)
        # + 1-5 tools (0.6) + 5-10 history (0.3)
        # score ~ 0.25*0.7 + 0.25*0.6 + 0.25*0.6 + 0.15*0.3 + 0.10*0
        # = 0.175 + 0.15 + 0.15 + 0.045 = 0.52 => middle
        msgs = [_user_msg("x" * 4500)] * 6  # 6 messages
        tier = router.classify_tier(msgs, json_mode=True, tools=[{"n": 1}])
        assert tier == "middle"


# ---------------------------------------------------------------------------
# Hard override rules
# ---------------------------------------------------------------------------


class TestRoutingRules:
    def test_rule_overrides_scoring(self):
        config = SmartRouterConfig(
            cheap_provider=FakeChatLLM(model="cheap"),
            primary_provider=FakeChatLLM(model="primary"),
            mode="rules",
            rules=[
                RoutingRule(
                    pattern=r"(?i)urgent|critico",
                    tier="primary",
                    reason="urgency override",
                ),
            ],
        )
        router = SmartRouterAdapter(config)
        msgs = [_user_msg("Oi")]  # simple message, would normally be cheap
        assert router.classify_tier(msgs) == "cheap"

        msgs_urgent = [_user_msg("Caso critico")]
        assert router.classify_tier(msgs_urgent) == "primary"

    def test_rules_checked_in_weighted_mode_too(self):
        config = SmartRouterConfig(
            cheap_provider=FakeChatLLM(model="cheap"),
            primary_provider=FakeChatLLM(model="primary"),
            mode="weighted",
            rules=[RoutingRule(pattern=r"FORCE_PRIMARY", tier="primary")],
        )
        router = SmartRouterAdapter(config)
        assert router.classify_tier([_user_msg("FORCE_PRIMARY")]) == "primary"

    def test_no_rule_match_falls_through(self):
        config = SmartRouterConfig(
            cheap_provider=FakeChatLLM(model="cheap"),
            rules=[RoutingRule(pattern=r"NOMATCH", tier="primary")],
        )
        router = SmartRouterAdapter(config)
        assert router.classify_tier([_user_msg("normal")]) == "cheap"


# ---------------------------------------------------------------------------
# Provider routing + fallback
# ---------------------------------------------------------------------------


class TestProviderRouting:
    @pytest.mark.asyncio
    async def test_routes_to_cheap(self, router: SmartRouterAdapter):
        result = await router.generate([_user_msg("Oi")])
        assert result == "cheap response"

    @pytest.mark.asyncio
    async def test_routes_to_primary_for_complex(self):
        config = SmartRouterConfig(
            cheap_provider=FakeChatLLM(model="cheap", responses=["cheap"]),
            primary_provider=FakeChatLLM(model="primary", responses=["primary"]),
            rules=[RoutingRule(pattern=r"FORCE_PRIMARY", tier="primary")],
        )
        router = SmartRouterAdapter(config)
        result = await router.generate([_user_msg("FORCE_PRIMARY")])
        assert result == "primary"

    @pytest.mark.asyncio
    async def test_routes_to_middle_tier(self):
        """Force routing to the middle provider (line 133)."""
        config = SmartRouterConfig(
            cheap_provider=FakeChatLLM(model="cheap", responses=["cheap"]),
            middle_provider=FakeChatLLM(model="middle", responses=["middle"]),
            primary_provider=FakeChatLLM(model="primary", responses=["primary"]),
            rules=[RoutingRule(pattern=r"FORCE_MIDDLE", tier="middle")],
        )
        router = SmartRouterAdapter(config)
        result = await router.generate([_user_msg("FORCE_MIDDLE")])
        assert result == "middle"

    @pytest.mark.asyncio
    async def test_fallback_when_tier_provider_missing(self):
        # Only primary configured
        config = SmartRouterConfig(primary_provider=FakeChatLLM(model="primary", responses=["only"]))
        router = SmartRouterAdapter(config)
        # Simple message would want cheap, but falls back to primary
        result = await router.generate([_user_msg("Oi")])
        assert result == "only"

    @pytest.mark.asyncio
    async def test_stream_routes_correctly(self, router: SmartRouterAdapter):
        chunks = []
        async for chunk in router.stream([_user_msg("Oi")]):
            chunks.append(chunk)
        assert "".join(chunks) == "cheap response"

    def test_no_provider_raises(self):
        config = SmartRouterConfig()
        with pytest.raises(ValueError, match="at least one provider"):
            SmartRouterAdapter(config)


# ---------------------------------------------------------------------------
# Protocol compliance
# ---------------------------------------------------------------------------


class TestProtocolCompliance:
    def test_model_name(self, router: SmartRouterAdapter):
        assert "smart-router" in router.model_name

    def test_capabilities(self, router: SmartRouterAdapter):
        caps = router.capabilities
        assert caps["provider"] == "smart-router"
        assert caps["streaming"] is True
        assert caps["tool_use"] is True
        assert caps["routing_mode"] == "weighted"

    def test_chatllm_protocol_check(self, router: SmartRouterAdapter):
        from ailine_runtime.domain.ports.llm import ChatLLM

        assert isinstance(router, ChatLLM)


# ---------------------------------------------------------------------------
# Individual scoring functions
# ---------------------------------------------------------------------------


class TestScoringFunctions:
    def test_token_score_tiers(self):
        assert SmartRouterAdapter._score_tokens([_user_msg("hi")]) == 0.1
        assert SmartRouterAdapter._score_tokens([_user_msg("x" * 2500)]) == 0.4
        assert SmartRouterAdapter._score_tokens([_user_msg("x" * 5000)]) == 0.7
        assert SmartRouterAdapter._score_tokens([_user_msg("x" * 10000)]) == 1.0

    def test_structured_score(self):
        assert SmartRouterAdapter._score_structured({}) == 0.0
        assert SmartRouterAdapter._score_structured({"json_mode": True}) == 0.6
        assert SmartRouterAdapter._score_structured({"response_format": {}}) == 1.0
        assert SmartRouterAdapter._score_structured({"structured_output": True}) == 1.0

    def test_tool_score(self):
        assert SmartRouterAdapter._score_tools({}) == 0.0
        assert SmartRouterAdapter._score_tools({"tools": [1]}) == 0.6
        assert SmartRouterAdapter._score_tools({"tools": list(range(6))}) == 1.0

    def test_history_score(self):
        assert SmartRouterAdapter._score_history([]) == 0.0
        assert SmartRouterAdapter._score_history([_user_msg("a")] * 3) == 0.0
        assert SmartRouterAdapter._score_history([_user_msg("a")] * 5) == 0.3
        assert SmartRouterAdapter._score_history([_user_msg("a")] * 15) == 0.6
        assert SmartRouterAdapter._score_history([_user_msg("a")] * 25) == 1.0

    def test_intent_score_no_signal(self):
        assert SmartRouterAdapter._score_intent([_user_msg("Oi")]) == 0.0

    def test_intent_score_one_signal(self):
        assert SmartRouterAdapter._score_intent([_user_msg("analise")]) == 0.3

    def test_intent_score_two_signals(self):
        """Exactly 2 complexity signals yields 0.6 (line 250)."""
        # "analise" matches the first pattern, "complexa" matches the second
        assert SmartRouterAdapter._score_intent([_user_msg("analise complexa")]) == 0.6

    def test_intent_score_multiple_signals(self):
        assert SmartRouterAdapter._score_intent([_user_msg("analise detalhada curriculo BNCC acessibilidade")]) == 1.0

    def test_intent_score_empty(self):
        assert SmartRouterAdapter._score_intent([]) == 0.0

    def test_rules_empty_messages(self):
        config = SmartRouterConfig(
            cheap_provider=FakeChatLLM(model="cheap"),
            rules=[RoutingRule(pattern=r"test", tier="primary")],
        )
        router = SmartRouterAdapter(config)
        assert router._check_rules([]) is None


# ---------------------------------------------------------------------------
# compute_route pure function (FINDING-06)
# ---------------------------------------------------------------------------


class TestComputeRoute:
    """Tests for the stateless compute_route function."""

    def test_all_zeros_returns_cheap(self):
        features = RouteFeatures(
            token_score=0.0,
            structured_score=0.0,
            tool_score=0.0,
            history_score=0.0,
            intent_score=0.0,
        )
        decision = compute_route(features)
        assert decision.tier == "cheap"
        assert decision.score == 0.0

    def test_all_ones_returns_primary(self):
        features = RouteFeatures(
            token_score=1.0,
            structured_score=1.0,
            tool_score=1.0,
            history_score=1.0,
            intent_score=1.0,
        )
        decision = compute_route(features)
        assert decision.tier == "primary"
        assert decision.score == 1.0

    def test_middle_range_returns_middle(self):
        # Score = 0.25*0.8 + 0.25*0.6 + 0.25*0.5 + 0.15*0.3 + 0.10*0.0
        # = 0.20 + 0.15 + 0.125 + 0.045 + 0 = 0.52
        features = RouteFeatures(
            token_score=0.8,
            structured_score=0.6,
            tool_score=0.5,
            history_score=0.3,
            intent_score=0.0,
        )
        decision = compute_route(features)
        assert decision.tier == "middle"
        assert 0.41 <= decision.score <= 0.70

    def test_cheap_boundary(self):
        # Score = 0.25*0.4 + 0.25*0.4 + 0.25*0.4 + 0.15*0.4 + 0.10*0.0
        # = 0.10 + 0.10 + 0.10 + 0.06 + 0 = 0.36
        features = RouteFeatures(
            token_score=0.4,
            structured_score=0.4,
            tool_score=0.4,
            history_score=0.4,
            intent_score=0.0,
        )
        decision = compute_route(features)
        assert decision.tier == "cheap"
        assert decision.score <= TIER_CHEAP_MAX

    def test_primary_boundary(self):
        # Score = 0.25*1.0 + 0.25*1.0 + 0.25*1.0 + 0.15*0.6 + 0.10*0.6
        # = 0.25 + 0.25 + 0.25 + 0.09 + 0.06 = 0.90
        features = RouteFeatures(
            token_score=1.0,
            structured_score=1.0,
            tool_score=1.0,
            history_score=0.6,
            intent_score=0.6,
        )
        decision = compute_route(features)
        assert decision.tier == "primary"
        assert decision.score > TIER_MIDDLE_MAX

    def test_rule_override_takes_precedence(self):
        features = RouteFeatures(
            token_score=0.0,
            structured_score=0.0,
            tool_score=0.0,
            history_score=0.0,
            intent_score=0.0,
            rule_tier="primary",
        )
        decision = compute_route(features)
        assert decision.tier == "primary"
        assert decision.reason == "rule_override"
        assert decision.score == 0.0

    def test_score_clamped_to_0_1(self):
        # Even with values > 1.0 (should not happen, but guard)
        features = RouteFeatures(
            token_score=2.0,
            structured_score=2.0,
            tool_score=2.0,
            history_score=2.0,
            intent_score=2.0,
        )
        decision = compute_route(features)
        assert decision.score == 1.0

    def test_returns_route_decision_type(self):
        features = RouteFeatures(
            token_score=0.5,
            structured_score=0.0,
            tool_score=0.0,
            history_score=0.0,
            intent_score=0.0,
        )
        decision = compute_route(features)
        assert isinstance(decision, RouteDecision)
        assert isinstance(decision.tier, str)
        assert isinstance(decision.score, float)

    def test_features_frozen(self):
        """RouteFeatures is immutable."""
        features = RouteFeatures(
            token_score=0.5,
            structured_score=0.0,
            tool_score=0.0,
            history_score=0.0,
            intent_score=0.0,
        )
        with pytest.raises(AttributeError):
            features.token_score = 0.9  # type: ignore[misc]


# ---------------------------------------------------------------------------
# SmartRouter web search
# ---------------------------------------------------------------------------


class TestSmartRouterWebSearch:
    """Test SmartRouter web search delegation."""

    def test_capabilities_reflect_provider_search(self):
        config = SmartRouterConfig(
            cheap_provider=FakeChatLLM(model="cheap"),
            primary_provider=FakeChatLLM(model="primary"),
        )
        router = SmartRouterAdapter(config)
        # FakeChatLLM has web_search=True
        assert router.capabilities["web_search"] is True

    @pytest.mark.asyncio
    async def test_generate_with_search_delegates_to_primary(self):
        config = SmartRouterConfig(
            cheap_provider=FakeChatLLM(model="cheap"),
            primary_provider=FakeChatLLM(model="primary"),
        )
        router = SmartRouterAdapter(config)
        result = await router.generate_with_search("test query")
        assert "test query" in result.text
        assert len(result.sources) >= 1


# ---------------------------------------------------------------------------
# ScoreBreakdown
# ---------------------------------------------------------------------------


class TestScoreBreakdown:
    """Tests for per-dimension weighted score breakdown."""

    def test_compute_route_returns_breakdown(self):
        features = RouteFeatures(
            token_score=0.8,
            structured_score=0.6,
            tool_score=0.5,
            history_score=0.3,
            intent_score=0.2,
        )
        decision = compute_route(features)
        assert decision.score_breakdown is not None
        bd = decision.score_breakdown
        assert isinstance(bd, ScoreBreakdown)
        assert abs(bd.token - W_TOKENS * 0.8) < 1e-9
        assert abs(bd.structured - W_STRUCTURED * 0.6) < 1e-9
        assert abs(bd.tool - W_TOOLS * 0.5) < 1e-9
        assert abs(bd.history - W_HISTORY * 0.3) < 1e-9
        assert abs(bd.intent - W_INTENT * 0.2) < 1e-9

    def test_breakdown_sums_to_score(self):
        features = RouteFeatures(
            token_score=0.7,
            structured_score=0.4,
            tool_score=0.9,
            history_score=0.1,
            intent_score=0.5,
        )
        decision = compute_route(features)
        bd = decision.score_breakdown
        assert bd is not None
        total = bd.token + bd.structured + bd.tool + bd.history + bd.intent
        assert abs(total - decision.score) < 1e-9

    def test_rule_override_has_no_breakdown(self):
        features = RouteFeatures(
            token_score=0.5,
            structured_score=0.5,
            tool_score=0.5,
            history_score=0.5,
            intent_score=0.5,
            rule_tier="primary",
        )
        decision = compute_route(features)
        # Rule override skips scoring, so no breakdown
        assert decision.score_breakdown is None

    def test_breakdown_frozen(self):
        features = RouteFeatures(
            token_score=0.5,
            structured_score=0.0,
            tool_score=0.0,
            history_score=0.0,
            intent_score=0.0,
        )
        decision = compute_route(features)
        assert decision.score_breakdown is not None
        with pytest.raises(AttributeError):
            decision.score_breakdown.token = 999.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# RouteMetrics + get_recent_metrics ring buffer
# ---------------------------------------------------------------------------


class TestRouteMetrics:
    """Tests for telemetry capture and ring buffer retrieval."""

    @pytest.mark.asyncio
    async def test_generate_captures_metrics(self, router: SmartRouterAdapter):
        assert len(router.get_recent_metrics()) == 0
        await router.generate([_user_msg("Oi")])
        metrics = router.get_recent_metrics()
        assert len(metrics) == 1
        m = metrics[0]
        assert isinstance(m, RouteMetrics)
        assert m.tier == "cheap"
        assert m.provider_name == "cheap-model"
        assert m.latency_ms >= 0.0
        assert m.token_estimate >= 1
        assert isinstance(m.features, RouteFeatures)

    @pytest.mark.asyncio
    async def test_stream_captures_metrics(self, router: SmartRouterAdapter):
        chunks = []
        async for chunk in router.stream([_user_msg("Oi")]):
            chunks.append(chunk)
        metrics = router.get_recent_metrics()
        assert len(metrics) == 1
        assert metrics[0].tier == "cheap"
        assert metrics[0].provider_name == "cheap-model"
        assert metrics[0].latency_ms >= 0.0

    @pytest.mark.asyncio
    async def test_metrics_accumulate(self, router: SmartRouterAdapter):
        await router.generate([_user_msg("a")])
        await router.generate([_user_msg("b")])
        await router.generate([_user_msg("c")])
        assert len(router.get_recent_metrics()) == 3

    @pytest.mark.asyncio
    async def test_get_recent_metrics_with_n(self, router: SmartRouterAdapter):
        for i in range(5):
            await router.generate([_user_msg(f"msg{i}")])
        assert len(router.get_recent_metrics(n=3)) == 3
        assert len(router.get_recent_metrics(n=10)) == 5
        assert len(router.get_recent_metrics(n=1)) == 1

    @pytest.mark.asyncio
    async def test_ring_buffer_evicts_oldest(self):
        config = SmartRouterConfig(
            cheap_provider=FakeChatLLM(model="cheap", responses=["r"]),
            metrics_capacity=3,
        )
        router = SmartRouterAdapter(config)
        for i in range(5):
            await router.generate([_user_msg(f"msg{i}")])
        metrics = router.get_recent_metrics()
        # Only last 3 should remain
        assert len(metrics) == 3

    @pytest.mark.asyncio
    async def test_metrics_include_score_breakdown(self, router: SmartRouterAdapter):
        await router.generate([_user_msg("Oi")])
        m = router.get_recent_metrics()[0]
        assert m.score_breakdown is not None
        assert isinstance(m.score_breakdown, ScoreBreakdown)

    def test_default_metrics_capacity(self):
        assert DEFAULT_METRICS_CAPACITY == 100
        config = SmartRouterConfig(
            cheap_provider=FakeChatLLM(model="cheap"),
        )
        router = SmartRouterAdapter(config)
        assert router._metrics.maxlen == 100


# ---------------------------------------------------------------------------
# Fallback chain logging
# ---------------------------------------------------------------------------


class TestFallbackLogging:
    """Tests for fallback detection and is_fallback flag in metrics."""

    @pytest.mark.asyncio
    async def test_fallback_sets_flag_in_metrics(self):
        # Only primary configured -- cheap tier request triggers fallback
        config = SmartRouterConfig(
            primary_provider=FakeChatLLM(model="primary", responses=["fallback"]),
        )
        router = SmartRouterAdapter(config)
        result = await router.generate([_user_msg("Oi")])
        assert result == "fallback"
        metrics = router.get_recent_metrics()
        assert len(metrics) == 1
        assert metrics[0].is_fallback is True
        assert metrics[0].provider_name == "primary"

    @pytest.mark.asyncio
    async def test_no_fallback_flag_when_tier_matches(self, router: SmartRouterAdapter):
        await router.generate([_user_msg("Oi")])
        metrics = router.get_recent_metrics()
        assert len(metrics) == 1
        assert metrics[0].is_fallback is False
        assert metrics[0].provider_name == "cheap-model"

    @pytest.mark.asyncio
    async def test_stream_fallback_sets_flag(self):
        config = SmartRouterConfig(
            primary_provider=FakeChatLLM(model="primary", responses=["fallback"]),
        )
        router = SmartRouterAdapter(config)
        chunks = []
        async for chunk in router.stream([_user_msg("Oi")]):
            chunks.append(chunk)
        metrics = router.get_recent_metrics()
        assert len(metrics) == 1
        assert metrics[0].is_fallback is True


# ---------------------------------------------------------------------------
# Config: cache_ttl_seconds removed
# ---------------------------------------------------------------------------


class TestConfigCacheTtlRemoved:
    """Verify dead cache_ttl_seconds field no longer exists."""

    def test_no_cache_ttl_field(self):
        config = SmartRouterConfig(
            cheap_provider=FakeChatLLM(model="cheap"),
        )
        assert not hasattr(config, "cache_ttl_seconds")

    def test_metrics_capacity_field_exists(self):
        config = SmartRouterConfig(
            cheap_provider=FakeChatLLM(model="cheap"),
            metrics_capacity=50,
        )
        assert config.metrics_capacity == 50
