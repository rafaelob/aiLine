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
import functools
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
    clear_org_id,
    clear_tenant_id,
    clear_user_role,
    set_org_id,
    set_tenant_id,
    set_user_role,
    validate_teacher_id_format,
)

logger = structlog.get_logger("ailine.middleware.tenant_context")

# Path prefixes excluded from tenant context enforcement.
# Use trailing slash to ensure segment-boundary matching:
# e.g. "/demo/" matches "/demo/login" but NOT "/demo_anything".
# Exact paths (no trailing content) go in _EXCLUDED_EXACT instead.
_EXCLUDED_PREFIXES = (
    "/docs/",
    "/redoc/",
    "/demo/",
    "/setup/",
)

# Exact-match excluded paths (not prefix-based).
# /auth/login, /auth/register, /auth/roles don't require tenant context.
# /auth/me DOES require tenant context (authenticated endpoint).
_EXCLUDED_EXACT = frozenset({
    "/health",
    "/health/ready",
    "/docs",
    "/redoc",
    "/demo",
    "/setup",
    "/openapi.json",
    "/auth/login",
    "/auth/register",
    "/auth/roles",
})

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
    # Refresh caches so env changes (e.g. test fixtures) take effect.
    _is_dev_mode.cache_clear()
    _get_jwt_config.cache_clear()

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


@functools.lru_cache(maxsize=1)
def _is_dev_mode() -> bool:
    """Check if dev mode is enabled (cached after first call per app lifecycle).

    Uses lru_cache to avoid per-request os.getenv() overhead.
    Call ``_is_dev_mode.cache_clear()`` when the environment changes
    (e.g. in create_app or test fixtures).
    """
    return os.getenv("AILINE_DEV_MODE", "").lower() in ("true", "1", "yes")


@functools.lru_cache(maxsize=1)
def _get_jwt_config() -> dict[str, Any]:
    """Read JWT configuration from environment variables (cached).

    Uses lru_cache to avoid per-request os.getenv() overhead.
    Call ``_get_jwt_config.cache_clear()`` when the environment changes
    (e.g. in create_app or test fixtures).

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


class _JwtClaims:
    """Lightweight container for claims extracted from a JWT."""

    __slots__ = ("org_id", "role", "teacher_id")

    def __init__(
        self,
        teacher_id: str | None = None,
        role: str | None = None,
        org_id: str | None = None,
    ) -> None:
        self.teacher_id = teacher_id
        self.role = role
        self.org_id = org_id


def _extract_teacher_id_from_jwt(
    token: str,
) -> tuple[_JwtClaims, str | None]:
    """Extract claims (sub, role, org_id) from a JWT token.

    Returns a tuple of (_JwtClaims, error_reason). If teacher_id inside
    the claims is not None, error_reason is None and vice versa.
    """
    cfg = _get_jwt_config()
    has_key_material = bool(cfg["secret"]) or bool(cfg["public_key"])

    if has_key_material:
        claims, error = _verified_jwt_decode(token, cfg)
        if claims.teacher_id is not None:
            return claims, None
        # Verified decode failed -- do NOT fall through to unverified
        return _JwtClaims(), error

    # Fallback: unverified base64 decode (only when no key material)
    if _is_dev_mode():
        claims = _unverified_jwt_decode(token)
        # SECURITY: Unverified tokens cannot escalate roles.
        # Only extract sub; hardcode role to "teacher" to prevent
        # forged super_admin claims in dev mode.
        claims.role = "teacher"
        claims.org_id = None
        return claims, None

    # In non-dev mode without key material, reject JWT silently
    logger.warning(
        "jwt_no_key_material",
        msg=(
            "JWT received but no AILINE_JWT_SECRET or AILINE_JWT_PUBLIC_KEY "
            "is configured. Set key material or enable dev mode."
        ),
    )
    return _JwtClaims(), "no_key_material"


def _verified_jwt_decode(
    token: str, cfg: dict[str, Any]
) -> tuple[_JwtClaims, str | None]:
    """Decode and verify a JWT using PyJWT.

    Supports HS256 (symmetric), RS256, and ES256 (asymmetric).
    Validates exp, nbf, iss, aud, and sub claims.
    Rejects the ``none`` algorithm unconditionally.

    Returns (_JwtClaims, None) on success, (_JwtClaims(), error_reason) on failure.
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
        return _JwtClaims(), "jwt_library_missing"

    algorithms = cfg["algorithms"]
    if not algorithms:
        logger.warning("jwt_no_algorithms", msg="No allowed JWT algorithms configured")
        return _JwtClaims(), "no_algorithms"

    # Reject 'none' algorithm explicitly (defense in depth)
    algorithms = [a for a in algorithms if a.lower() != "none"]

    # Determine the verification key
    if cfg["public_key"]:
        key: str | bytes = cfg["public_key"]
    elif cfg["secret"]:
        key = cfg["secret"]
    else:
        return _JwtClaims(), "no_key_material"

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
            return _JwtClaims(), "missing_sub"

        # Extract RBAC claims with backward-compatible defaults
        role = payload.get("role", "teacher")
        org_id = payload.get("org_id")

        logger.debug(
            "auth_jwt_success",
            teacher_id=sub,
            role=role,
            org_id=org_id,
            issuer=payload.get("iss"),
        )
        return _JwtClaims(teacher_id=sub, role=role, org_id=org_id), None

    except pyjwt.ExpiredSignatureError:
        logger.warning("jwt_expired", msg="JWT token has expired")
        return _JwtClaims(), "expired"
    except pyjwt.ImmatureSignatureError:
        logger.warning("jwt_not_yet_valid", msg="JWT nbf claim is in the future")
        return _JwtClaims(), "not_yet_valid"
    except pyjwt.InvalidIssuerError:
        logger.warning("jwt_invalid_issuer", msg="JWT issuer mismatch")
        return _JwtClaims(), "invalid_issuer"
    except pyjwt.InvalidAudienceError:
        logger.warning("jwt_invalid_audience", msg="JWT audience mismatch")
        return _JwtClaims(), "invalid_audience"
    except pyjwt.InvalidAlgorithmError:
        logger.warning("jwt_invalid_algorithm", msg="JWT uses disallowed algorithm")
        return _JwtClaims(), "invalid_algorithm"
    except pyjwt.DecodeError as exc:
        logger.warning("jwt_decode_error", error=str(exc))
        return _JwtClaims(), "decode_error"
    except pyjwt.InvalidTokenError as exc:
        logger.warning("jwt_invalid", error=str(exc))
        return _JwtClaims(), "invalid_token"


