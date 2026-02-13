"""Lightweight in-process metrics counters.

Exposes Prometheus-compatible text format at /metrics endpoint.
Pre-MVP: in-memory counters. Production: use prometheus_client library.

Thread-safety: uses threading.Lock for atomic increments. Suitable for
single-process ASGI servers (uvicorn). For multi-process deployments,
replace with a shared-memory or Redis-backed backend.
"""

from __future__ import annotations

import threading
from typing import Any


class Counter:
    """Increment-only counter with label support.

    Usage::

        reqs = Counter("http_requests_total", "Total HTTP requests")
        reqs.inc(method="GET", path="/health", status="200")
    """

    def __init__(self, name: str, help_text: str = "") -> None:
        self.name = name
        self.help_text = help_text
        self._values: dict[tuple[tuple[str, str], ...], float] = {}
        self._lock = threading.Lock()

    def inc(self, value: float = 1.0, **labels: str) -> None:
        """Increment the counter by *value* for the given label set."""
        key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) + value

    def get(self, **labels: str) -> float:
        """Return the current value for the given label set."""
        key = tuple(sorted(labels.items()))
        with self._lock:
            return self._values.get(key, 0.0)

    def collect(self) -> list[tuple[dict[str, str], float]]:
        """Return all label-set / value pairs for exposition."""
        with self._lock:
            return [(dict(k), v) for k, v in self._values.items()]


class Histogram:
    """Track value distributions with configurable buckets.

    Usage::

        dur = Histogram("request_duration_seconds", "Request duration",
                        buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0])
        dur.observe(0.042, method="GET", path="/health")
    """

    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

    def __init__(
        self,
        name: str,
        help_text: str = "",
        buckets: tuple[float, ...] | list[float] | None = None,
    ) -> None:
        self.name = name
        self.help_text = help_text
        self.buckets = tuple(sorted(buckets or self.DEFAULT_BUCKETS))
        # Per label-set: {bucket_le -> count}, _sum, _count
        self._data: dict[tuple[tuple[str, str], ...], dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _ensure_entry(
        self, key: tuple[tuple[str, str], ...]
    ) -> dict[str, Any]:
        if key not in self._data:
            self._data[key] = {
                "buckets": {b: 0 for b in self.buckets},
                "_sum": 0.0,
                "_count": 0,
            }
        return self._data[key]

    def observe(self, value: float, **labels: str) -> None:
        """Record an observed value into the histogram buckets."""
        key = tuple(sorted(labels.items()))
        with self._lock:
            entry = self._ensure_entry(key)
            entry["_sum"] += value
            entry["_count"] += 1
            for b in self.buckets:
                if value <= b:
                    entry["buckets"][b] += 1

    def collect(
        self,
    ) -> list[tuple[dict[str, str], dict[str, Any]]]:
        """Return all label-set / histogram data pairs."""
        with self._lock:
            return [(dict(k), dict(v)) for k, v in self._data.items()]


# ---------------------------------------------------------------------------
# Pre-defined metrics (global singletons)
# ---------------------------------------------------------------------------

http_requests_total = Counter(
    "ailine_http_requests_total",
    "Total HTTP requests by method, path, and status.",
)

http_request_duration = Histogram(
    "ailine_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

llm_calls_total = Counter(
    "ailine_llm_calls_total",
    "Total LLM API calls by provider, tier, and status.",
)

llm_call_duration = Histogram(
    "ailine_llm_call_duration_seconds",
    "LLM call duration in seconds.",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

circuit_breaker_state = Counter(
    "ailine_circuit_breaker_state",
    "Circuit breaker state transitions.",
)


# ---------------------------------------------------------------------------
# Prometheus text format exposition
# ---------------------------------------------------------------------------


def _format_labels(labels: dict[str, str]) -> str:
    """Format label dict as Prometheus label string."""
    if not labels:
        return ""
    parts = [f'{k}="{v}"' for k, v in sorted(labels.items())]
    return "{" + ",".join(parts) + "}"


def render_metrics() -> str:
    """Render all registered metrics in Prometheus text exposition format.

    Returns a plain-text string suitable for ``GET /metrics``.
    """
    lines: list[str] = []

    for counter in (http_requests_total, llm_calls_total, circuit_breaker_state):
        lines.append(f"# HELP {counter.name} {counter.help_text}")
        lines.append(f"# TYPE {counter.name} counter")
        for labels, value in counter.collect():
            lbl = _format_labels(labels)
            # Prometheus counter values must be integer or float.
            lines.append(f"{counter.name}{lbl} {value}")
        lines.append("")

    for histogram in (http_request_duration, llm_call_duration):
        lines.append(f"# HELP {histogram.name} {histogram.help_text}")
        lines.append(f"# TYPE {histogram.name} histogram")
        for labels, data in histogram.collect():
            for bucket_le, count in sorted(data["buckets"].items()):
                lbl = dict(labels)
                lbl["le"] = str(bucket_le)
                lines.append(
                    f"{histogram.name}_bucket{_format_labels(lbl)} {count}"
                )
            # +Inf bucket
            inf_labels = dict(labels)
            inf_labels["le"] = "+Inf"
            lines.append(
                f"{histogram.name}_bucket{_format_labels(inf_labels)} "
                f"{data['_count']}"
            )
            lines.append(
                f"{histogram.name}_sum{_format_labels(labels)} {data['_sum']}"
            )
            lines.append(
                f"{histogram.name}_count{_format_labels(labels)} "
                f"{data['_count']}"
            )
        lines.append("")

    return "\n".join(lines) + "\n"
