"""Pipeline run domain entities.

Pure Pydantic models for tracking pipeline execution state and events.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .plan import RunStage


class RunEvent(BaseModel):
    """A single event emitted during a pipeline run."""

    event_id: str
    run_id: str
    stage: RunStage
    event_type: str  # start, progress, complete, error
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: str


class PipelineRun(BaseModel):
    """Tracks the full lifecycle of a plan generation pipeline run."""

    run_id: str
    plan_id: str | None = None
    trigger: str = "api"
    input_data: dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"
    started_at: str | None = None
    completed_at: str | None = None
    events: list[RunEvent] = Field(default_factory=list)
