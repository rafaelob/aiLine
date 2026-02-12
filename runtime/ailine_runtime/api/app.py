"""FastAPI application factory.

Usage:
    from ailine_runtime.api import create_app
    app = create_app()
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..shared.config import Settings, get_settings
from ..shared.container import Container
from ..shared.observability import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings is None:
        settings = get_settings()

    configure_logging(json_output=True)

    container = Container.build(settings)

    app = FastAPI(
        title="AiLine Runtime API",
        version="0.1.0",
        description="Adaptive Inclusive Learning — Individual Needs in Education",
    )

    # Store container in app state for access in routers
    app.state.container = container
    app.state.settings = settings

    # CORS — restrict in production via AILINE_CORS_ORIGINS env var
    import os

    cors_origins = os.getenv("AILINE_CORS_ORIGINS", "http://localhost:3000").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    # Demo mode middleware -- intercepts /plans/generate when demo_mode=true
    if settings.demo_mode:
        from .middleware.demo_mode import DemoModeMiddleware

        app.add_middleware(DemoModeMiddleware)

    # Register routers
    from .routers import (
        curriculum,
        demo,
        materials,
        media,
        plans,
        plans_stream,
        sign_language,
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

    return app
