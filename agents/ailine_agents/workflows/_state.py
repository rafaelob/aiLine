"""LangGraph state types for agent-driven workflows."""

from __future__ import annotations

from typing import Any, TypedDict


class _RunStateRequired(TypedDict):
    """Required fields for the plan generation pipeline state."""

    run_id: str
    user_prompt: str


class RunState(_RunStateRequired, total=False):
    """LangGraph state for the plan generation pipeline.

    Required: run_id, user_prompt.
    Optional: populated during pipeline execution.
    """

    teacher_id: str | None
    subject: str | None
    class_accessibility_profile: dict[str, Any] | None
    learner_profiles: list[dict[str, Any]] | None
    draft: dict[str, Any]
    quality_assessment: dict[str, Any]
    validation: dict[str, Any]
    final: dict[str, Any]
    refine_iter: int
    quality_decision: dict[str, Any] | None

    # RAG results from planner tool calls (if any)
    rag_results: list[dict[str, Any]] | None

    # Idempotency: prevents duplicate plan generations from double-clicks.
    idempotency_key: str | None

    # Workflow timing: monotonic timestamp when the workflow started.
    started_at: float | None

    # Transformation scorecard computed after executor.
    scorecard: dict[str, Any] | None


class _TutorGraphStateRequired(TypedDict):
    """Required fields for the tutor graph state."""

    tutor_id: str
    session_id: str
    user_message: str


class TutorGraphState(_TutorGraphStateRequired, total=False):
    """State dict flowing through the tutor LangGraph."""

    history: list[dict[str, Any]]
    spec: dict[str, Any]
    intent: str
    rag_results: list[dict[str, Any]]
    response: str
    validated_output: dict[str, Any] | None
    error: str | None

    # Workflow timing: monotonic timestamp when the workflow started.
    started_at: float | None
