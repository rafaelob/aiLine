"""Authentication API router -- login, register, user profile.

Provides JWT-based authentication with role-based access.
In dev mode (AILINE_DEV_MODE=true), passwords are not required.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import os
import re
import secrets
import time
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from ...adapters.db.models import UserRow
from ...adapters.db.user_repository import InMemoryUserRepository, UserRepository
from ...app.authz import require_authenticated
from ...domain.entities.user import UserRole
from ...shared.tenant import get_current_org_id, get_current_user_role

logger = structlog.get_logger("ailine.api.auth")

router = APIRouter()


# -- Request/Response schemas ------------------------------------------------

# Lightweight email format check (RFC 5321 simplified).
# Rejects obviously malformed addresses without pulling in email-validator.
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


_ALLOWED_SELF_ASSIGN_ROLES = frozenset({
    UserRole.TEACHER, UserRole.STUDENT, UserRole.PARENT,
})


def _validate_role(role: str, *, allow_admin: bool = False) -> str:
    """Validate and normalize a role string against UserRole enum.

    Non-admin users cannot self-assign admin roles (super_admin, school_admin).
    Returns a valid UserRole value, defaulting to 'teacher' on invalid input.
    """
    try:
        validated = UserRole(role)
    except ValueError:
        return UserRole.TEACHER
    if not allow_admin and validated not in _ALLOWED_SELF_ASSIGN_ROLES:
        return UserRole.TEACHER
    return validated


class LoginRequest(BaseModel):
    """Login request body."""

    email: str = Field(..., max_length=320, description="User email")
    password: str = Field(default="", description="Password (optional in dev mode)")
    role: str = Field(default="teacher", description="Requested role")

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str) -> str:
        if not _EMAIL_RE.match(v):
            msg = "Invalid email format"
            raise ValueError(msg)
        return v.lower().strip()


class RegisterRequest(BaseModel):
    """Register request body."""

    email: str = Field(..., max_length=320)
    display_name: str = Field(..., max_length=200)
    role: str = Field(default="teacher")
    org_id: str | None = None
    locale: str = "en"
    password: str = Field(default="", description="Password (optional in dev mode)")

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str) -> str:
        if not _EMAIL_RE.match(v):
            msg = "Invalid email format"
            raise ValueError(msg)
        return v.lower().strip()


class UserResponse(BaseModel):
    """User profile response."""

    id: str
    email: str
    display_name: str
    role: str
    org_id: str | None = None
    locale: str = "en"
    avatar_url: str = ""
    accessibility_profile: str = ""
    is_active: bool = True


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# -- User store (InMemoryUserRepository pre-MVP; PostgresUserRepository post-MVP)

_user_repo: UserRepository = InMemoryUserRepository()
_users_lock = asyncio.Lock()

# Dedicated login rate limiter: per-IP, 5 attempts per minute.
_login_attempts: dict[str, list[float]] = {}
_login_rate_lock = asyncio.Lock()
_LOGIN_MAX_ATTEMPTS = 5
_LOGIN_WINDOW_SECONDS = 60.0
_LOGIN_CLEANUP_INTERVAL = 300.0  # Prune stale IPs every 5 minutes
_login_last_cleanup = 0.0


def _user_response(user: UserRow) -> UserResponse:
    """Build a UserResponse from a UserRow ORM model."""
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        org_id=user.org_id,
        locale=user.locale or "en",
        avatar_url=user.avatar_url or "",
        accessibility_profile=user.accessibility_profile or "",
        is_active=user.is_active,
    )


def _hash_password(password: str, salt: bytes | None = None) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with random salt.

    Format: ``<hex_salt>$<hex_derived_key>``
    Uses 600,000 iterations per NIST SP 800-132 recommendation.
    Returns empty string for empty password (demo/dev profiles).
    """
    if not password:
        return ""
    if salt is None:
        salt = secrets.token_bytes(32)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations=600_000)
    return f"{salt.hex()}${dk.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored PBKDF2 hash.

    Returns False if the password is empty or the hash format is invalid.
    Uses constant-time comparison via hmac.compare_digest.
    """
    if not password or not stored_hash:
        return False
    if "$" not in stored_hash:
        # Legacy SHA-256 hash (no salt separator) — reject for safety
        return False
    salt_hex, _, _dk_hex = stored_hash.partition("$")
    try:
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    new_hash = _hash_password(password, salt=salt)
    return hmac.compare_digest(new_hash, stored_hash)


def _create_jwt(user_id: str, role: str, org_id: str | None = None) -> str:
    """Create a signed JWT using PyJWT (HS256).

    Uses the same secret and algorithm as the verification path in
    TenantContextMiddleware, ensuring tokens produced here are
    correctly verifiable by the middleware.

    In dev mode without AILINE_JWT_SECRET, falls back to a dev-only secret.
    """
    import jwt as pyjwt

    dev_mode = os.getenv("AILINE_DEV_MODE", "").lower() in ("true", "1", "yes")
    secret = os.getenv("AILINE_JWT_SECRET", "")
    if not secret:
        if not dev_mode:
            raise RuntimeError(
                "AILINE_JWT_SECRET must be set in non-dev mode. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(48))'"
            )
        secret = "dev-secret-not-for-production-use-32bytes!"

    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "exp": now + 86400,  # 24h
        "iat": now,
    }
    if org_id:
        payload["org_id"] = org_id

    return pyjwt.encode(payload, secret, algorithm="HS256")


async def _check_login_rate(client_ip: str) -> None:
    """Enforce per-IP login rate limit (5 attempts/minute).

    Raises HTTPException 429 if the limit is exceeded.
    Periodically prunes stale IP entries to prevent unbounded memory growth.
    """
    global _login_last_cleanup
    now = time.monotonic()
    async with _login_rate_lock:
        cutoff = now - _LOGIN_WINDOW_SECONDS

        # Periodic cleanup: prune IPs whose attempts are all expired
        if now - _login_last_cleanup > _LOGIN_CLEANUP_INTERVAL:
            stale_ips = [
                ip for ip, ts_list in _login_attempts.items()
                if all(t <= cutoff for t in ts_list)
            ]
            for ip in stale_ips:
                del _login_attempts[ip]
            _login_last_cleanup = now

        attempts = _login_attempts.get(client_ip, [])
        attempts = [t for t in attempts if t > cutoff]
        if len(attempts) >= _LOGIN_MAX_ATTEMPTS:
            logger.warning(
                "auth.login_rate_limited",
                client_ip=client_ip,
                attempts=len(attempts),
            )
            raise HTTPException(
                status_code=429,
                detail="Too many login attempts. Please try again later.",
                headers={"Retry-After": str(int(_LOGIN_WINDOW_SECONDS))},
            )
        attempts.append(now)
        _login_attempts[client_ip] = attempts


# -- Endpoints ---------------------------------------------------------------


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request) -> TokenResponse:
    """Authenticate user and return JWT token.

    In dev mode, any email/role combination is accepted without password.
    Includes per-IP rate limiting (5 attempts/minute) to mitigate brute force.
    """
    # Per-IP login rate limiting
    client_ip = request.client.host if request.client else "unknown"
    await _check_login_rate(client_ip)

    # Validate role — non-admin users cannot self-assign admin roles
    validated_role = _validate_role(body.role)

    async with _users_lock:
        user = await _user_repo.get_by_email(body.email)

        if user is None:
            dev_mode = os.getenv("AILINE_DEV_MODE", "").lower() in ("true", "1", "yes")
            if not dev_mode:
                raise HTTPException(status_code=401, detail="Invalid credentials")

            user = UserRow(
                email=body.email,
                display_name=body.email.split("@")[0].replace(".", " ").title(),
                role=validated_role,
                locale="en",
                avatar_url="",
                accessibility_profile="",
                is_active=True,
                hashed_password=_hash_password(body.password),
            )
            await _user_repo.create(user)
            logger.info("auth.auto_created_user", user_id=user.id, role=validated_role)
        else:
            # Verify password: if user has a hashed password, require correct password
            stored_hash = user.hashed_password or ""
            if stored_hash:
                if not _verify_password(body.password, stored_hash):
                    raise HTTPException(status_code=401, detail="Invalid credentials")
            else:
                # User has no password (demo user) — only allow in dev mode.
                # In non-dev mode, passwordless accounts are NEVER accessible
                # (prevents auth bypass when demo users are seeded but dev mode is off).
                dev_mode = os.getenv("AILINE_DEV_MODE", "").lower() in ("true", "1", "yes")
                if not dev_mode:
                    raise HTTPException(status_code=401, detail="Invalid credentials")

        # Snapshot immutable fields WHILE under the lock to prevent race
        # conditions with concurrent modifications to the user row.
        snapshot_id = user.id
        snapshot_role = user.role
        snapshot_org = user.org_id
        snapshot_response = _user_response(user)

    token = _create_jwt(snapshot_id, snapshot_role, snapshot_org)

    return TokenResponse(
        access_token=token,
        user=snapshot_response,
    )


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest) -> TokenResponse:
    """Register a new user."""
    # Validate role — non-admin users cannot self-register as admin
    validated_role = _validate_role(body.role)

    async with _users_lock:
        existing = await _user_repo.get_by_email(body.email)
        if existing is not None:
            raise HTTPException(status_code=409, detail="Email already registered")

        user = UserRow(
            email=body.email,
            display_name=body.display_name,
            role=validated_role,
            org_id=body.org_id,
            locale=body.locale,
            avatar_url="",
            accessibility_profile="",
            is_active=True,
            hashed_password=_hash_password(body.password),
        )
        await _user_repo.create(user)
        logger.info("auth.registered", user_id=user.id, role=validated_role)

        # Snapshot under lock
        snapshot_response = _user_response(user)

    token = _create_jwt(user.id, validated_role, body.org_id)

    return TokenResponse(
        access_token=token,
        user=snapshot_response,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    teacher_id: str = Depends(require_authenticated),
) -> UserResponse:
    """Get the current user's profile."""
    role = get_current_user_role() or "teacher"
    org_id = get_current_org_id()

    # Find user in store by ID
    async with _users_lock:
        user = await _user_repo.get_by_id(teacher_id)
        if user is not None:
            return _user_response(user)

    # User not in store (could be from JWT/demo), return basic profile
    return UserResponse(
        id=teacher_id,
        email="",
        display_name=teacher_id,
        role=role,
        org_id=org_id,
    )


