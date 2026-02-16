"""Demo mode middleware -- intercepts plan generation when AILINE_DEMO_MODE=true.

When demo mode is active, requests to POST /plans/generate or
POST /plans/generate/stream that include a ``demo_scenario_id`` field
are intercepted and served from cached scenario data instead of
invoking the real LLM pipeline.

Requests without ``demo_scenario_id`` or to other endpoints pass through
normally, so the middleware is transparent to non-demo traffic.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ...app.services.demo import DemoService

logger = structlog.get_logger("ailine.middleware.demo_mode")

# Paths that can be intercepted in demo mode.
_INTERCEPTABLE_PATHS = {
    "/plans/generate",
}


class DemoModeMiddleware(BaseHTTPMiddleware):
    """Intercept plan generation requests when demo mode is active.

    Activation requires **both**:
    1. ``AILINE_DEMO_MODE=true`` in settings (checked via ``app.state.settings``)
    2. The request body contains a ``demo_scenario_id`` field

    If both conditions are met, the middleware returns the cached plan
    directly, bypassing the full pipeline. For the streaming endpoint,
    the caller should use the ``/demo/scenarios/{id}/stream`` endpoint
    directly; this middleware only handles the synchronous generate path.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Only intercept POST to known paths
        if request.method != "POST" or request.url.path not in _INTERCEPTABLE_PATHS:
            return await call_next(request)

        # Check if demo mode is enabled in settings
        settings = getattr(request.app.state, "settings", None)
        if settings is None or not getattr(settings, "demo_mode", False):
            return await call_next(request)

        # Parse body to look for demo_scenario_id
        try:
            body_bytes = await request.body()
            body = json.loads(body_bytes)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return await call_next(request)

        scenario_id = body.get("demo_scenario_id")
        if not scenario_id:
            # No demo scenario requested -- pass through to real pipeline
            return await call_next(request)

        # Serve from cached scenario
        svc = _get_or_create_demo_service(request)
        cached_plan = svc.get_cached_plan(scenario_id)
        if cached_plan is None:
            logger.warning("demo_scenario_not_found", scenario_id=scenario_id)
            return JSONResponse(
                status_code=404,
                content={"detail": f"Demo scenario '{scenario_id}' not found."},
            )

        score = svc.get_score(scenario_id)
        prompt = svc.get_prompt(scenario_id)
        run_id = body.get("run_id", f"demo-{scenario_id}")

        logger.info(
            "demo_mode_intercept",
            path=request.url.path,
            scenario_id=scenario_id,
            run_id=run_id,
        )

        return JSONResponse(
            content={
                "run_id": run_id,
                "status": "completed",
                "prompt": prompt,
                "plan": cached_plan,
                "score": score,
                "demo_mode": True,
                "ts": datetime.now(UTC).isoformat(),
            }
        )


def _get_or_create_demo_service(request: Request) -> DemoService:
    """Retrieve or create the DemoService singleton on app state."""
    if not hasattr(request.app.state, "demo_service"):
        request.app.state.demo_service = DemoService()
    svc: DemoService = request.app.state.demo_service
    return svc
