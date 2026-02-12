"""Domain entities re-exports.

Provides a single import point for the most commonly used domain models.
"""

from .accessibility import AccessibilityNeed, SupportIntensity
from .curriculum import CurriculumObjective, CurriculumSystem
from .material import Material, MaterialChunk
from .plan import (
    AccessibilityAdaptation,
    AccessibilityPackDraft,
    ExportFormat,
    Objective,
    PlanStep,
    RunStage,
    StudentPlan,
    StudentStep,
    StudyPlanDraft,
)
from .run import PipelineRun, RunEvent
from .tutor import (
    LearnerProfile,
    TutorAgentSpec,
    TutorMaterialsScope,
    TutorMessage,
    TutorPersona,
    TutorSession,
    TutorTurnOutput,
)

__all__ = [
    # plan
    "AccessibilityAdaptation",
    # accessibility
    "AccessibilityNeed",
    "AccessibilityPackDraft",
    # curriculum
    "CurriculumObjective",
    "CurriculumSystem",
    "ExportFormat",
    # tutor
    "LearnerProfile",
    # material
    "Material",
    "MaterialChunk",
    "Objective",
    # run
    "PipelineRun",
    "PlanStep",
    "RunEvent",
    "RunStage",
    "StudentPlan",
    "StudentStep",
    "StudyPlanDraft",
    "SupportIntensity",
    "TutorAgentSpec",
    "TutorMaterialsScope",
    "TutorMessage",
    "TutorPersona",
    "TutorSession",
    "TutorTurnOutput",
]
