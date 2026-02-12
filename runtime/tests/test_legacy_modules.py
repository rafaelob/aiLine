"""Tests for legacy modules: api_app, workflow_langgraph, tutoring.models.

These are thin re-export modules kept for backward compatibility.
We verify they import and expose the expected symbols.
"""

from __future__ import annotations


class TestApiApp:
    def test_imports_create_app(self):
        from ailine_runtime.api_app import create_app
        assert callable(create_app)

    def test_app_attribute(self):
        from ailine_runtime.api_app import app
        assert app is not None


class TestWorkflowLanggraph:
    def test_imports_build_workflow(self):
        from ailine_runtime.workflow_langgraph import build_workflow
        assert callable(build_workflow)

    def test_imports_run_state(self):
        from ailine_runtime.workflow_langgraph import RunState
        assert RunState is not None

    def test_all_exports(self):
        from ailine_runtime.workflow_langgraph import __all__
        assert "RunState" in __all__
        assert "build_workflow" in __all__

    def test_build_workflow_delegates(self):
        """Verify build_workflow is a thin wrapper over build_plan_workflow."""
        from unittest.mock import MagicMock, patch

        mock_build = MagicMock(return_value="mock_workflow")
        with patch(
            "ailine_runtime.workflow_langgraph.build_plan_workflow", mock_build
        ):
            from ailine_runtime.workflow_langgraph import build_workflow
            result = build_workflow("cfg", ["tool"])
            mock_build.assert_called_once_with("cfg", ["tool"])
            assert result == "mock_workflow"


class TestTutoringModels:
    def test_imports_tutor_models(self):
        from ailine_runtime.tutoring.models import (
            LearnerProfile,
            TutorAgentSpec,
            TutorMaterialsScope,
            TutorMessage,
            TutorPersona,
            TutorSession,
            TutorTurnOutput,
        )
        # Verify all are actual classes (not None)
        assert LearnerProfile is not None
        assert TutorAgentSpec is not None
        assert TutorMaterialsScope is not None
        assert TutorMessage is not None
        assert TutorPersona is not None
        assert TutorSession is not None
        assert TutorTurnOutput is not None

    def test_all_exports(self):
        from ailine_runtime.tutoring.models import __all__
        expected = {
            "LearnerProfile",
            "TutorAgentSpec",
            "TutorMaterialsScope",
            "TutorMessage",
            "TutorPersona",
            "TutorSession",
            "TutorTurnOutput",
        }
        assert set(__all__) == expected
