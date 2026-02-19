"""Demo mode API router -- thin routing layer.

Profile definitions live in demo_profiles.py; seed logic in demo_seed.py.
This file contains only the FastAPI route definitions and guards.
"""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from ...app.services.demo import DemoService
from .demo_profiles import DEMO_PROFILES
from .demo_seed import seed_demo_data_for_teacher

logger = structlog.get_logger("ailine.api.demo")

router = APIRouter()


def _require_demo_mode(request: Request, *, require_token: bool = False) -> None:
    """Raise 403 if demo mode is not enabled."""
    settings = getattr(request.app.state, "settings", None)
    if settings is not None and getattr(settings, "demo_mode", False):
        pass
    else:
        demo_env = os.getenv("AILINE_DEMO_MODE", "").strip()
        if demo_env not in ("1", "true", "yes"):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Demo mode is not enabled. Set AILINE_DEMO_MODE=1 "
                    "in the environment to use demo endpoints."
                ),
            )

    if require_token:
        expected_token = os.getenv("AILINE_DEMO_TOKEN", "").strip()
        if expected_token:
            provided = request.headers.get("X-Demo-Token", "").strip()
            if provided != expected_token:
                raise HTTPException(
                    status_code=403,
                    detail="Invalid or missing X-Demo-Token header.",
                )


def _get_demo_service(request: Request) -> DemoService:
    """Retrieve or create the DemoService singleton from app state."""
    if not hasattr(request.app.state, "demo_service"):
        request.app.state.demo_service = DemoService()
    svc: DemoService = request.app.state.demo_service
    return svc


# ---------------------------------------------------------------------------
# Profiles & Seed Data endpoints
# ---------------------------------------------------------------------------


@router.get("/profiles")
async def get_demo_profiles() -> dict[str, Any]:
    """Return all pre-configured demo profiles for hackathon judges."""
    profiles = []
    for key, profile in DEMO_PROFILES.items():
        profiles.append({**profile, "demo_key": key})
    return {"profiles": profiles, "mode": "hackathon_demo"}


@router.post("/seed")
async def seed_demo_data(request: Request) -> dict[str, Any]:
    """Populate stores with sample data for the demo teacher profile.

    Requires AILINE_DEMO_MODE=1. Idempotent.
    """
    _require_demo_mode(request, require_token=True)
    return seed_demo_data_for_teacher()


# ---------------------------------------------------------------------------
# Scenario endpoints
# ---------------------------------------------------------------------------


@router.get("/scenarios")
async def list_scenarios(request: Request) -> list[dict[str, Any]]:
    """List all available demo scenarios with summary info."""
    svc = _get_demo_service(request)
    return svc.list_scenarios()


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str, request: Request) -> dict[str, Any]:
    """Get a specific demo scenario with its full cached plan."""
    svc = _get_demo_service(request)
    scenario = svc.get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(
            status_code=404, detail=f"Scenario '{scenario_id}' not found."
        )
    return scenario


@router.post("/reset")
async def reset_demo(request: Request) -> dict[str, str]:
    """Clear and reload demo session state."""
    _require_demo_mode(request, require_token=True)
    svc = _get_demo_service(request)
    svc.reset()
    return {"status": "ok", "message": "Demo state reset."}


@router.post("/scenarios/{scenario_id}/run")
async def run_demo_scenario(scenario_id: str, request: Request) -> dict[str, Any]:
    """Run a demo scenario, returning the cached plan immediately."""
    _require_demo_mode(request)
    return await _execute_scenario(scenario_id, request)


@router.post("/scenarios/{scenario_id}/execute")
async def execute_demo_scenario(scenario_id: str, request: Request) -> dict[str, Any]:
    """Execute a demo scenario (alias for /run)."""
    _require_demo_mode(request)
    return await _execute_scenario(scenario_id, request)


async def _execute_scenario(scenario_id: str, request: Request) -> dict[str, Any]:
    """Shared implementation for run/execute endpoints."""
    svc = _get_demo_service(request)
    cached_plan = svc.get_cached_plan(scenario_id)
    if cached_plan is None:
        raise HTTPException(
            status_code=404, detail=f"Scenario '{scenario_id}' not found."
        )

    score = svc.get_score(scenario_id)
    prompt = svc.get_prompt(scenario_id)

    return {
        "run_id": f"demo-{scenario_id}",
        "status": "completed",
        "prompt": prompt,
        "plan": cached_plan,
        "score": score,
        "demo_mode": True,
    }


@router.post("/scenarios/{scenario_id}/stream")
async def stream_demo_scenario(
    scenario_id: str, request: Request
) -> EventSourceResponse:
    """Stream a demo scenario with simulated delays."""
    svc = _get_demo_service(request)
    scenario = svc.get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(
            status_code=404, detail=f"Scenario '{scenario_id}' not found."
        )

    cached_events = svc.get_cached_events(scenario_id)
    cached_plan = svc.get_cached_plan(scenario_id)
    score = svc.get_score(scenario_id)
    run_id = f"demo-{scenario_id}"

    async def event_generator() -> AsyncIterator[dict[str, str]]:
        prev_delay = 0

        for seq, event_def in enumerate(cached_events, start=1):
            if await request.is_disconnected():
                logger.info("demo_stream_client_disconnected", run_id=run_id)
                break

            delay_ms = event_def.get("delay_ms", 0)
            wait_ms = max(0, delay_ms - prev_delay)
            if wait_ms > 0:
                await asyncio.sleep(wait_ms / 1000.0)
            prev_delay = delay_ms
            payload = event_def.get("payload", {})

            if event_def["type"] == "run_complete" and cached_plan is not None:
                payload = {
                    **payload,
                    "plan_id": run_id,
                    "plan": cached_plan,
                    "score": score,
                    "demo_mode": True,
                }

            sse_data = json.dumps(
                {
                    "run_id": run_id,
                    "seq": seq,
                    "ts": datetime.now(UTC).isoformat(),
                    "type": event_def["type"],
                    "stage": event_def.get("stage", "unknown"),
                    "payload": payload,
                },
                ensure_ascii=False,
            )

            yield {"data": sse_data}

    return EventSourceResponse(event_generator())
