"""Tests for the skills resolution LangGraph nodes (F-177).

Covers:
- _resolve_skills_from_request() with explicit and accessibility modes
- make_skills_node() for plan_workflow
- make_tutor_skills_node() for tutor_workflow
- Edge cases: empty request, invalid profiles, mixed modes
"""

from __future__ import annotations

from typing import Any

import pytest

from ailine_agents.workflows._skills_node import (
    _resolve_skills_from_request,
    make_skills_node,
    make_tutor_skills_node,
)


# ---------------------------------------------------------------------------
# _resolve_skills_from_request — Explicit selection mode
# ---------------------------------------------------------------------------


class TestResolveExplicitSkills:
    """Mode 1: selected_skills dict entries are converted to ActivatedSkill."""

    def test_single_explicit_skill(self) -> None:
        request = {
            "selected_skills": [
                {
                    "slug": "lesson-planner",
                    "description": "Plans lessons",
                    "instructions_md": "# Lesson Planner\nPlan detailed lessons.",
                    "reason": "teacher requested",
                    "priority": 10,
                }
            ],
        }
        result = _resolve_skills_from_request(request)
        assert len(result) == 1
        assert result[0].name == "lesson-planner"
        assert result[0].description == "Plans lessons"
        assert result[0].reason == "teacher requested"
        assert result[0].priority == 10

    def test_multiple_explicit_skills(self) -> None:
        request = {
            "selected_skills": [
                {"slug": "quiz-generator", "description": "Generates quizzes"},
                {"name": "rubric-writer", "description": "Writes rubrics"},
            ],
        }
        result = _resolve_skills_from_request(request)
        assert len(result) == 2
        names = {s.name for s in result}
        assert "quiz-generator" in names
        assert "rubric-writer" in names

    def test_explicit_defaults(self) -> None:
        """Missing fields get sensible defaults."""
        request = {"selected_skills": [{"slug": "socratic-tutor"}]}
        result = _resolve_skills_from_request(request)
        assert len(result) == 1
        assert result[0].name == "socratic-tutor"
        assert result[0].description == ""
        assert result[0].reason == "explicitly selected"
        assert result[0].priority == 50

    def test_non_dict_entries_ignored(self) -> None:
        """String entries (not dicts) are silently skipped."""
        request = {"selected_skills": ["lesson-planner", {"slug": "quiz-generator"}]}
        result = _resolve_skills_from_request(request)
        assert len(result) == 1
        assert result[0].name == "quiz-generator"

    def test_empty_selected_skills(self) -> None:
        request = {"selected_skills": []}
        result = _resolve_skills_from_request(request)
        assert result == []


# ---------------------------------------------------------------------------
# _resolve_skills_from_request — Accessibility policy mode
# ---------------------------------------------------------------------------


class TestResolveAccessibilitySkills:
    """Mode 2: accessibility_needs or accessibility_profile resolve via policy."""

    def test_single_need_autism(self) -> None:
        request = {"accessibility_needs": ["autism"]}
        result = _resolve_skills_from_request(request)
        assert len(result) > 0
        names = {s.name for s in result}
        # Must-have skills for autism
        assert "accessibility-coach" in names
        assert "accessibility-adaptor" in names

    def test_single_profile_shorthand(self) -> None:
        """accessibility_profile is a shorthand for a single-element needs list."""
        request = {"accessibility_profile": "hearing"}
        result = _resolve_skills_from_request(request)
        assert len(result) > 0
        names = {s.name for s in result}
        assert "accessibility-coach" in names

    def test_multiple_needs_deduplicates(self) -> None:
        """Skills shared across needs are deduplicated with highest priority."""
        request = {"accessibility_needs": ["autism", "adhd"]}
        result = _resolve_skills_from_request(request)
        names = [s.name for s in result]
        # accessibility-coach appears in both but should only appear once
        assert names.count("accessibility-coach") == 1

    def test_max_skills_limits_output(self) -> None:
        request = {"accessibility_needs": ["autism"], "max_skills": 3}
        result = _resolve_skills_from_request(request)
        assert len(result) <= 3

    def test_unknown_need_skipped(self) -> None:
        """Unknown accessibility needs are silently filtered out."""
        request = {"accessibility_needs": ["unknown_need"]}
        result = _resolve_skills_from_request(request)
        assert result == []

    def test_mixed_valid_invalid_needs(self) -> None:
        request = {"accessibility_needs": ["autism", "nonexistent"]}
        result = _resolve_skills_from_request(request)
        assert len(result) > 0  # autism skills still resolved

    def test_priorities_are_numeric(self) -> None:
        """All resolved skills have numeric priorities."""
        request = {"accessibility_needs": ["visual"]}
        result = _resolve_skills_from_request(request)
        for skill in result:
            assert isinstance(skill.priority, int)
            assert skill.priority >= 0


