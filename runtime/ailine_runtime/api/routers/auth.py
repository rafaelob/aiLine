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
import uuid
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


# -- DI wiring helpers -------------------------------------------------------


def set_user_repo(repo: UserRepository) -> None:
    """Inject a user repository (called from app.py at startup)."""
    global _user_repo
    _user_repo = repo
    logger.info("auth.user_repo_set", backend=type(repo).__name__)


def is_user_repo_set() -> bool:
    """True if a non-default repo was already injected (e.g., by test fixtures)."""
    return not isinstance(_user_repo, InMemoryUserRepository)


# -- Request/Response schemas ------------------------------------------------

# Lightweight email format check (RFC 5321 simplified).
# Rejects obviously malformed addresses without pulling in email-validator.
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


_ALLOWED_SELF_ASSIGN_ROLES = frozenset({
    UserRole.TEACHER, UserRole.STUDENT, UserRole.PARENT,
})


def _validate_role(role: str, *, allow_admin: bool = False) -> UserRole:
    """Validate and normalize a role string against UserRole enum.

    F-261: raises HTTPException 422 for completely unknown role values.
    Admin roles (super_admin, school_admin) are silently downgraded to
    'teacher' for security (non-admin cannot self-assign).
    """
    try:
        validated = UserRole(role)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid role: '{role}'. Valid roles: {', '.join(r.value for r in UserRole)}",
        ) from None
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


# -- User store (InMemoryUserRepository default; replaced via set_user_repo)

_user_repo: UserRepository = InMemoryUserRepository()

# Dedicated login rate limiter: per-IP, 20 attempts per minute (F-249).
_login_attempts: dict[str, list[float]] = {}
_login_rate_lock = asyncio.Lock()
_LOGIN_MAX_ATTEMPTS = 20
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


def _create_jwt(
    user_id: str,
    role: str,
    org_id: str | None = None,
    ttl_override: int | None = None,
) -> str:
    """Create a signed JWT with jti claim.

    Algorithm selection (F-231):
    - RS256 when AILINE_JWT_PRIVATE_KEY is set (production path)
    - HS256 when only AILINE_JWT_SECRET is set
    - HS256 with dev fallback secret in dev mode

    TTL: Uses ``ttl_override`` if given, else ``AILINE_JWT_ACCESS_TTL_SECONDS``
    env var, else 86400s (24h) in dev mode / 900s (15 min) otherwise.
    """
    import jwt as pyjwt

    dev_mode = os.getenv("AILINE_DEV_MODE", "").lower() in ("true", "1", "yes")
    private_key = os.getenv("AILINE_JWT_PRIVATE_KEY", "").strip()
    secret = os.getenv("AILINE_JWT_SECRET", "")

    # Select algorithm and signing key
    if private_key:
        algorithm = "RS256"
        signing_key = private_key
    elif secret:
        algorithm = "HS256"
        signing_key = secret
    elif dev_mode:
        from ...shared.jwt_dev_secret import DEV_JWT_SECRET

        algorithm = "HS256"
        signing_key = DEV_JWT_SECRET
    else:
        raise RuntimeError(
            "JWT key material must be set in non-dev mode. "
            "Set AILINE_JWT_PRIVATE_KEY (RS256) or AILINE_JWT_SECRET (HS256)."
        )

    # TTL: explicit override > env var > dev default (24h) / prod default (15 min)
    if ttl_override is not None:
        ttl = ttl_override
    else:
        env_ttl = os.getenv("AILINE_JWT_ACCESS_TTL_SECONDS", "").strip()
        ttl = int(env_ttl) if env_ttl else 86400 if dev_mode else 900

    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "jti": str(uuid.uuid4()),
        "exp": now + ttl,
        "iat": now,
    }
    if org_id:
        payload["org_id"] = org_id

    # Include iss/aud claims when configured
    issuer = os.getenv("AILINE_JWT_ISSUER", "").strip()
    audience = os.getenv("AILINE_JWT_AUDIENCE", "").strip()
    if issuer:
        payload["iss"] = issuer
    if audience:
        payload["aud"] = audience

    return pyjwt.encode(payload, signing_key, algorithm=algorithm)


