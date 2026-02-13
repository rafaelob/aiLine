"""Tenant context middleware -- extracts and validates teacher_id per request.

Populates ``contextvars`` with the authenticated teacher_id so that
downstream code can call ``get_current_teacher_id()`` /
``get_tenant()`` without passing the ID explicitly through every
function signature.

Authentication sources (in priority order):

1. **Authorization header** (``Bearer <JWT>``) -- production path.
   The JWT is decoded and the ``sub`` claim is used as teacher_id.
   *Note:* Full JWT verification (signature, expiry) is a TODO for
   the production hardening phase; currently we decode without
   verification for pre-MVP convenience.

2. **X-Teacher-ID header** -- development/testing convenience.
   Only accepted when ``AILINE_DEV_MODE=true`` is explicitly set.
   This avoids requiring JWT infrastructure during local dev.

   **SECURITY WARNING:** The X-Teacher-ID header bypass allows any
   caller to impersonate any teacher without authentication. This
   MUST NEVER be enabled in production. The ``validate_dev_mode()``
   function enforces this constraint at startup by raising
   ``ValueError`` if ``AILINE_DEV_MODE=true`` and
   ``AILINE_ENV=production``.

3. **Request body ``teacher_id`` field** -- legacy backward compatibility.
   If neither header is present, the middleware does NOT block the
   request. Router handlers can still read ``teacher_id`` from the
   body and set it manually. This preserves backward compat with
   existing clients that embed teacher_id in the payload.

Routes that are excluded from tenant enforcement:
- ``/health``
- ``/docs``, ``/openapi.json``, ``/redoc``
- ``/demo/*``
"""

from __future__ import annotations

import base64
import json
import os
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ...shared.tenant import (
    clear_tenant_id,
    set_tenant_id,
    validate_teacher_id_format,
)

logger = structlog.get_logger("ailine.middleware.tenant_context")

# Paths excluded from tenant context enforcement.
_EXCLUDED_PREFIXES = (
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/demo",
)


def validate_dev_mode(*, env: str = "") -> None:
    """Validate dev-mode safety at application startup.

    Must be called during app creation. Raises ``ValueError`` if
    dev mode (X-Teacher-ID bypass) is enabled in a production
    environment, and logs a WARNING in any non-production
    environment where dev mode is active.

    Args:
        env: The current deployment environment (from ``settings.env``).
             Expected values: ``"development"``, ``"staging"``,
             ``"production"``.

    Raises:
        ValueError: If ``AILINE_DEV_MODE=true`` and *env* is
            ``"production"``.
    """
    if not _is_dev_mode():
        return

    if env == "production":
        raise ValueError(
            "FATAL: AILINE_DEV_MODE=true is FORBIDDEN in production. "
            "The X-Teacher-ID header bypass allows unauthenticated "
            "impersonation of any teacher. Remove AILINE_DEV_MODE from "
            "the environment or set AILINE_ENV to a non-production value."
        )

    logger.warning(
        "dev_mode_enabled",
        msg=(
            "X-Teacher-ID header bypass is ACTIVE. Any client can "
            "impersonate any teacher without authentication. This "
            "must NOT be used in production."
        ),
        env=env or "unknown",
    )


def _is_dev_mode() -> bool:
    """Check if dev mode is enabled via environment variable."""
    return os.getenv("AILINE_DEV_MODE", "").lower() in ("true", "1", "yes")


def _extract_teacher_id_from_jwt(token: str) -> str | None:
    """Extract teacher_id (``sub`` claim) from a JWT token.

    Attempts verified decode first (PyJWT with HS256, exp/iss validation).
    If PyJWT is not installed, falls back to unverified base64 decode
    (suitable for pre-MVP / local development only).

    Environment variables used for verified mode:
    - ``AILINE_JWT_SECRET``: HMAC secret for HS256 signature verification.
    - ``AILINE_JWT_ISSUER``: Expected ``iss`` claim (optional; skipped if empty).

    Returns None if the token cannot be decoded or lacks a ``sub`` claim.
    """
    # Try verified decode when PyJWT is available and a secret is configured
    jwt_secret = os.getenv("AILINE_JWT_SECRET", "")
    if jwt_secret:
        result = _verified_jwt_decode(token, jwt_secret)
        if result is not None:
            return result
        # Verified decode failed (expired, bad signature, etc.)
        # Do NOT fall through to unverified decode -- that would
        # bypass the security the secret was meant to enforce.
        return None

    # Fallback: unverified base64 decode (pre-MVP convenience)
    return _unverified_jwt_decode(token)


