"""RFC 7807 Problem Details error handler middleware.

Converts all unhandled exceptions and FastAPI HTTPExceptions into
RFC 7807 Problem Details JSON responses, providing a consistent
error format across all API endpoints.

Response format::

    {
        "type": "about:blank",
        "title": "Not Found",
        "status": 404,
        "detail": "Resource not found.",
        "instance": "/materials/abc-123",
        "request_id": "...",
        "trace_id": "..."
    }

Reference: https://www.rfc-editor.org/rfc/rfc7807
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ...shared.observability import get_request_context

_log = structlog.get_logger("ailine.api.errors")

# Map HTTP status codes to human-readable titles.
_STATUS_TITLES: dict[int, str] = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}


def _build_problem(
    *,
    status: int,
    detail: str,
    instance: str = "",
    type_uri: str = "about:blank",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an RFC 7807 Problem Details dict."""
    ctx = get_request_context()
    problem: dict[str, Any] = {
        "type": type_uri,
        "title": _STATUS_TITLES.get(status, "Error"),
        "status": status,
        "detail": detail,
    }
    if instance:
        problem["instance"] = instance
    if ctx.get("request_id"):
        problem["request_id"] = ctx["request_id"]
    if extra:
        problem.update(extra)
    return problem


def install_error_handlers(app: FastAPI) -> None:
    """Register RFC 7807 error handlers on the FastAPI app.

    Must be called after app creation but before serving requests.
    Handles:
    - Starlette/FastAPI HTTPException -> 4xx/5xx Problem Details
    - RequestValidationError -> 422 with field-level errors
    - Unhandled exceptions -> 500 Problem Details
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        problem = _build_problem(
            status=exc.status_code,
            detail=detail,
            instance=str(request.url.path),
        )
        _log.info(
            "http_error",
            status=exc.status_code,
            path=request.url.path,
            detail=detail[:200],
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=problem,
            media_type="application/problem+json",
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for err in exc.errors():
            loc = " -> ".join(str(part) for part in err.get("loc", []))
            errors.append({
                "field": loc,
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
            })
        problem = _build_problem(
            status=422,
            detail="Request validation failed.",
            instance=str(request.url.path),
            extra={"errors": errors},
        )
        _log.info(
            "validation_error",
            path=request.url.path,
            error_count=len(errors),
        )
        return JSONResponse(
            status_code=422,
            content=problem,
            media_type="application/problem+json",
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        _log.exception(
            "unhandled_error",
            path=request.url.path,
            error_type=type(exc).__name__,
            error=str(exc)[:500],
        )
        problem = _build_problem(
            status=500,
            detail="An unexpected error occurred.",
            instance=str(request.url.path),
        )
        return JSONResponse(
            status_code=500,
            content=problem,
            media_type="application/problem+json",
        )