@router.get("/roles")
async def list_roles() -> dict[str, Any]:
    """List all available roles with descriptions."""
    return {
        "roles": [
            {
                "id": "super_admin",
                "name": "Super Administrator",
                "description": "Full system access, manages all organizations and users",
                "icon": "shield",
            },
            {
                "id": "school_admin",
                "name": "School Administrator",
                "description": "Manages teachers and students within an organization",
                "icon": "building",
            },
            {
                "id": "teacher",
                "name": "Teacher",
                "description": "Creates lesson plans, manages students, uses AI tools",
                "icon": "graduation-cap",
            },
            {
                "id": "student",
                "name": "Student",
                "description": "Accesses personalized learning content and tutoring",
                "icon": "book-open",
            },
            {
                "id": "parent",
                "name": "Parent / Guardian",
                "description": "Views child's progress and communicates with teachers",
                "icon": "heart",
            },
        ]
    }


# -- Demo user seeding -------------------------------------------------------


def seed_demo_users() -> None:
    """Pre-seed the in-memory user store with demo profiles.

    Called synchronously at startup before any requests are served,
    so direct dict access is safe (no concurrent async tasks yet).
    Uses InMemoryUserRepository.seed_sync() for synchronous insertion.
    """
    from ...adapters.db.user_repository import InMemoryUserRepository
    from .demo import DEMO_PROFILES

    # Only InMemoryUserRepository supports synchronous seeding
    if not isinstance(_user_repo, InMemoryUserRepository):
        logger.info("auth.seed_demo_users_skipped", reason="not in-memory repo")
        return

    for key, profile in DEMO_PROFILES.items():
        email = f"{key}@ailine-demo.edu"
        if not _user_repo.has_email(email):
            row = UserRow(
                id=profile["id"],
                email=email,
                display_name=profile["name"],
                role=profile.get("role", "teacher"),
                locale="en",
                avatar_url="",
                accessibility_profile=profile.get("accessibility", ""),
                is_active=True,
                hashed_password="",
            )
            _user_repo.seed_sync(row)
