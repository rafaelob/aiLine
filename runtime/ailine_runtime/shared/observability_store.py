"""In-memory observability store for dashboard metrics.

Tracks SSE event counts, token usage, provider status,
circuit breaker state, and standards alignment evidence.
"""

from __future__ import annotations

import threading
import time
from typing import Any

# Cost estimates per 1K tokens (USD) -- rough approximations for demo
_COST_PER_1K_INPUT: dict[str, float] = {
    "claude-opus-4-6": 0.015,
    "claude-sonnet-4-5": 0.003,
    "claude-haiku-4-5": 0.0008,
    "gpt-5.2": 0.015,
    "gpt-4o": 0.005,
    "gpt-4o-mini": 0.00015,
    "gemini-3-pro-preview": 0.00125,
    "gemini-3-flash-preview": 0.000075,
    "gemini-2.5-pro": 0.00125,
    "gemini-2.5-flash": 0.000075,
    "default": 0.003,
}

_COST_PER_1K_OUTPUT: dict[str, float] = {
    "claude-opus-4-6": 0.075,
    "claude-sonnet-4-5": 0.015,
    "claude-haiku-4-5": 0.004,
    "gpt-5.2": 0.060,
    "gpt-4o": 0.015,
    "gpt-4o-mini": 0.0006,
    "gemini-3-pro-preview": 0.005,
    "gemini-3-flash-preview": 0.0003,
    "gemini-2.5-pro": 0.005,
    "gemini-2.5-flash": 0.0003,
    "default": 0.015,
}


class ObservabilityStore:
    """In-memory store for observability dashboard data.

    Thread-safe for concurrent access from middleware and API handlers.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sse_counts: dict[str, int] = {}
        self._token_usage: dict[str, int] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }
        self._provider_status: dict[str, Any] = {
            "name": "unknown",
            "model": "unknown",
            "status": "unknown",
            "last_success": None,
        }
        self._circuit_breaker_state: str = "closed"
        self._standards_evidence: dict[str, dict[str, Any]] = {}
        self._cost_model: str = "default"

    # --- SSE event tracking ---

    def record_sse_event(self, event_type: str) -> None:
        """Increment SSE event counter by type."""
        with self._lock:
            self._sse_counts[event_type] = self._sse_counts.get(event_type, 0) + 1

    def get_sse_event_counts(self) -> dict[str, int]:
        """Return SSE event counts by type."""
        with self._lock:
            return dict(self._sse_counts)

    # --- Token usage ---

    def record_tokens(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        model: str = "default",
    ) -> None:
        """Record token usage for cost estimation."""
        with self._lock:
            self._token_usage["input_tokens"] += input_tokens
            self._token_usage["output_tokens"] += output_tokens
            self._token_usage["total_tokens"] += input_tokens + output_tokens
            self._cost_model = model

    def get_token_stats(self) -> dict[str, Any]:
        """Return token usage and cost estimate."""
        with self._lock:
            inp = self._token_usage["input_tokens"]
            out = self._token_usage["output_tokens"]
            model = self._cost_model

            input_cost = (inp / 1000) * _COST_PER_1K_INPUT.get(
                model, _COST_PER_1K_INPUT["default"]
            )
            output_cost = (out / 1000) * _COST_PER_1K_OUTPUT.get(
                model, _COST_PER_1K_OUTPUT["default"]
            )

            return {
                "input_tokens": inp,
                "output_tokens": out,
                "total_tokens": inp + out,
                "estimated_cost_usd": round(input_cost + output_cost, 4),
                "cost_breakdown": {
                    "input_cost_usd": round(input_cost, 4),
                    "output_cost_usd": round(output_cost, 4),
                    "model": model,
                },
            }

    # --- Provider status ---

    def update_provider_status(
        self,
        name: str,
        model: str,
        status: str = "healthy",
    ) -> None:
        """Update current LLM provider status."""
        with self._lock:
            self._provider_status = {
                "name": name,
                "model": model,
                "status": status,
                "last_success": (
                    time.time()
                    if status == "healthy"
                    else self._provider_status.get("last_success")
                ),
            }

    def get_provider_status(self) -> dict[str, Any]:
        """Return current provider status."""
        with self._lock:
            return dict(self._provider_status)

    # --- Circuit breaker ---

    def update_circuit_breaker_state(self, state: str) -> None:
        """Update circuit breaker state (closed, open, half-open)."""
        with self._lock:
            self._circuit_breaker_state = state

    def get_circuit_breaker_state(self) -> str:
        """Return current circuit breaker state."""
        with self._lock:
            return self._circuit_breaker_state

    # --- Standards evidence ---

    def record_standards_evidence(
        self,
        run_id: str,
        standards: list[dict[str, Any]],
        bloom_level: str | None = None,
        alignment_explanation: str = "",
    ) -> None:
        """Record standards alignment evidence for a run."""
        with self._lock:
            self._standards_evidence[run_id] = {
                "standards": standards,
                "bloom_level": bloom_level,
                "alignment_explanation": alignment_explanation,
                "recorded_at": time.time(),
            }

    def get_standards_evidence(self, run_id: str) -> dict[str, Any]:
        """Return standards evidence for a run, or empty defaults."""
        with self._lock:
            return self._standards_evidence.get(
                run_id,
                {
                    "standards": [],
                    "bloom_level": None,
                    "alignment_explanation": "Standards evidence not yet captured for this run.",
                },
            )


# Module-level singleton
_store: ObservabilityStore | None = None
_store_lock = threading.Lock()


def get_observability_store() -> ObservabilityStore:
    """Get or create the singleton observability store."""
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = ObservabilityStore()
    return _store


def reset_observability_store() -> None:
    """Reset the singleton (for testing)."""
    global _store
    _store = None
