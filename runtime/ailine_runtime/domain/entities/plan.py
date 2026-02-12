"""Plan-related domain entities.

Pure Pydantic models with zero framework dependencies.
These represent the core study plan structure used throughout the pipeline:
Planner -> Validator -> Executor -> Export.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class RunStage(StrEnum):
    """Stages of a pipeline run lifecycle."""

    PLANNER = "planner"
    VALIDATE = "validate"
    REFINE = "refine"
    EXECUTOR = "executor"
    DONE = "done"
    FAILED = "failed"


class ExportFormat(StrEnum):
    """Supported export formats for study plans.

    Each format targets a specific accessibility need or delivery channel.
    """

    STANDARD_HTML = "standard_html"
    LOW_DISTRACTION_HTML = "low_distraction_html"
    LARGE_PRINT_HTML = "large_print_html"
    HIGH_CONTRAST_HTML = "high_contrast_html"
    DYSLEXIA_FRIENDLY_HTML = "dyslexia_friendly_html"
    SCREEN_READER_HTML = "screen_reader_html"
    VISUAL_SCHEDULE_HTML = "visual_schedule_html"
    VISUAL_SCHEDULE_JSON = "visual_schedule_json"
    STUDENT_PLAIN_TEXT = "student_plain_text"
    AUDIO_SCRIPT = "audio_script"


class Objective(BaseModel):
    """A single learning objective tied to a curriculum standard."""

    id: str | None = Field(None, description="Curriculum code (e.g. EF06MA01).")
    text: str = Field(..., description="Learning objective (clear and observable).")


class PlanStep(BaseModel):
    """One step in the teacher-facing study plan sequence."""

    minutes: int = Field(..., ge=1)
    title: str
    instructions: list[str] = Field(
        ..., description="Numbered instructions (1 action per item)."
    )
    activities: list[str] = Field(default_factory=list)
    assessment: list[str] = Field(
        default_factory=list, description="Quick checks."
    )


class StudentStep(BaseModel):
    """One step in the student-facing plan (simplified language)."""

    minutes: int = Field(..., ge=1)
    title: str
    instructions: list[str] = Field(
        ..., description="Very short, clear steps."
    )
    check_for_understanding: list[str] = Field(default_factory=list)
    self_regulation_prompts: list[str] = Field(default_factory=list)


class StudentPlan(BaseModel):
    """Student-facing version of a study plan (neurodiversity-friendly)."""

    summary: list[str] = Field(default_factory=list)
    steps: list[StudentStep] = Field(default_factory=list)
    glossary: list[str] = Field(default_factory=list)
    alternative_response_options: list[str] = Field(default_factory=list)


class AccessibilityAdaptation(BaseModel):
    """A single accessibility adaptation targeting a specific need."""

    target: str = Field(
        ...,
        description="autism|adhd|learning|hearing|visual|speech_language|motor|universal",
    )
    strategies: list[str] = Field(default_factory=list)
    do_not: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class AccessibilityPackDraft(BaseModel):
    """Accessibility metadata attached to a study plan draft."""

    applied_adaptations: list[AccessibilityAdaptation] = Field(
        default_factory=list
    )
    media_requirements: list[str] = Field(default_factory=list)
    ui_recommendations: list[str] = Field(default_factory=list)
    visual_schedule_notes: list[str] = Field(default_factory=list)
    teacher_review_points: list[str] = Field(default_factory=list)
    human_review_required: bool = False
    human_review_reasons: list[str] = Field(default_factory=list)


class StudyPlanDraft(BaseModel):
    """Complete study plan draft produced by the Planner stage.

    Contains both teacher-facing and student-facing content,
    plus accessibility pack and evidence requests for RAG.
    """

    title: str
    grade: str
    standard: str = Field(..., description="BNCC|US")
    objectives: list[Objective]
    steps: list[PlanStep]
    accessibility_pack_draft: AccessibilityPackDraft = Field(
        default_factory=AccessibilityPackDraft
    )
    student_plan: StudentPlan = Field(default_factory=StudentPlan)
    evidence_requests: list[str] = Field(default_factory=list)
