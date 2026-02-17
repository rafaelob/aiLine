"""Tenant context middleware -- extracts and validates teacher_id per request.

Populates ``contextvars`` with the authenticated teacher_id so that
downstream code can call ``get_current_teacher_id()`` /
``get_tenant()`` without passing the ID explicitly through every
function signature.

Authentication sources (in priority order):

1. **Authorization header** (``Bearer <JWT>``) -- production path.
   The JWT is decoded and the ``sub`` claim is used as teacher_id.
   Supports RS256, ES256, and HS256 algorithms with full signature
   verification, claims validation (iss/aud/exp/nbf/sub), and
   algorithm pinning (rejects ``"none"`` and unsigned tokens).

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
- ``/setup/*``
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

from ...domain.exceptions import InvalidTenantIdError
from ...shared.tenant import (
    clear_tenant_id,
    set_tenant_id,
    validate_teacher_id_format,
)

logger = structlog.get_logger("ailine.middleware.tenant_context")

# Paths excluded from tenant context enforcement.
_EXCLUDED_PREFIXES = (
    "/health/ready",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/demo",
    "/setup",
    "/metrics",
)

# Exact-match excluded paths (not prefix-based).
_EXCLUDED_EXACT = frozenset({"/health"})

# Algorithms considered safe. "none" is explicitly excluded.
_ALLOWED_ALGORITHMS = ("HS256", "RS256", "ES256")


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


def _get_jwt_config() -> dict[str, Any]:
    """Read JWT configuration from environment variables.

    Returns a dict with keys:
    - secret: HMAC secret (for HS256) or empty string
    - public_key: PEM-encoded public key (for RS256/ES256) or empty string
    - issuer: expected ``iss`` claim or None
    - audience: expected ``aud`` claim or None
    - algorithms: list of allowed algorithms
    """
    secret = os.getenv("AILINE_JWT_SECRET", "")
    public_key = os.getenv("AILINE_JWT_PUBLIC_KEY", "")
    issuer = os.getenv("AILINE_JWT_ISSUER", "") or None
    audience = os.getenv("AILINE_JWT_AUDIENCE", "") or None

    # Determine algorithms based on what key material is available
    algorithms_env = os.getenv("AILINE_JWT_ALGORITHMS", "")
    if algorithms_env:
        algorithms = [
            a.strip()
            for a in algorithms_env.split(",")
            if a.strip() in _ALLOWED_ALGORITHMS
        ]
    elif public_key:
        algorithms = ["RS256", "ES256"]
    elif secret:
        algorithms = ["HS256"]
    else:
        algorithms = []

    return {
        "secret": secret,
        "public_key": public_key,
        "issuer": issuer,
        "audience": audience,
        "algorithms": algorithms,
    }


def _extract_teacher_id_from_jwt(token: str) -> tuple[str | None, str | None]:
    """Extract teacher_id (``sub`` claim) from a JWT token.

    Returns a tuple of (teacher_id, error_reason). If teacher_id is not
    None, error_reason is None and vice versa. Both being None means
    no JWT config is set and unverified fallback was used but sub was
    missing.
    """
    cfg = _get_jwt_config()
    has_key_material = bool(cfg["secret"]) or bool(cfg["public_key"])

    if has_key_material:
        result, error = _verified_jwt_decode(token, cfg)
        if result is not None:
            return result, None
        # Verified decode failed -- do NOT fall through to unverified
        return None, error

    # Fallback: unverified base64 decode (only when no key material)
    if _is_dev_mode():
        return _unverified_jwt_decode(token), None

    # In non-dev mode without key material, reject JWT silently
    logger.warning(
        "jwt_no_key_material",
        msg=(
            "JWT received but no AILINE_JWT_SECRET or AILINE_JWT_PUBLIC_KEY "
            "is configured. Set key material or enable dev mode."
        ),
    )
    return None, "no_key_material"


def _verified_jwt_decode(
    token: str, cfg: dict[str, Any]
) -> tuple[str | None, str | None]:
    """Decode and verify a JWT using PyJWT.

    Supports HS256 (symmetric), RS256, and ES256 (asymmetric).
    Validates exp, nbf, iss, aud, and sub claims.
    Rejects the ``none`` algorithm unconditionally.

    Returns (sub_claim, None) on success, (None, error_reason) on failure.
    """
    try:
        import jwt as pyjwt
    except ImportError:
        logger.warning(
            "jwt_library_missing",
            msg=(
                "JWT key material is configured but PyJWT is not installed. Install it with: pip install PyJWT[crypto]"
            ),
        )
        return None, "jwt_library_missing"

    algorithms = cfg["algorithms"]
    if not algorithms:
        logger.warning("jwt_no_algorithms", msg="No allowed JWT algorithms configured")
        return None, "no_algorithms"

    # Reject 'none' algorithm explicitly (defense in depth)
    algorithms = [a for a in algorithms if a.lower() != "none"]

    # Determine the verification key
    if cfg["public_key"]:
        key: str | bytes = cfg["public_key"]
    elif cfg["secret"]:
        key = cfg["secret"]
    else:
        return None, "no_key_material"

    try:
        decode_opts: dict[str, Any] = {
            "algorithms": algorithms,
            "options": {
                "require": ["exp", "sub"],
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iss": cfg["issuer"] is not None,
                "verify_aud": cfg["audience"] is not None,
            },
        }
        if cfg["issuer"]:
            decode_opts["issuer"] = cfg["issuer"]
        if cfg["audience"]:
            decode_opts["audience"] = cfg["audience"]

        payload = pyjwt.decode(token, key, **decode_opts)

        sub = payload.get("sub")
        if not sub or not isinstance(sub, str):
            logger.warning("jwt_missing_sub", msg="JWT payload missing 'sub' claim")
            return None, "missing_sub"

        logger.info(
            "auth_jwt_success",
            teacher_id=sub,
            issuer=payload.get("iss"),
        )
        return sub, None

    except pyjwt.ExpiredSignatureError:
        logger.warning("jwt_expired", msg="JWT token has expired")
        return None, "expired"
    except pyjwt.ImmatureSignatureError:
        logger.warning("jwt_not_yet_valid", msg="JWT nbf claim is in the future")
        return None, "not_yet_valid"
    except pyjwt.InvalidIssuerError:
        logger.warning("jwt_invalid_issuer", msg="JWT issuer mismatch")
        return None, "invalid_issuer"
    except pyjwt.InvalidAudienceError:
        logger.warning("jwt_invalid_audience", msg="JWT audience mismatch")
        return None, "invalid_audience"
    except pyjwt.InvalidAlgorithmError:
        logger.warning("jwt_invalid_algorithm", msg="JWT uses disallowed algorithm")
        return None, "invalid_algorithm"
    except pyjwt.DecodeError as exc:
        logger.warning("jwt_decode_error", error=str(exc))
        return None, "decode_error"
    except pyjwt.InvalidTokenError as exc:
        logger.warning("jwt_invalid", error=str(exc))
        return None, "invalid_token"


def _unverified_jwt_decode(token: str) -> str | None:
    """Decode JWT payload without signature verification (dev-mode fallback).

    Only used when no key material is configured AND dev mode is enabled.
    Extracts the ``sub`` claim from the base64-encoded payload segment.
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
        payload: dict[str, Any] = json.loads(payload_bytes)
        sub = payload.get("sub")
        return str(sub) if sub is not None else None
    except (ValueError, KeyError, json.JSONDecodeError):
        logger.warning("unverified_jwt_decode_failed")
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
        if path in _EXCLUDED_EXACT or any(
            path.startswith(prefix) for prefix in _EXCLUDED_PREFIXES
        ):
            return await call_next(request)

        teacher_id: str | None = None
        jwt_error: str | None = None

        # 1. Try Authorization header (JWT)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            jwt_token = auth_header[7:].strip()
            if jwt_token:
                teacher_id, jwt_error = _extract_teacher_id_from_jwt(jwt_token)
                if teacher_id:
                    logger.debug(
                        "tenant_from_jwt",
                        teacher_id=teacher_id,
                        path=path,
                    )
                elif jwt_error:
                    # JWT was present but invalid -- log auth failure
                    logger.warning(
                        "auth_jwt_failure",
                        reason=jwt_error,
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
            except (ValueError, InvalidTenantIdError):
                logger.warning("teacher_id_format_invalid", path=path)
                return JSONResponse(
                    status_code=422,
                    content={
                        "detail": (
                            "Invalid teacher_id format. Must be a UUID or alphanumeric identifier (max 128 chars)."
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
