"""FastAPI application factory.

Usage:
    from ailine_runtime.api import create_app
    app = create_app()
"""

from __future__ import annotations

import os
import re
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response

from ..shared.config import Settings, get_settings
from ..shared.container import Container
from ..shared.metrics import (
    http_request_duration,
    http_requests_total,
    render_metrics,
)
from ..shared.observability import configure_logging

_log = structlog.get_logger("ailine.api.app")

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
        elif _UUID_RE.fullmatch(part) or _NUMERIC_RE.match(part):
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
    from .middleware.tenant_context import validate_dev_mode

    validate_dev_mode(env=settings.env)

    # Initialize OpenTelemetry tracing (no-op when AILINE_OTEL_ENABLED is unset)
    from ..shared.tracing import init_tracing, instrument_fastapi

    init_tracing(service_name="ailine-runtime")

    container = Container.build(settings)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        """Manage application lifecycle: graceful startup and shutdown."""
        _log.info("app.startup", version="0.1.0")
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
        allow_methods=["GET", "POST", "OPTIONS"],
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
    async def metrics_middleware(request: Request, call_next: RequestResponseEndpoint) -> Response:
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
    # Metrics endpoint (Prometheus text format)
    # -----------------------------------------------------------------

    @app.get("/metrics", include_in_schema=False)
    async def metrics_endpoint() -> PlainTextResponse:
        """Expose in-process metrics in Prometheus text exposition format."""
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
        curriculum,
        demo,
        materials,
        media,
        observability,
        plans,
        plans_stream,
        rag_diagnostics,
        sign_language,
        traces,
        tutors,
    )

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
    app.include_router(
        rag_diagnostics.router, prefix="/rag", tags=["rag-diagnostics"]
    )
    app.include_router(
        observability.router, prefix="/observability", tags=["observability"]
    )

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
