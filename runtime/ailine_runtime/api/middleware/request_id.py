"""Request ID middleware for structured logging correlation.

Extracts ``X-Request-ID`` from the incoming request header, or generates a
new UUID4 if absent. The ID is stored in a ``contextvars.ContextVar`` so that
all structured log entries within the same request can include it
automatically via structlog's ``merge_contextvars`` processor.
"""

from __future__ import annotations

import contextvars
import re
import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable accessible throughout the request lifecycle.
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)

# Max 128 chars, alphanumeric + hyphens + dots + underscores
_VALID_RID = re.compile(r"^[a-zA-Z0-9._-]{1,128}$")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject a request ID into every request/response cycle.

    Behavior:
    1. Read ``X-Request-ID`` header from the request (if present and non-empty).
    2. Otherwise generate a new UUID4.
    3. Store the value in ``request_id_var`` (for structured logging).
    4. Bind it to structlog's context vars.
    5. Echo the value back in the ``X-Request-ID`` response header.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        rid = request.headers.get("X-Request-ID", "").strip()
        if not rid or not _VALID_RID.match(rid):
            rid = str(uuid.uuid4())

        # Store in contextvars for downstream access
        token = request_id_var.set(rid)
        try:
            # Bind request_id to structlog.  Do NOT call clear_contextvars()
            # here -- that would erase the teacher_id binding set by the
            # TenantContextMiddleware which runs earlier in the middleware
            # chain (Starlette LIFO ordering).
            structlog.contextvars.bind_contextvars(request_id=rid)

            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            request_id_var.reset(token)
            structlog.contextvars.unbind_contextvars("request_id")