async def _check_login_rate(client_ip: str) -> None:
    """Enforce per-IP login rate limit (20 attempts/minute).

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
    Includes per-IP rate limiting (20 attempts/minute) to mitigate brute force.
    """
    # Per-IP login rate limiting
    client_ip = request.client.host if request.client else "unknown"
    await _check_login_rate(client_ip)

    # Validate role — non-admin users cannot self-assign admin roles
    validated_role = _validate_role(body.role)

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

    token = _create_jwt(user.id, user.role, user.org_id)

    return TokenResponse(
        access_token=token,
        user=_user_response(user),
    )


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest) -> TokenResponse:
    """Register a new user."""
    # Validate role — non-admin users cannot self-register as admin
    validated_role = _validate_role(body.role)

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

    token = _create_jwt(user.id, validated_role, body.org_id)

    return TokenResponse(
        access_token=token,
        user=_user_response(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    teacher_id: str = Depends(require_authenticated),
) -> UserResponse:
    """Get the current user's profile."""
    role = get_current_user_role() or "teacher"
    org_id = get_current_org_id()

    # Find user in store by ID
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


@router.post("/logout")
async def logout(
    request: Request,
    teacher_id: str = Depends(require_authenticated),
) -> dict[str, str]:
    """Invalidate the current JWT by blacklisting its jti in Redis.

    The jti (JWT ID) is added to a Redis SET with a TTL matching the
    token's remaining lifetime. Subsequent requests with the same jti
    are rejected by the middleware (F-231).

    Falls back to a no-op acknowledgement when Redis is unavailable
    (in-memory dev mode).
    """
    import jwt as pyjwt

    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return {"status": "ok"}

    raw_token = auth_header[7:]
    try:
        # Decode without verification just to read jti + exp
        unverified = pyjwt.decode(raw_token, options={"verify_signature": False})
        jti = unverified.get("jti")
        exp = unverified.get("exp", 0)
    except Exception:
        return {"status": "ok"}

    if not jti:
        return {"status": "ok"}

    # Blacklist in Redis with TTL = remaining token lifetime
    remaining = max(int(exp) - int(time.time()), 1)
    redis_client = await _get_redis_client(request)
    if redis_client is not None:
        try:
            await redis_client.setex(f"jti_blacklist:{jti}", remaining, "1")
            logger.info("auth.logout", teacher_id=teacher_id, jti=jti)
        except Exception as exc:
            logger.warning("auth.logout_redis_failed", error=str(exc))

    return {"status": "ok"}


async def _get_redis_client(request: Request) -> Any:
    """Extract the Redis client from the app container via public protocol.

    F-258: Uses ``EventBus.get_redis_client()`` instead of accessing
    the private ``_redis`` attribute directly.
    """
    container = getattr(request.app.state, "container", None)
    if container is None:
        return None
    event_bus = getattr(container, "event_bus", None)
    if event_bus is None:
        return None
    return await event_bus.get_redis_client()


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


# -- Demo login endpoint -----------------------------------------------------


class DemoLoginRequest(BaseModel):
    """Demo login request — accepts a demo profile key."""

    demo_key: str = Field(..., max_length=100, description="Demo profile key")


# Short-key aliases used by the login page (login-data.ts).
# Maps to the canonical long keys in demo_profiles.py.
_SHORT_TO_LONG_KEY: dict[str, str] = {
    "teacher": "teacher-ms-johnson",
    "student-asd": "student-alex-tea",
    "student-adhd": "student-maya-adhd",
    "student-dyslexia": "student-lucas-dyslexia",
    "student-hearing": "student-sofia-hearing",
    "parent": "parent-david",
}


@router.post("/demo-login", response_model=TokenResponse)
async def demo_login(body: DemoLoginRequest, request: Request) -> TokenResponse:
    """Authenticate via a demo profile key and return a JWT.

    Looks up the profile in DEMO_PROFILES, finds or creates the matching
    user, and returns a JWT with the correct role/org_id.  Accepts both
    long keys (``teacher-ms-johnson``) and short aliases (``teacher``).
    """
    # F-255: Rate-limit demo login the same as normal login
    client_ip = request.client.host if request.client else "unknown"
    await _check_login_rate(client_ip)

    from .demo_profiles import DEMO_PROFILES

    # Resolve short aliases to canonical long keys
    canonical_key = _SHORT_TO_LONG_KEY.get(body.demo_key, body.demo_key)
    profile = DEMO_PROFILES.get(canonical_key)
    if profile is None:
        raise HTTPException(status_code=404, detail="Unknown demo profile key")

    email = f"{canonical_key}@ailine-demo.edu"
    raw_role = profile.get("role", "teacher")
    # F-251: Enforce role validation -- demo profiles are capped to
    # teacher/student/parent.  Admin roles cannot be minted via demo login.
    role = _validate_role(raw_role)

    user = await _user_repo.get_by_email(email)
    if user is None:
        # Auto-create if not yet seeded
        user = UserRow(
            id=profile["id"],
            email=email,
            display_name=profile["name"],
            role=role,
            locale="en",
            avatar_url="",
            accessibility_profile=profile.get("accessibility", ""),
            is_active=True,
            hashed_password=_hash_password("demo123"),
        )
        await _user_repo.create(user)
        logger.info("auth.demo_login_created_user", demo_key=canonical_key)

    token = _create_jwt(user.id, user.role, user.org_id)
    logger.info("auth.demo_login", demo_key=canonical_key, user_id=user.id)

    return TokenResponse(
        access_token=token,
        user=_user_response(user),
    )


# -- Demo user seeding -------------------------------------------------------


def seed_demo_users() -> None:
    """Pre-seed the user store with demo profiles (InMemory path).

    Called synchronously at startup before any requests are served.
    Only works with InMemoryUserRepository. For PostgresUserRepository,
    use ``seed_demo_users_async()`` instead (called from a lifespan hook).
    """
    from ...adapters.db.user_repository import InMemoryUserRepository
    from .demo_profiles import DEMO_PROFILES

    if not isinstance(_user_repo, InMemoryUserRepository):
        logger.info("auth.seed_demo_users_skipped", reason="not in-memory repo")
        return

    demo_pw_hash = _hash_password("demo123")
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
                hashed_password=demo_pw_hash,
            )
            _user_repo.seed_sync(row)


async def seed_demo_users_async() -> None:
    """Pre-seed demo users via async repository (Postgres path).

    Safe for concurrent calls — uses get_by_email + create with the
    DB UNIQUE constraint on email as the ultimate guard.
    """
    from .demo_profiles import DEMO_PROFILES

    demo_pw_hash = _hash_password("demo123")
    seeded = 0
    for key, profile in DEMO_PROFILES.items():
        email = f"{key}@ailine-demo.edu"
        existing = await _user_repo.get_by_email(email)
        if existing is None:
            row = UserRow(
                id=profile["id"],
                email=email,
                display_name=profile["name"],
                role=profile.get("role", "teacher"),
                locale="en",
                avatar_url="",
                accessibility_profile=profile.get("accessibility", ""),
                is_active=True,
                hashed_password=demo_pw_hash,
            )
            await _user_repo.create(row)
            seeded += 1
    logger.info("auth.seed_demo_users_async", seeded=seeded)
