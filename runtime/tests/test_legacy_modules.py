"""Tests for legacy modules: tutoring.models.

Legacy api_app and workflow_langgraph have been removed (they were thin
re-export shims). Only tutoring.models backward compatibility is tested.
"""

from __future__ import annotations


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