# ---------------------------------------------------------------------------
# _resolve_skills_from_request — Mode priority
# ---------------------------------------------------------------------------


class TestResolvePriority:
    """Explicit selection takes precedence over accessibility policy."""

    def test_explicit_prevents_accessibility(self) -> None:
        """When selected_skills is provided, accessibility_needs is ignored."""
        request = {
            "selected_skills": [{"slug": "quiz-generator"}],
            "accessibility_needs": ["autism"],
        }
        result = _resolve_skills_from_request(request)
        assert len(result) == 1
        assert result[0].name == "quiz-generator"

    def test_empty_request(self) -> None:
        result = _resolve_skills_from_request({})
        assert result == []

    def test_none_values(self) -> None:
        request = {"selected_skills": None, "accessibility_needs": None}
        result = _resolve_skills_from_request(request)
        assert result == []


# ---------------------------------------------------------------------------
# make_skills_node — Plan workflow
# ---------------------------------------------------------------------------


def _make_mock_config() -> Any:
    """Create a minimal RunnableConfig with mocked callbacks for SSE."""
    config: dict[str, Any] = {"callbacks": []}
    return config


class TestPlanSkillsNode:
    """make_skills_node() creates a LangGraph node for plan_workflow."""

    @pytest.mark.asyncio
    async def test_skip_when_no_skill_request(self) -> None:
        node = make_skills_node()
        state = {"run_id": "r-1", "user_prompt": "test"}
        result = await node(state, _make_mock_config())
        assert result["activated_skills"] == []
        assert result["skill_prompt_fragment"] == ""

    @pytest.mark.asyncio
    async def test_resolves_explicit_skills(self) -> None:
        node = make_skills_node()
        state = {
            "run_id": "r-1",
            "user_prompt": "test",
            "skill_request": {
                "selected_skills": [
                    {
                        "slug": "lesson-planner",
                        "description": "Plans lessons",
                        "instructions_md": "Plan a lesson.",
                        "reason": "requested",
                    }
                ],
            },
        }
        result = await node(state, _make_mock_config())
        assert len(result["activated_skills"]) == 1
        assert result["activated_skills"][0]["name"] == "lesson-planner"
        assert result["skill_prompt_fragment"] != ""

    @pytest.mark.asyncio
    async def test_resolves_accessibility_skills(self) -> None:
        node = make_skills_node()
        state = {
            "run_id": "r-1",
            "user_prompt": "test",
            "skill_request": {"accessibility_needs": ["autism"]},
        }
        result = await node(state, _make_mock_config())
        assert len(result["activated_skills"]) > 0
        names = {s["name"] for s in result["activated_skills"]}
        assert "accessibility-coach" in names

    @pytest.mark.asyncio
    async def test_fragment_contains_skill_names(self) -> None:
        node = make_skills_node()
        state = {
            "run_id": "r-1",
            "user_prompt": "test",
            "skill_request": {
                "selected_skills": [
                    {
                        "slug": "quiz-generator",
                        "description": "Generates quizzes",
                        "instructions_md": "Generate a quiz.",
                    }
                ],
            },
        }
        result = await node(state, _make_mock_config())
        assert "quiz-generator" in result["skill_prompt_fragment"]

    @pytest.mark.asyncio
    async def test_custom_token_budget(self) -> None:
        node = make_skills_node()
        state = {
            "run_id": "r-1",
            "user_prompt": "test",
            "skill_request": {
                "selected_skills": [
                    {
                        "slug": "lesson-planner",
                        "instructions_md": "x" * 20000,
                    }
                ],
                "token_budget": 100,
            },
        }
        result = await node(state, _make_mock_config())
        # Fragment should be truncated due to low budget
        fragment = result["skill_prompt_fragment"]
        assert len(fragment) < 20000

    @pytest.mark.asyncio
    async def test_error_returns_empty_skills(self) -> None:
        """Errors in skill resolution are non-fatal."""
        node = make_skills_node()
        state = {
            "run_id": "r-1",
            "user_prompt": "test",
            "skill_request": {
                "selected_skills": "invalid-not-a-list",
            },
        }
        result = await node(state, _make_mock_config())
        assert result["activated_skills"] == []
        assert result["skill_prompt_fragment"] == ""


