"""SmartRouter types and pure scoring functions.

Data types (RouteFeatures, ScoreBreakdown, RouteDecision, RouteMetrics,
RoutingRule, SmartRouterConfig) and the stateless compute_route() function
live here to keep smart_router.py focused on orchestration and telemetry.

Implements ADR-049: Weighted complexity scoring with rebalanced weights
(0.25/0.25/0.25/0.15/0.10).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...domain.ports.llm import ChatLLM

# Dimension weights (ADR-049 rebalanced)
W_TOKENS = 0.25
W_STRUCTURED = 0.25
W_TOOLS = 0.25
W_HISTORY = 0.15
W_INTENT = 0.10

# Tier thresholds
TIER_CHEAP_MAX = 0.40
TIER_MIDDLE_MAX = 0.70

# Default ring buffer capacity for metrics history
DEFAULT_METRICS_CAPACITY = 100


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
class ScoreBreakdown:
    """Per-dimension weighted contributions to the composite score."""

    token: float
    structured: float
    tool: float
    history: float
    intent: float


@dataclass(frozen=True)
class RouteDecision:
    """Output of the routing decision: tier name, score, and breakdown."""

    tier: str  # "cheap", "middle", or "primary"
    score: float
    reason: str = ""
    score_breakdown: ScoreBreakdown | None = None


@dataclass(frozen=True)
class RouteMetrics:
    """Telemetry record for a single routing decision.

    Captured for every generate/stream call to enable operational
    visibility into routing behavior and provider performance.
    """

    timestamp: float  # time.monotonic() for duration calculations
    tier: str
    score: float
    provider_name: str
    latency_ms: float  # wall-clock ms for the provider call
    token_estimate: int  # rough char-based token estimate
    features: RouteFeatures
    score_breakdown: ScoreBreakdown | None = None
    is_fallback: bool = False  # True if a non-preferred provider was used
    wall_time_iso: str = ""  # ISO 8601 wall-clock time for display/audit


@dataclass(frozen=True)
class RoutingRule:
    """Hard override rule evaluated before scoring."""

    pattern: str  # regex applied to the last user message
    tier: str  # "cheap", "middle", or "primary"
    reason: str = ""


@dataclass
class SmartRouterConfig:
    """Configuration for the SmartRouter."""

    cheap_provider: ChatLLM | None = None
    middle_provider: ChatLLM | None = None
    primary_provider: ChatLLM | None = None
    mode: str = "weighted"  # "weighted" or "rules"
    rules: list[RoutingRule] = field(default_factory=list)
    metrics_capacity: int = DEFAULT_METRICS_CAPACITY


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

    breakdown = ScoreBreakdown(
        token=W_TOKENS * features.token_score,
        structured=W_STRUCTURED * features.structured_score,
        tool=W_TOOLS * features.tool_score,
        history=W_HISTORY * features.history_score,
        intent=W_INTENT * features.intent_score,
    )

    score = (
        breakdown.token
        + breakdown.structured
        + breakdown.tool
        + breakdown.history
        + breakdown.intent
    )
    score = min(1.0, max(0.0, score))

    if score <= TIER_CHEAP_MAX:
        tier = "cheap"
    elif score <= TIER_MIDDLE_MAX:
        tier = "middle"
    else:
        tier = "primary"

    return RouteDecision(tier=tier, score=score, score_breakdown=breakdown)


# --- Scoring functions (stateless, used by SmartRouterAdapter) ---

# Complexity signal patterns for intent scoring
_COMPLEXITY_SIGNALS = [
    # Cognitive verbs (PT + EN)
    re.compile(r"(?:analis|compar|avali|sintetiz|critic|analyze|compare|evaluate|synthesize|critique)", re.IGNORECASE),
    # Depth signals (PT + EN)
    re.compile(r"(?:multi|complex|detalhad|aprofundad|detailed|in-depth)", re.IGNORECASE),
    # Curriculum alignment (PT + EN)
    re.compile(
        r"(?:curricul|BNCC|standard|alignment|assessment|rubric"
        r"|formative|summative|scaffold|UDL|IEP|curriculum|standards)",
        re.IGNORECASE,
    ),
    # Accessibility / inclusion (PT + EN)
    re.compile(
        r"(?:acessibilid|inclusiv|adapt|TEA|TDAH|accessibility|inclusive"
        r"|autism|ADHD|dyslexia|hearing|impairment|differentiated|accommodation)",
        re.IGNORECASE,
    ),
]


def score_tokens(messages: list[dict[str, Any]]) -> float:
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


def score_structured(kwargs: dict[str, Any]) -> float:
    """Score based on whether structured output is requested."""
    if "response_format" in kwargs or "structured_output" in kwargs:
        return 1.0
    if kwargs.get("json_mode"):
        return 0.6
    return 0.0


def score_tools(kwargs: dict[str, Any]) -> float:
    """Score based on tool/function calling requirements."""
    tools = kwargs.get("tools") or []
    if len(tools) > 5:
        return 1.0
    if len(tools) > 0:
        return 0.6
    return 0.0


def score_history(messages: list[dict[str, Any]]) -> float:
    """Score based on conversation history length."""
    turns = len(messages)
    if turns > 20:
        return 1.0
    if turns > 10:
        return 0.6
    if turns > 4:
        return 0.3
    return 0.0


def score_intent(messages: list[dict[str, Any]]) -> float:
    """Score based on detected complexity signals in the prompt."""
    if not messages:
        return 0.0
    last_content = str(messages[-1].get("content", ""))
    matches = sum(1 for pat in _COMPLEXITY_SIGNALS if pat.search(last_content))
    if matches >= 3:
        return 1.0
    if matches >= 2:
        return 0.6
    if matches >= 1:
        return 0.3
    return 0.0


def estimate_tokens(messages: list[dict[str, Any]]) -> int:
    """Estimate token count using tiktoken BPE tokenization.

    Uses cl100k_base encoding (GPT-4/Claude family) for accurate counts.
    """
    from ...app.token_counter import count_tokens

    total_text = " ".join(str(m.get("content", "")) for m in messages)
    return max(1, count_tokens(total_text))
