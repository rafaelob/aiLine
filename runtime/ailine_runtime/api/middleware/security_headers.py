"""Security headers middleware.

Adds recommended security-hardening HTTP headers to every response:

- ``X-Content-Type-Options: nosniff`` -- prevents MIME-type sniffing.
- ``X-Frame-Options: DENY`` -- prevents clickjacking via iframes.
- ``Referrer-Policy: strict-origin-when-cross-origin`` -- limits referrer leakage.
- ``Permissions-Policy`` -- disables unused browser features.
- ``Strict-Transport-Security`` -- enforces HTTPS.
- ``Content-Security-Policy`` -- restricts resource origins.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Headers applied to every response.
_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(self), microphone=(), geolocation=()",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' https://vlibras.gov.br; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "font-src 'self'; "
        "frame-src https://vlibras.gov.br; "
        "frame-ancestors 'none'; "
        "object-src 'none'; "
        "base-uri 'self'"
    ),
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Append security-hardening headers to every HTTP response."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response
