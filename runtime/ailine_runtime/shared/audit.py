"""Structured audit logging for security-relevant events.

Provides typed helpers for recording:
- Authentication success/failure
- Admin actions (CRUD on resources)
- Content access (material reads, tutor interactions)
- LLM calls with cost tracking

All events are emitted via structlog as structured JSON, enriched with
request context (request_id, teacher_id) when available. These logs can
be ingested by any log aggregator (ELK, Loki, CloudWatch, etc.) and
queried for security auditing, compliance, and incident response.

Event naming convention: ``audit.<category>.<action>``
"""

from __future__ import annotations

from typing import Any

import structlog

from .observability import get_request_context

_log = structlog.get_logger("ailine.audit")


def _enrich(data: dict[str, Any]) -> dict[str, Any]:
    """Inject request context into audit event data."""
    ctx = get_request_context()
    if ctx["request_id"] is not None and "request_id" not in data:
        data["request_id"] = ctx["request_id"]
    if ctx["teacher_id"] is not None and "teacher_id" not in data:
        data["teacher_id"] = ctx["teacher_id"]
    return data


# ---------------------------------------------------------------------------
# Authentication events
# ---------------------------------------------------------------------------


def log_auth_success(
    *,
    teacher_id: str,
    method: str,
    issuer: str | None = None,
    ip: str | None = None,
) -> None:
    """Record a successful authentication event.

    Args:
        teacher_id: The authenticated teacher ID.
        method: Auth method used ("jwt", "dev_header", "body").
        issuer: JWT issuer claim if applicable.
        ip: Client IP address.
    """
    data = _enrich({
        "teacher_id": teacher_id,
        "method": method,
        "issuer": issuer,
        "ip": ip,
    })
    _log.info("audit.auth.success", **data)


def log_auth_failure(
    *,
    reason: str,
    method: str,
    ip: str | None = None,
    token_hint: str | None = None,
) -> None:
    """Record a failed authentication attempt.

    Args:
        reason: Why authentication failed (e.g., "expired", "invalid_sig").
        method: Auth method attempted.
        ip: Client IP address.
        token_hint: First 8 chars of the token (for correlation, not security).
    """
    data = _enrich({
        "reason": reason,
        "method": method,
        "ip": ip,
        "token_hint": token_hint,
    })
    _log.warning("audit.auth.failure", **data)


# ---------------------------------------------------------------------------
# Admin / resource action events
# ---------------------------------------------------------------------------


def log_admin_action(
    *,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    detail: str | None = None,
) -> None:
    """Record an administrative action.

    Args:
        action: The action performed ("create", "update", "delete").
        resource_type: Type of resource ("material", "tutor", "plan", "course").
        resource_id: ID of the affected resource.
        detail: Optional extra detail.
    """
    data = _enrich({
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "detail": detail,
    })
    _log.info("audit.admin.action", **data)


# ---------------------------------------------------------------------------
# Content access events
# ---------------------------------------------------------------------------


def log_content_access(
    *,
    resource_type: str,
    resource_id: str,
    access_type: str = "read",
) -> None:
    """Record a content access event.

    Args:
        resource_type: Type of resource accessed.
        resource_id: ID of the resource.
        access_type: Type of access ("read", "download", "stream").
    """
    data = _enrich({
        "resource_type": resource_type,
        "resource_id": resource_id,
        "access_type": access_type,
    })
    _log.info("audit.content.access", **data)


# ---------------------------------------------------------------------------
# LLM call events (with cost tracking)
# ---------------------------------------------------------------------------


def log_llm_call(
    *,
    provider: str,
    model: str,
    tier: str,
    latency_ms: float,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_usd: float | None = None,
    success: bool,
    error: str | None = None,
) -> None:
    """Record an LLM API call with cost tracking.

    Args:
        provider: LLM provider ("anthropic", "openai", "gemini").
        model: Model ID.
        tier: SmartRouter tier.
        latency_ms: Call latency in milliseconds.
        input_tokens: Input token count.
        output_tokens: Output token count.
        cost_usd: Estimated cost in USD (None if unknown).
        success: Whether the call succeeded.
        error: Error message if the call failed.
    """
    data = _enrich({
        "provider": provider,
        "model": model,
        "tier": tier,
        "latency_ms": round(latency_ms, 2),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost_usd, 6) if cost_usd is not None else None,
        "success": success,
    })
    if error is not None:
        data["error"] = error
    if success:
        _log.info("audit.llm.call", **data)
    else:
        _log.warning("audit.llm.call.failed", **data)