# ---------------------------------------------------------------------------
# make_tutor_skills_node — Tutor workflow
# ---------------------------------------------------------------------------


class TestTutorSkillsNode:
    """make_tutor_skills_node() creates a LangGraph node for tutor_workflow."""

    @pytest.mark.asyncio
    async def test_skip_when_no_skill_request(self) -> None:
        node = make_tutor_skills_node()
        state = {
            "tutor_id": "t-1",
            "session_id": "s-1",
            "user_message": "hello",
        }
        result = await node(state, _make_mock_config())
        assert result["activated_skills"] == []
        assert result["skill_prompt_fragment"] == ""

    @pytest.mark.asyncio
    async def test_resolves_explicit_skills(self) -> None:
        node = make_tutor_skills_node()
        state = {
            "tutor_id": "t-1",
            "session_id": "s-1",
            "user_message": "hello",
            "skill_request": {
                "selected_skills": [
                    {
                        "slug": "socratic-tutor",
                        "description": "Socratic method",
                        "instructions_md": "Use Socratic questioning.",
                    }
                ],
            },
        }
        result = await node(state, _make_mock_config())
        assert len(result["activated_skills"]) == 1
        assert result["activated_skills"][0]["name"] == "socratic-tutor"

    @pytest.mark.asyncio
    async def test_resolves_accessibility_profile(self) -> None:
        node = make_tutor_skills_node()
        state = {
            "tutor_id": "t-1",
            "session_id": "s-1",
            "user_message": "hello",
            "skill_request": {"accessibility_profile": "adhd"},
        }
        result = await node(state, _make_mock_config())
        assert len(result["activated_skills"]) > 0

    @pytest.mark.asyncio
    async def test_error_returns_empty_skills(self) -> None:
        node = make_tutor_skills_node()
        state = {
            "tutor_id": "t-1",
            "session_id": "s-1",
            "user_message": "hello",
            "skill_request": {"selected_skills": 12345},  # invalid type
        }
        result = await node(state, _make_mock_config())
        assert result["activated_skills"] == []
        assert result["skill_prompt_fragment"] == ""


# ---------------------------------------------------------------------------
# Integration: skill_prompt_fragment in planner prompt
# ---------------------------------------------------------------------------


class TestPlannerPromptSkillInjection:
    """Verify _build_planner_prompt injects skill_prompt_fragment."""

    def test_planner_prompt_includes_fragment(self) -> None:
        from ailine_agents.workflows._planner_node import _build_planner_prompt

        state = {
            "run_id": "r-1",
            "user_prompt": "Create a fractions plan",
            "skill_prompt_fragment": "## Skills Runtime\n- lesson-planner: active",
        }
        result = _build_planner_prompt(state, refine_iter=0)  # type: ignore[arg-type]
        assert "Skills Runtime" in result
        assert "lesson-planner" in result

    def test_planner_prompt_without_fragment(self) -> None:
        from ailine_agents.workflows._planner_node import _build_planner_prompt

        state = {
            "run_id": "r-1",
            "user_prompt": "Create a plan",
        }
        result = _build_planner_prompt(state, refine_iter=0)  # type: ignore[arg-type]
        assert "Skills Runtime" not in result
