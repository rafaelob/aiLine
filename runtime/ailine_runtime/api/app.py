"""FastAPI application factory.

Usage:
    from ailine_runtime.api import create_app
    app = create_app()
"""

from __future__ import annotations

import os
import re
import time
import typing
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response

from ..app.authz import require_authenticated
from ..shared.config import Settings, get_settings
from ..shared.container import Container
from ..shared.metrics import (
    http_request_duration,
    http_requests_total,
    render_metrics,
)
from ..shared.observability import configure_logging

_log = structlog.get_logger("ailine.api.app")

# Cached skills info — populated once on first diagnostics/capabilities request (F-241).
_skills_cache: dict[str, Any] | None = None


def _get_skills_info(settings_obj: Any) -> dict[str, Any]:
    """Return cached skills registry info (count + names).

    Scans skill directories once, then caches the result for the
    lifetime of the process. Safe for concurrent access since the
    dict is replaced atomically (GIL-protected).
    """
    global _skills_cache
    if _skills_cache is not None:
        return _skills_cache
    try:
        from ailine_agents.skills.registry import SkillRegistry

        registry = SkillRegistry()
        count = registry.scan_paths(settings_obj.skill_source_paths())
        result: dict[str, Any] = {
            "loaded": True,
            "available": True,
            "count": count,
            "names": registry.list_names(),
        }
    except Exception:
        result = {"loaded": False, "available": False, "count": 0, "names": []}
    _skills_cache = result
    return result


# Regex patterns for normalizing path parameters in metrics labels.
# Matches UUID v4/v7 (with or without hyphens) and pure numeric IDs.
_UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
_NUMERIC_RE = re.compile(r"^[0-9]+$")