def _verified_jwt_decode(token: str, secret: str) -> str | None:
    """Decode and verify a JWT using PyJWT (HS256).

    Validates ``exp`` (expiry) and optionally ``iss`` (issuer) claims.
    Returns the ``sub`` claim on success, None on any failure.
    """
    try:
        import jwt as pyjwt
    except ImportError:
        logger.warning(
            "jwt_library_missing",
            msg=(
                "AILINE_JWT_SECRET is set but PyJWT is not installed. "
                "Install it with: pip install PyJWT"
            ),
        )
        return None

    issuer = os.getenv("AILINE_JWT_ISSUER", "") or None
    try:
        decode_opts: dict[str, Any] = {
            "algorithms": ["HS256"],
            "options": {"require": ["exp", "sub"]},
        }
        if issuer:
            decode_opts["issuer"] = issuer
        payload = pyjwt.decode(token, secret, **decode_opts)
        return payload.get("sub")
    except pyjwt.ExpiredSignatureError:
        logger.warning("jwt_expired", msg="JWT token has expired")
        return None
    except pyjwt.InvalidIssuerError:
        logger.warning("jwt_invalid_issuer", msg="JWT issuer mismatch")
        return None
    except pyjwt.InvalidTokenError as exc:
        logger.warning("jwt_invalid", error=str(exc))
        return None


def _unverified_jwt_decode(token: str) -> str | None:
    """Decode JWT payload without signature verification (pre-MVP fallback).

    Only used when AILINE_JWT_SECRET is not configured. Extracts the
    ``sub`` claim from the base64-encoded payload segment.
    """
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes)
        return payload.get("sub")
    except Exception:
        return None


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Extract teacher_id from request and store in contextvars.

    The middleware is permissive: if no teacher_id can be extracted,
    the request proceeds without a tenant context. Endpoints that
    require tenant isolation call ``get_current_teacher_id()`` which
    will raise 401 if the context is missing.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # Skip excluded paths
        path = request.url.path
        if any(path.startswith(prefix) for prefix in _EXCLUDED_PREFIXES):
            return await call_next(request)

        teacher_id: str | None = None

        # 1. Try Authorization header (JWT)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            jwt_token = auth_header[7:].strip()
            if jwt_token:
                teacher_id = _extract_teacher_id_from_jwt(jwt_token)
                if teacher_id:
                    logger.debug(
                        "tenant_from_jwt",
                        teacher_id=teacher_id,
                        path=path,
                    )

        # 2. Try X-Teacher-ID header (dev mode only)
        if teacher_id is None:
            x_teacher_id = request.headers.get("X-Teacher-ID", "").strip()
            if x_teacher_id:
                if _is_dev_mode():
                    teacher_id = x_teacher_id
                    logger.debug(
                        "tenant_from_header",
                        teacher_id=teacher_id,
                        path=path,
                    )
                else:
                    logger.warning(
                        "x_teacher_id_ignored",
                        reason="AILINE_DEV_MODE is not enabled",
                        path=path,
                    )

        # Validate format if we have a teacher_id
        if teacher_id is not None:
            try:
                teacher_id = validate_teacher_id_format(teacher_id)
            except Exception:
                return JSONResponse(
                    status_code=422,
                    content={
                        "detail": (
                            "Invalid teacher_id format. Must be a UUID or "
                            "alphanumeric identifier (max 128 chars)."
                        )
                    },
                )

        # Set in contextvars (None means "no tenant context")
        if teacher_id is not None:
            token = set_tenant_id(teacher_id)
            try:
                # Also bind to structlog for correlation
                structlog.contextvars.bind_contextvars(teacher_id=teacher_id)
                response = await call_next(request)
                return response
            finally:
                clear_tenant_id(token)
                structlog.contextvars.unbind_contextvars("teacher_id")
        else:
            # No tenant context -- proceed without it.
            # Endpoints requiring auth will call get_current_teacher_id()
            # which raises 401.
            return await call_next(request)