def _unverified_jwt_decode(token: str) -> _JwtClaims:
    """Decode JWT payload without signature verification (dev-mode fallback).

    Only used when no key material is configured AND dev mode is enabled.
    Extracts sub, role, and org_id claims from the base64-encoded payload.
    """
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return _JwtClaims()
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload: dict[str, Any] = json.loads(payload_bytes)
        sub = payload.get("sub")
        teacher_id = str(sub) if sub is not None else None
        role = payload.get("role", "teacher")
        org_id = payload.get("org_id")
        return _JwtClaims(
            teacher_id=teacher_id,
            role=role,
            org_id=str(org_id) if org_id is not None else None,
        )
    except (ValueError, KeyError, json.JSONDecodeError):
        logger.warning("unverified_jwt_decode_failed")
        return _JwtClaims()


def extract_teacher_id_from_jwt(token: str) -> tuple[str | None, str | None]:
    """Public API: extract teacher_id from a JWT token.

    Returns a tuple of (teacher_id, error_reason). If teacher_id is not
    None, error_reason is None and vice versa.

    This is the public wrapper around the internal ``_extract_teacher_id_from_jwt``
    function, intended for use by WebSocket endpoints and other code that
    needs JWT verification outside the middleware pipeline.
    """
    claims, error = _extract_teacher_id_from_jwt(token)
    return claims.teacher_id, error


def extract_claims_from_jwt(token: str) -> tuple[_JwtClaims, str | None]:
    """Public API: extract all RBAC claims from a JWT token.

    Returns a tuple of (_JwtClaims, error_reason). Extends
    ``extract_teacher_id_from_jwt`` with role and org_id.
    """
    return _extract_teacher_id_from_jwt(token)


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
        role: str | None = None
        org_id: str | None = None
        jwt_error: str | None = None

        # 1. Try Authorization header (JWT)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            jwt_token = auth_header[7:].strip()
            if jwt_token:
                claims, jwt_error = _extract_teacher_id_from_jwt(jwt_token)
                teacher_id = claims.teacher_id
                role = claims.role
                org_id = claims.org_id
                if teacher_id:
                    logger.debug(
                        "tenant_from_jwt",
                        teacher_id=teacher_id,
                        role=role,
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
                    # Also check for X-User-Role and X-Org-ID (dev mode only)
                    raw_role = (
                        request.headers.get("X-User-Role", "").strip() or "teacher"
                    )
                    # SECURITY: Restrict dev mode role escalation — super_admin
                    # cannot be assumed via dev headers (must use real JWT).
                    dev_allowed_roles = frozenset({
                        "teacher", "student", "parent", "school_admin",
                    })
                    if raw_role not in dev_allowed_roles:
                        logger.warning(
                            "dev_role_escalation_blocked",
                            requested_role=raw_role,
                            teacher_id=teacher_id,
                            path=path,
                            msg=(
                                f"X-User-Role '{raw_role}' blocked in dev mode. "
                                "Only teacher/student/parent/school_admin allowed via headers."
                            ),
                        )
                        raw_role = "teacher"
                    role = raw_role
                    org_id = (
                        request.headers.get("X-Org-ID", "").strip() or None
                    )
                    logger.debug(
                        "tenant_from_header",
                        teacher_id=teacher_id,
                        role=role,
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
            tid_token = set_tenant_id(teacher_id)
            role_token = set_user_role(role or "teacher")
            org_token = set_org_id(org_id) if org_id else None
            try:
                # Also bind to structlog for correlation
                structlog.contextvars.bind_contextvars(
                    teacher_id=teacher_id, role=role or "teacher",
                )
                response = await call_next(request)
                return response
            finally:
                clear_tenant_id(tid_token)
                clear_user_role(role_token)
                if org_token is not None:
                    clear_org_id(org_token)
                structlog.contextvars.unbind_contextvars("teacher_id", "role")
        else:
            # No tenant context -- proceed without it.
            # Endpoints requiring auth will call get_current_teacher_id()
            # which raises 401.
            return await call_next(request)