def normalize_metric_path(path: str) -> str:
    """Replace dynamic path segments with ``:id`` to avoid high-cardinality labels.

    Normalizes UUID-like segments and numeric IDs so that
    ``/plans/550e8400-e29b-41d4-a716-446655440000`` becomes ``/plans/:id``
    and ``/materials/123`` becomes ``/materials/:id``.
    """
    parts = path.split("/")
    normalized: list[str] = []
    for part in parts:
        if not part:
            normalized.append(part)
        elif _UUID_RE.fullmatch(part) or _NUMERIC_RE.fullmatch(part):
            normalized.append(":id")
        else:
            normalized.append(part)
    return "/".join(normalized)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings is None:
        settings = get_settings()

    configure_logging(json_output=True)

    # Validate dev-mode safety before building the application.
    # Clear the cached dev-mode check so it re-reads the env var
    # (important when create_app is called multiple times in tests).
    from .middleware.tenant_context import _is_dev_mode, validate_dev_mode

    _is_dev_mode.cache_clear()
    validate_dev_mode(env=settings.env)

    # Initialize OpenTelemetry tracing (no-op when AILINE_OTEL_ENABLED is unset)
    from ..shared.tracing import init_tracing, instrument_fastapi

    init_tracing(service_name="ailine-runtime")

    # Validate environment early — fail fast on misconfiguration (GPT-5.2 review).
    env_warnings = settings.validate_environment()
    if env_warnings:
        for w in env_warnings:
            _log.warning("config.validation_warning", message=w)

    container = Container.build(settings)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        """Manage application lifecycle: graceful startup and shutdown."""
        _log.info("app.startup", version="0.1.0")

        # Async seeding for Postgres-backed user repo (F-230)
        if settings.demo_mode:
            from .routers.auth import is_user_repo_set, seed_demo_users_async

            if is_user_repo_set():
                try:
                    await seed_demo_users_async()
                except Exception as exc:
                    _log.warning(
                        "seed_demo_users_async_failed",
                        error=str(exc),
                        hint="Run alembic upgrade head to create the users table",
                    )

        yield
        _log.info("app.shutdown_started")
        await container.close()
        _log.info("app.shutdown_complete")

    app = FastAPI(
        title="AiLine Runtime API",
        version="0.1.0",
        description="Adaptive Inclusive Learning — Individual Needs in Education",
        lifespan=lifespan,
    )

    # Store container in app state for access in routers
    app.state.container = container
    app.state.settings = settings

    # Auto-instrument FastAPI with OpenTelemetry spans
    instrument_fastapi(app)

    # -----------------------------------------------------------------
    # Middleware stack (outermost first)
    # -----------------------------------------------------------------

    # CORS — restrict in production via AILINE_CORS_ORIGINS env var
    cors_origins = [
        o.strip()
        for o in os.getenv("AILINE_CORS_ORIGINS", "http://localhost:3000").split(",")
        if o.strip()
    ]
    if not cors_origins:
        cors_origins = ["http://localhost:3000"]
    # Reject wildcard when credentials are enabled (browsers enforce this anyway,
    # but failing early avoids confusion).
    if "*" in cors_origins:
        raise ValueError("CORS origins cannot include '*' when allow_credentials=True")
    # Only expose X-Teacher-ID header in dev mode (security hardening).
    # In production this header is rejected by the tenant middleware anyway,
    # but removing it from CORS prevents browsers from sending it at all.
    cors_headers = ["Authorization", "Content-Type", "Accept", "X-Request-ID"]
    if os.getenv("AILINE_DEV_MODE", "").lower() in ("true", "1", "yes"):
        cors_headers.append("X-Teacher-ID")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=cors_headers,
    )

    # Security headers (X-Content-Type-Options, X-Frame-Options, etc.)
    from .middleware.security_headers import SecurityHeadersMiddleware

    app.add_middleware(SecurityHeadersMiddleware)

    # Rate limiter — per-client sliding window.
    # Added BEFORE tenant context in the add_middleware chain so that
    # in Starlette's LIFO processing order, the rate limiter runs
    # AFTER tenant context on the inbound path. This allows it to
    # use teacher_id (set by tenant context) for keying.
    from .middleware.rate_limit import RateLimitMiddleware

    app.add_middleware(RateLimitMiddleware)

    # Request ID — extract from header or generate UUID4, bind to structlog
    from .middleware.request_id import RequestIDMiddleware

    app.add_middleware(RequestIDMiddleware)

    # Tenant context — extract teacher_id from JWT / X-Teacher-ID header
    from .middleware.tenant_context import TenantContextMiddleware

    app.add_middleware(TenantContextMiddleware)

    # -----------------------------------------------------------------
    # Metrics instrumentation (lightweight, no external deps)
    # -----------------------------------------------------------------

    @app.middleware("http")
    async def metrics_middleware(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Record HTTP request count and duration metrics."""
        start = time.monotonic()
        response = await call_next(request)
        duration = time.monotonic() - start
        # Normalize path to avoid high cardinality from path params.
        path = normalize_metric_path(request.url.path)
        method = request.method
        status = str(response.status_code)
        http_requests_total.inc(method=method, path=path, status=status)
        http_request_duration.observe(duration, method=method, path=path)
        return response

    # -----------------------------------------------------------------
    # Health probes
    # -----------------------------------------------------------------

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Liveness probe. Always returns OK if the process is running."""
        return {"status": "ok"}

    @app.get("/health/ready")
    async def health_ready() -> Response:
        """Readiness probe. Checks database and Redis connectivity.

        Returns 200 when all checks pass or are skipped (unconfigured),
        503 when any configured check actually fails.

        Check values:
        - ``"ok"``   -- dependency reachable.
        - ``"skip"`` -- dependency not configured (acceptable).
        - ``"error: ..."`` -- dependency configured but unreachable (failure).
        """
        checks: dict[str, str] = {}
        has_error = False

        # --- Database check ---
        checks["db"] = await _check_db(container)
        if checks["db"] not in ("ok", "skip"):
            has_error = True

        # --- Redis check ---
        checks["redis"] = await _check_redis(container)
        if checks["redis"] not in ("ok", "skip"):
            has_error = True

        status = "degraded" if has_error else "ready"
        status_code = 503 if has_error else 200

        return JSONResponse(
            content={"status": status, "checks": checks},
            status_code=status_code,
        )

    # -----------------------------------------------------------------
    # Public diagnostics (no auth — safe subset for frontend status)
    # -----------------------------------------------------------------

    @app.get("/health/diagnostics")
    async def health_diagnostics() -> Response:
        """Public system diagnostics for the frontend Status Indicator.

        Returns overall status, dependency availability (without latency),
        version, environment, uptime, and skill count. Sensitive operational
        details (latency, model config, API keys, memory) are only available
        at ``/internal/diagnostics`` (authenticated).
        """
        import time as _time

        app_start_time = getattr(app.state, "_start_time", None)
        if app_start_time is None:
            app.state._start_time = _time.monotonic()  # type: ignore[attr-defined]
            app_start_time = app.state._start_time

        # Dependency status (no latency — that is internal)
        db_check = await _check_db(container)
        redis_check = await _check_redis(container)

        deps_status = {
            "db": {"status": db_check},
            "redis": {"status": redis_check},
        }

        all_ok = all(d["status"] in ("ok", "skip") for d in deps_status.values())

        skills_info = _get_skills_info(settings)

        diagnostics: dict[str, Any] = {
            "status": "healthy" if all_ok else "degraded",
            "dependencies": deps_status,
            "skills": {"available": skills_info["available"], "count": skills_info["count"]},
            "uptime_seconds": round(_time.monotonic() - app_start_time, 1),
            "environment": settings.env,
            "version": app.version,
        }
        return JSONResponse(content=diagnostics, status_code=200 if all_ok else 503)

    # -----------------------------------------------------------------
    # Private diagnostics (authenticated — full operational details)
    # -----------------------------------------------------------------

    @app.get("/internal/diagnostics")
    async def internal_diagnostics(
        _teacher_id: str = Depends(require_authenticated),
    ) -> Response:
        """Authenticated diagnostics with full operational data.

        Includes dependency latency, LLM model config, API key presence,
        skill names, and process memory. Requires valid JWT.
        """
        import os
        import time as _time

        diagnostics: dict[str, Any] = {}
        app_start_time = getattr(app.state, "_start_time", None)
        if app_start_time is None:
            app.state._start_time = _time.monotonic()  # type: ignore[attr-defined]
            app_start_time = app.state._start_time

        # -- Dependencies with latency --
        deps_status: dict[str, Any] = {}

        db_start = _time.monotonic()
        db_check = await _check_db(container)
        db_latency_ms = round((_time.monotonic() - db_start) * 1000, 1)
        deps_status["db"] = {"status": db_check, "latency_ms": db_latency_ms}

        redis_start = _time.monotonic()
        redis_check = await _check_redis(container)
        redis_latency_ms = round((_time.monotonic() - redis_start) * 1000, 1)
        deps_status["redis"] = {"status": redis_check, "latency_ms": redis_latency_ms}

        diagnostics["dependencies"] = deps_status

        # -- LLM models configured --
        diagnostics["llm"] = {
            "provider": settings.llm.provider,
            "model": settings.llm.model,
            "planner_model": settings.planner_model,
            "executor_model": settings.executor_model,
            "qg_model": settings.qg_model,
            "tutor_model": settings.tutor_model,
        }

        # -- API key presence (never expose actual keys) --
        diagnostics["api_keys"] = {
            "anthropic": bool(settings.anthropic_api_key),
            "openai": bool(settings.openai_api_key),
            "google": bool(settings.google_api_key),
            "openrouter": bool(settings.openrouter_api_key),
            "elevenlabs": bool(settings.elevenlabs_api_key),
        }

        # -- Skills (cached — F-241) --
        skills_info = _get_skills_info(settings)
        diagnostics["skills"] = {
            "loaded": skills_info["loaded"],
            "count": skills_info["count"],
            "names": skills_info["names"],
        }

        # -- Memory usage (stdlib only, no psutil dependency) --
        import sys

        mem: dict[str, Any] = {"pid": os.getpid()}
        try:
            if sys.platform == "win32":
                import ctypes
                import ctypes.wintypes

                class ProcessMemoryCounters(ctypes.Structure):
                    _fields_: typing.ClassVar[list[tuple[str, type]]] = [
                        ("cb", ctypes.wintypes.DWORD),
                        ("PageFaultCount", ctypes.wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t),
                    ]

                counters = ProcessMemoryCounters()
                counters.cb = ctypes.sizeof(counters)
                handle = ctypes.windll.kernel32.GetCurrentProcess()  # type: ignore[union-attr]
                ctypes.windll.psapi.GetProcessMemoryInfo(  # type: ignore[union-attr]
                    handle,
                    ctypes.byref(counters),
                    counters.cb,
                )
                mem["rss_mb"] = round(counters.WorkingSetSize / (1024 * 1024), 1)
            else:
                import resource

                usage = resource.getrusage(resource.RUSAGE_SELF)
                divisor = 1024 if sys.platform == "linux" else 1
                mem["rss_mb"] = round(usage.ru_maxrss / divisor / 1024, 1)
        except Exception:
            mem["rss_mb"] = -1
        diagnostics["memory"] = mem

        # -- Uptime --
        diagnostics["uptime_seconds"] = round(_time.monotonic() - app_start_time, 1)

        # -- Environment --
        diagnostics["environment"] = settings.env
        diagnostics["version"] = app.version

        # -- Overall status --
        all_ok = all(d.get("status") in ("ok", "skip") for d in deps_status.values())
        diagnostics["status"] = "healthy" if all_ok else "degraded"

        return JSONResponse(content=diagnostics, status_code=200 if all_ok else 503)

    # -----------------------------------------------------------------
    # Capabilities endpoint — dynamic feature discovery
    # -----------------------------------------------------------------

    @app.get("/capabilities")
    async def capabilities() -> dict[str, Any]:
        """Public endpoint listing currently available platform features.

        Returns which adapters and services are wired and operational.
        Useful for progressive enhancement in the frontend — e.g., only
        show TTS button if TTS is configured, sign language if available.
        """
        caps: dict[str, Any] = {
            "version": app.version,
            "personas": 9,
            "sign_languages": 8,
        }

        # LLM availability
        caps["llm"] = {
            "available": bool(
                settings.anthropic_api_key
                or settings.openai_api_key
                or settings.google_api_key
                or settings.openrouter_api_key
            ),
            "provider": settings.llm.provider,
        }

        # TTS (ElevenLabs)
        caps["tts"] = {"available": bool(settings.elevenlabs_api_key)}

        # Image generation (Gemini Imagen)
        caps["image_generation"] = {"available": bool(settings.google_api_key)}

        # Vector search (pgvector)
        caps["vector_search"] = {"available": container.vectorstore is not None}

        # Braille translation
        caps["braille"] = {"available": True, "grades": [1], "languages": ["en", "pt-BR", "es"]}

        # Skills (cached — F-241)
        skills_info = _get_skills_info(settings)
        caps["skills"] = {"available": skills_info["available"], "count": skills_info["count"]}

        # Demo mode
        caps["demo_mode"] = settings.demo_mode

        return caps

    # -----------------------------------------------------------------
    # Metrics endpoint (Prometheus text format)
    # -----------------------------------------------------------------

    @app.get("/metrics", include_in_schema=False)
    async def metrics_endpoint(
        _teacher_id: str = Depends(require_authenticated),
    ) -> PlainTextResponse:
        """Expose in-process metrics in Prometheus text exposition format.

        Requires authentication to prevent unauthenticated access to
        operational data (request counts, latency distributions, etc.).
        """
        return PlainTextResponse(
            content=render_metrics(),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    # -----------------------------------------------------------------
    # RFC 7807 error handlers
    # -----------------------------------------------------------------
    from .middleware.error_handler import install_error_handlers

    install_error_handlers(app)

    # -----------------------------------------------------------------
    # Demo mode middleware
    # -----------------------------------------------------------------
    if settings.demo_mode:
        from .middleware.demo_mode import DemoModeMiddleware

        app.add_middleware(DemoModeMiddleware)

    # -----------------------------------------------------------------
    # Register routers
    # -----------------------------------------------------------------
    from .routers import (
        auth,
        curriculum,
        demo,
        materials,
        media,
        observability,
        plans,
        plans_stream,
        progress,
        rag_diagnostics,
        runs,
        setup,
        sign_language,
        skills,
        skills_v1,
        traces,
        tts,
        tutors,
    )

    # Auth and setup (no tenant context required, must be registered first)
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(setup.router, prefix="/setup", tags=["setup"])

    app.include_router(materials.router, prefix="/materials", tags=["materials"])
    app.include_router(plans.router, prefix="/plans", tags=["plans"])
    app.include_router(plans_stream.router, prefix="/plans", tags=["plans-stream"])
    app.include_router(tutors.router, prefix="/tutors", tags=["tutors"])
    app.include_router(curriculum.router, prefix="/curriculum", tags=["curriculum"])
    app.include_router(media.router, prefix="/media", tags=["media"])
    app.include_router(
        sign_language.router, prefix="/sign-language", tags=["sign-language"]
    )
    app.include_router(demo.router, prefix="/demo", tags=["demo"])
    app.include_router(traces.router, prefix="/traces", tags=["traces"])
    app.include_router(runs.router, prefix="/runs", tags=["runs"])
    app.include_router(rag_diagnostics.router, prefix="/rag", tags=["rag-diagnostics"])
    app.include_router(
        observability.router, prefix="/observability", tags=["observability"]
    )
    app.include_router(progress.router, prefix="/progress", tags=["progress"])
    app.include_router(skills.router, prefix="/skills", tags=["skills"])
    app.include_router(
        skills_v1.router, prefix="/v1/skills", tags=["skills-v1"]
    )
    app.include_router(tts.router, prefix="/v1/tts", tags=["tts"])

    # Wire SkillRepository for skills_v1 router (F-176).
    # Reuse the session factory from the vectorstore engine (same PG instance).
    _wire_skill_repo(container, skills_v1)

    # Wire UserRepository for auth router (F-230).
    _wire_user_repo(container, auth, db_url=settings.db.url if settings.db else "")

    # Pre-seed auth store with demo profiles when demo mode is active
    if settings.demo_mode:
        from .routers.auth import seed_demo_users

        seed_demo_users()

    return app


# ---------------------------------------------------------------------------
# Readiness check helpers
# ---------------------------------------------------------------------------


async def _check_db(container: Container) -> str:
    """Probe database connectivity via a simple ``SELECT 1``.

    Returns ``"ok"`` on success, ``"skip"`` when no vectorstore is configured
    (e.g. SQLite dev), or a short error description on failure.
    """
    vs = container.vectorstore
    if vs is None:
        return "skip"

    # The PgVectorStore exposes a session_factory we can use.
    session_factory = getattr(vs, "_session_factory", None)
    if session_factory is None:
        return "skip"

    try:
        from sqlalchemy import text

        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:
        _log.warning("readiness_db_check_failed", error=str(exc))
        return f"error: {type(exc).__name__}"


async def _check_redis(container: Container) -> str:
    """Probe Redis connectivity via ``PING``.

    Returns ``"ok"`` on success, ``"skip"`` when using in-memory event bus,
    or a short error description on failure.
    """
    event_bus = container.event_bus
    if event_bus is None:
        return "skip"

    # Only probe if the bus is a RedisEventBus (has _redis attribute).
    redis_client = getattr(event_bus, "_redis", None)
    if redis_client is None:
        return "skip"

    try:
        result = await redis_client.ping()
        return "ok" if result else "error: ping returned false"
    except Exception as exc:
        _log.warning("readiness_redis_check_failed", error=str(exc))
        return f"error: {type(exc).__name__}"


def _wire_skill_repo(container: Container, skills_v1_module: Any) -> None:
    """Inject a SkillRepository into the skills_v1 router.

    When a PostgreSQL-backed vectorstore is available, reuses its session
    factory to create a ``SessionFactorySkillRepository``. Otherwise, falls
    back to ``FakeSkillRepository`` for dev/test environments.

    Skips wiring if a repo has already been injected (e.g., by test fixtures
    calling ``set_skill_repo()`` before ``create_app()``).
    """
    # Respect pre-existing repo (test fixtures set it before create_app)
    if skills_v1_module.is_skill_repo_set():
        _log.info("skill_repo.wired", backend="pre_existing")
        return

    from ..domain.ports.skills import SkillRepository

    vs = container.vectorstore
    session_factory = getattr(vs, "_session_factory", None) if vs else None

    repo: SkillRepository
    if session_factory is not None:
        from ..adapters.db.skill_repository import SessionFactorySkillRepository

        repo = SessionFactorySkillRepository(session_factory)
        _log.info("skill_repo.wired", backend="postgres")
    else:
        from ..adapters.db.fake_skill_repository import FakeSkillRepository

        repo = FakeSkillRepository()
        _log.info("skill_repo.wired", backend="fake_in_memory")

    skills_v1_module.set_skill_repo(repo)


def _wire_user_repo(
    container: Container, auth_module: Any, *, db_url: str = ""
) -> None:
    """Inject a UserRepository into the auth router (F-230).

    Only wires a PostgreSQL-backed repository when the database URL is
    actually PostgreSQL. For SQLite/test environments, keeps the default
    ``InMemoryUserRepository`` to avoid migration-dependent table lookups.

    Skips wiring if a repo has already been injected (e.g., by test fixtures).
    """
    if auth_module.is_user_repo_set():
        _log.info("user_repo.wired", backend="pre_existing")
        return

    # Only use Postgres repo when the DB is actually PostgreSQL
    if "postgresql" not in db_url:
        _log.info("user_repo.wired", backend="in_memory_default")
        return

    vs = container.vectorstore
    session_factory = getattr(vs, "_session_factory", None) if vs else None

    if session_factory is not None:
        from ..adapters.db.user_repository import SessionFactoryUserRepository

        repo = SessionFactoryUserRepository(session_factory)
        auth_module.set_user_repo(repo)
        _log.info("user_repo.wired", backend="postgres")
    else:
        _log.info("user_repo.wired", backend="in_memory_default")
