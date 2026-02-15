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
    PlanReview,
    PlanStep,
    ReviewStatus,
    RunStage,
    StandardRef,
    StudentPlan,
    StudentStep,
    StudyPlanDraft,
    TransformationScorecard,
)
from .progress import (
    ClassProgressSummary,
    LearnerProgress,
    MasteryLevel,
    StandardSummary,
    StudentSummary,
)
from .run import PipelineRun, RunEvent
from .tutor import (
    LearnerProfile,
    TutorAgentSpec,
    TutorMaterialsScope,
    TutorMessage,
    TutorPersona,
    TutorSession,
    TutorTurnFlag,
    TutorTurnOutput,
)

__all__ = [
    # plan
    "AccessibilityAdaptation",
    # accessibility
    "AccessibilityNeed",
    "AccessibilityPackDraft",
    # progress
    "ClassProgressSummary",
    # curriculum
    "CurriculumObjective",
    "CurriculumSystem",
    "ExportFormat",
    # tutor
    "LearnerProfile",
    "LearnerProgress",
    "MasteryLevel",
    # material
    "Material",
    "MaterialChunk",
    "Objective",
    # run
    "PipelineRun",
    "PlanReview",
    "PlanStep",
    "ReviewStatus",
    "RunEvent",
    "RunStage",
    "StandardRef",
    "StandardSummary",
    "StudentPlan",
    "StudentStep",
    "StudentSummary",
    "StudyPlanDraft",
    "SupportIntensity",
    "TransformationScorecard",
    "TutorAgentSpec",
    "TutorMaterialsScope",
    "TutorMessage",
    "TutorPersona",
    "TutorSession",
    "TutorTurnFlag",
    "TutorTurnOutput",
]
