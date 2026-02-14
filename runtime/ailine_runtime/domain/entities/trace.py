"""Agent trace domain entities for pipeline observability.

Captures per-node execution data in the LangGraph workflow:
inputs/outputs summary, timing, tool calls, quality scores.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RouteRationale(BaseModel):
    """SmartRouter routing explanation for a single model selection."""

    task_type: str = Field("", description="Task type that triggered routing (e.g. planner, executor)")
    weighted_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Per-dimension weighted scores: token, structured, tool, history, intent",
    )
    composite_score: float = Field(0.0, description="Final composite score [0,1]")
    tier: str = Field("", description="Selected tier: cheap, middle, primary")
    model_selected: str = Field("", description="Final model ID used")
    reason: str = Field("", description="Human-readable routing explanation")


class NodeTrace(BaseModel):
    """Execution trace for a single LangGraph node."""

    node: str = Field(..., description="Node name (e.g. planner, validate, executor)")
    status: str = Field("success", description="success | failed | skipped")
    time_ms: float = Field(0.0, description="Wall-clock execution time in ms")
    inputs_summary: dict[str, Any] = Field(
        default_factory=dict,
        description="Truncated summary of node inputs",
    )
    outputs_summary: dict[str, Any] = Field(
        default_factory=dict,
        description="Truncated summary of node outputs",
    )
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Tool calls made during this node",
    )
    quality_score: int | None = Field(
        None,
        description="Quality score (only for validate node)",
    )
    route_rationale: RouteRationale | None = Field(
        None,
        description="SmartRouter rationale (only for nodes that select a model)",
    )
    error: str | None = Field(None, description="Error message if status=failed")


class RunTrace(BaseModel):
    """Complete execution trace for a pipeline run."""

    run_id: str = Field(..., description="Pipeline run ID")
    teacher_id: str = Field("", description="Owning teacher for tenant isolation")
    status: str = Field("running", description="running | completed | failed")
    total_time_ms: float = Field(0.0, description="Total wall-clock time")
    nodes: list[NodeTrace] = Field(default_factory=list, description="Per-node traces in order")
    final_score: int | None = Field(None, description="Final quality score if available")
    model_used: str = Field("", description="Primary model used")
    refinement_count: int = Field(0, description="Number of refinement iterations")
