"""Async retry helper with exponential backoff for transient LLM errors.

Retries only on transient failures (network errors, rate limits, server errors).
Non-transient errors (validation, auth, bad request) propagate immediately.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

import structlog

log = structlog.get_logger(__name__)

T = TypeVar("T")

# Exception types considered transient and safe to retry.
_TRANSIENT_BASE_EXCEPTIONS: tuple[type[BaseException], ...] = (
    ConnectionError,
    TimeoutError,
    asyncio.TimeoutError,
)

# HTTP status codes considered transient.
_TRANSIENT_HTTP_CODES: frozenset[int] = frozenset({429, 500, 502, 503})


def _is_transient(exc: BaseException) -> bool:
    """Determine whether an exception represents a transient failure.

    Returns True for:
    - ConnectionError, TimeoutError, asyncio.TimeoutError
    - httpx.HTTPStatusError with status 429/500/502/503
    - Any exception wrapping these (via __cause__)
    """
    if isinstance(exc, _TRANSIENT_BASE_EXCEPTIONS):
        return True

    # Check httpx.HTTPStatusError without importing httpx at module level
    exc_type_name = type(exc).__name__
    if exc_type_name == "HTTPStatusError":
        response = getattr(exc, "response", None)
        if response is not None:
            status_code = getattr(response, "status_code", None)
            if status_code in _TRANSIENT_HTTP_CODES:
                return True

    # Check for Anthropic/OpenAI rate limit and server errors
    if exc_type_name in ("RateLimitError", "InternalServerError", "APIConnectionError"):
        return True

    # Check chained cause
    return exc.__cause__ is not None and _is_transient(exc.__cause__)


async def with_retry(
    fn: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    operation_name: str = "llm_call",
    run_id: str = "",
) -> T:
    """Execute an async callable with retry and exponential backoff.

    Only retries on transient errors (network issues, rate limits,
    server 5xx errors). All other exceptions propagate immediately.

    Args:
        fn: Zero-argument async callable to execute.
        max_attempts: Maximum number of attempts (including the first).
        initial_delay: Delay in seconds before the first retry.
        backoff_factor: Multiplier applied to delay after each retry.
        operation_name: Name for logging context.
        run_id: Correlation ID for structured logging.

    Returns:
        The result of fn() on success.

    Raises:
        The last exception if all attempts are exhausted, or the first
        non-transient exception immediately.
    """
    delay = initial_delay
    last_exc: BaseException | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return await fn()
        except Exception as exc:
            last_exc = exc

            if not _is_transient(exc):
                log.warning(
                    "retry.non_transient_error",
                    operation=operation_name,
                    run_id=run_id,
                    attempt=attempt,
                    error_type=type(exc).__name__,
                    error=str(exc),
                )
                raise

            if attempt >= max_attempts:
                log.error(
                    "retry.exhausted",
                    operation=operation_name,
                    run_id=run_id,
                    attempts=max_attempts,
                    error_type=type(exc).__name__,
                    error=str(exc),
                )
                raise

            log.warning(
                "retry.attempt",
                operation=operation_name,
                run_id=run_id,
                attempt=attempt,
                max_attempts=max_attempts,
                delay_seconds=delay,
                error_type=type(exc).__name__,
                error=str(exc),
            )
            await asyncio.sleep(delay)
            delay *= backoff_factor

    # Should not reach here, but satisfy type checker
    assert last_exc is not None
    raise last_exc
