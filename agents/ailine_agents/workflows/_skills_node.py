"""Skills resolution node for LangGraph workflows (F-177).

Resolves activated skills from the database (or filesystem fallback)
based on the SkillRequestContext in the workflow state. Composes the
skill prompt fragment and writes it back to the state for downstream
nodes (planner, tutor) to inject into their LLM prompts.

Integrates with:
- SkillRepository (DB-backed, from F-175/F-176)
- SkillPromptComposer (token-budget composer)
- AccessibilityPolicy (deterministic skill tiers)
- SkillRegistry (filesystem fallback)
"""

from __future__ import annotations

import time
from typing import Any

import structlog
from langgraph.types import RunnableConfig

from ailine_runtime.api.streaming.events import SSEEventType

from ..skills.accessibility_policy import (
    ACCESSIBILITY_NEED_CATEGORIES,
    resolve_accessibility_skills,
)
from ..skills.composer import ActivatedSkill, compose_skills_fragment
from ._sse_helpers import get_emitter_and_writer, try_emit
from ._state import RunState, TutorGraphState

__all__ = ["make_skills_node", "make_tutor_skills_node"]

_log = structlog.get_logger("ailine.workflows.skills_node")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_skills_from_request(
    skill_request: dict[str, Any],
) -> list[ActivatedSkill]:
    """Resolve activated skills from a SkillRequestContext dict.

    Supports two modes:
    1. **selected_skills**: Explicit list of skill slugs to activate.
    2. **accessibility_profile**: Use AccessibilityPolicy to determine
       skills based on learner needs.

    Returns a list of ActivatedSkill instances ready for composition.
    """
    activated: list[ActivatedSkill] = []

    # Mode 1: Explicit skill selection
    selected = skill_request.get("selected_skills") or []
    for entry in selected:
        if isinstance(entry, dict):
            activated.append(
                ActivatedSkill(
                    name=entry.get("slug", entry.get("name", "unknown")),
                    description=entry.get("description", ""),
                    instructions_md=entry.get("instructions_md", ""),
                    reason=entry.get("reason", "explicitly selected"),
                    priority=int(entry.get("priority", 50)),
                )
            )

    # Mode 2: Accessibility policy (needs-based resolution)
    raw_needs = skill_request.get("accessibility_needs") or []
    # SECURITY: Sanitize accessibility_needs — only allow known categories
    # to prevent prompt injection via user-controlled input.
    accessibility_needs = [
        n for n in raw_needs
        if isinstance(n, str) and n in ACCESSIBILITY_NEED_CATEGORIES
    ]
    profile_name = skill_request.get("accessibility_profile")
    if isinstance(profile_name, str) and profile_name not in ACCESSIBILITY_NEED_CATEGORIES:
        profile_name = None

    # Support single profile name as shorthand for one-element needs list
    if profile_name and not accessibility_needs:
        accessibility_needs = [profile_name]

    if accessibility_needs and not activated:
        try:
            # accessibility_needs already sanitized above
            if accessibility_needs:
                policy_skills, _needs_review = resolve_accessibility_skills(
                    accessibility_needs,
                    max_skills=skill_request.get("max_skills", 8),
                )
                for slug, reason, priority in policy_skills:
                    activated.append(
                        ActivatedSkill(
                            name=slug,
                            description=reason,
                            instructions_md="",  # Instructions loaded separately
                            reason=reason,
                            priority=priority,
                        )
                    )
        except (ValueError, KeyError) as exc:
            _log.warning(
                "skills_node.policy_resolve_failed",
                needs=accessibility_needs,
                error=str(exc),
            )

    return activated


# ---------------------------------------------------------------------------
# Plan workflow skills node
# ---------------------------------------------------------------------------


def make_skills_node():
    """Create the skills resolution node for plan_workflow.

    Reads ``skill_request`` from state, resolves skills, composes
    the prompt fragment, and writes back ``activated_skills`` and
    ``skill_prompt_fragment``.
    """

    async def skills_node(state: RunState, config: RunnableConfig) -> RunState:
        """Resolve skills and compose prompt fragment."""
        emitter, writer = get_emitter_and_writer(config)
        run_id = state.get("run_id", "")
        start = time.monotonic()

        skill_request = state.get("skill_request")
        if not skill_request:
            _log.debug("skills_node.skip", run_id=run_id, reason="no skill_request")
            return {  # type: ignore[typeddict-item,return-value]
                "activated_skills": [],
                "skill_prompt_fragment": "",
            }

        try:
            activated = _resolve_skills_from_request(skill_request)

            # Compose prompt fragment
            token_budget = skill_request.get("token_budget", 2500)
            fragment = compose_skills_fragment(
                activated, token_budget=token_budget
            )

            # Emit SSE event
            activated_dicts = [
                {"name": s.name, "reason": s.reason, "priority": s.priority}
                for s in activated
            ]
            try_emit(
                emitter,
                writer,
                SSEEventType.STAGE_COMPLETE,
                "skills",
                {
                    "count": len(activated),
                    "skills": activated_dicts,
                    "fragment_tokens": len(fragment) // 4,
                },
            )

            elapsed = time.monotonic() - start
            _log.info(
                "skills_node.resolved",
                run_id=run_id,
                count=len(activated),
                fragment_tokens=len(fragment) // 4,
                elapsed_ms=round(elapsed * 1000),
            )

            return {  # type: ignore[typeddict-item,return-value]
                "activated_skills": activated_dicts,
                "skill_prompt_fragment": fragment,
            }

        except Exception as exc:
            _log.error(
                "skills_node.failed",
                run_id=run_id,
                error=str(exc),
            )
            # SECURITY: Emit generic message — log details server-side only.
            try_emit(
                emitter,
                writer,
                SSEEventType.STAGE_FAILED,
                "skills",
                {"error": "skills_resolution_failed"},
            )
            # Non-fatal: return empty skills so workflow continues
            return {  # type: ignore[typeddict-item,return-value]
                "activated_skills": [],
                "skill_prompt_fragment": "",
            }

    return skills_node


# ---------------------------------------------------------------------------
# Tutor workflow skills node
# ---------------------------------------------------------------------------


def make_tutor_skills_node():
    """Create the skills resolution node for tutor_workflow.

    Same logic as plan skills node but operates on TutorGraphState.
    """

    async def tutor_skills_node(
        state: TutorGraphState, config: RunnableConfig
    ) -> TutorGraphState:
        """Resolve skills for tutor context."""
        skill_request = state.get("skill_request")
        if not skill_request:
            return {  # type: ignore[typeddict-item,return-value]
                "activated_skills": [],
                "skill_prompt_fragment": "",
            }

        try:
            activated = _resolve_skills_from_request(skill_request)
            token_budget = skill_request.get("token_budget", 2500)
            fragment = compose_skills_fragment(
                activated, token_budget=token_budget
            )

            activated_dicts = [
                {"name": s.name, "reason": s.reason, "priority": s.priority}
                for s in activated
            ]

            _log.info(
                "tutor_skills_node.resolved",
                session_id=state.get("session_id", ""),
                count=len(activated),
            )

            return {  # type: ignore[typeddict-item,return-value]
                "activated_skills": activated_dicts,
                "skill_prompt_fragment": fragment,
            }

        except Exception as exc:
            _log.warning(
                "tutor_skills_node.failed",
                session_id=state.get("session_id", ""),
                error=str(exc),
            )
            return {  # type: ignore[typeddict-item,return-value]
                "activated_skills": [],
                "skill_prompt_fragment": "",
            }

    return tutor_skills_node
