"""Tests for the tutor workflow re-export shim.

The actual workflow logic is tested in the agents package (ailine_agents).
These tests verify the re-export module works correctly and that
the imported symbols match expectations.
"""

from __future__ import annotations

import pytest

from ailine_runtime.workflow.tutor_workflow import (
    TutorGraphState,
    build_tutor_workflow,
    run_tutor_turn,
)


class TestTutorWorkflowReExports:
    """Verify the re-export shim exposes the correct symbols."""

    def test_tutor_graph_state_is_type(self) -> None:
        assert TutorGraphState is not None

    def test_build_tutor_workflow_is_callable(self) -> None:
        assert callable(build_tutor_workflow)

    def test_run_tutor_turn_is_callable(self) -> None:
        assert callable(run_tutor_turn)

    def test_tutor_graph_state_has_required_keys(self) -> None:
        annotations = TutorGraphState.__annotations__
        assert "tutor_id" in annotations
        assert "session_id" in annotations
        assert "user_message" in annotations

    def test_imports_come_from_ailine_agents(self) -> None:
        """Ensure re-exports point to ailine_agents, not stale local code."""
        assert build_tutor_workflow.__module__.startswith("ailine_agents")
        assert run_tutor_turn.__module__.startswith("ailine_agents")


class TestClassifyIntentViaAgents:
    """Test _classify_intent through the agents package."""

    def test_classify_intent_importable(self) -> None:
        from ailine_agents.workflows.tutor_workflow import _classify_intent

        assert callable(_classify_intent)

    @pytest.mark.parametrize(
        "msg,expected",
        [
            ("oi", "greeting"),
            ("Ola!", "greeting"),
            ("bom dia", "greeting"),
            ("hello", "greeting"),
            ("me conta uma piada", "offtopic"),
            ("voce viu o jogo de futebol?", "offtopic"),
            ("nao entendi", "clarification"),
            ("pode explicar de novo?", "clarification"),
            ("Quanto e 2+2?", "question"),
            ("", "question"),
        ],
    )
    def test_intent_classification(self, msg: str, expected: str) -> None:
        from ailine_agents.workflows.tutor_workflow import _classify_intent

        assert _classify_intent(msg) == expected
