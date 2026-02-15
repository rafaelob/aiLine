"""Tutor-related domain entities (canonical source).

Pure Pydantic models for the 1:1 tutoring subsystem: learner profiles,
tutor agent specifications, session state, and structured turn output.

NOTE: tutoring/models.py re-exports from here. Do NOT duplicate definitions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class LearnerProfile(BaseModel):
    """Functional learner profile (non-diagnostic).

    ``needs`` contains functional needs and preferences, for example:
    "autism", "adhd", "learning_difficulty", "hearing", "visual",
    "needs_predictability", "needs_short_instructions", etc.
    """

    name: str = Field(..., description="Student name/alias (no sensitive data).")
    age: int | None = Field(None, ge=3, le=25)
    needs: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    accommodations: list[str] = Field(default_factory=list)
    language: str = Field("pt-BR")


class TutorPersona(BaseModel):
    """The generated persona (system prompt) for a tutor agent."""

    system_prompt: str
    response_contract: str = "json"
    notes: list[str] = Field(default_factory=list)


class TutorMaterialsScope(BaseModel):
    """Defines which materials a tutor agent is allowed to search."""

    teacher_id: str
    subject: str
    material_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class TutorAgentSpec(BaseModel):
    """Full specification of a configured tutor agent.

    Created by the teacher, persisted, and used at runtime to
    drive chat sessions with a student.
    """

    tutor_id: str
    created_at: str
    teacher_id: str
    subject: str
    grade: str
    standard: str = "BNCC"
    style: Literal["socratic", "coach", "direct", "explainer"] = "socratic"
    tone: str = "calmo, paciente, encorajador"
    student_profile: LearnerProfile
    materials_scope: TutorMaterialsScope
    persona: TutorPersona
    human_review_required: bool = False
    human_review_reasons: list[str] = Field(default_factory=list)


class TutorTurnOutput(BaseModel):
    """Structured output from a single tutor turn (for UI rendering)."""

    answer_markdown: str
    step_by_step: list[str] = Field(default_factory=list)
    check_for_understanding: list[str] = Field(default_factory=list)
    options_to_respond: list[str] = Field(default_factory=list)
    self_regulation_prompt: str | None = None
    citations: list[str] = Field(default_factory=list)
    teacher_note: str | None = None
    flags: list[str] = Field(default_factory=list)


class TutorMessage(BaseModel):
    """A single message in a tutoring session."""

    role: Literal["user", "assistant"]
    content: str
    created_at: str


class TutorSession(BaseModel):
    """Conversational state for a tutoring session."""

    session_id: str
    tutor_id: str
    created_at: str
    messages: list[TutorMessage] = Field(default_factory=list)

    def append(self, role: Literal["user", "assistant"], content: str) -> None:
        """Append a message with the current UTC timestamp."""
        self.messages.append(
            TutorMessage(
                role=role,
                content=content,
                created_at=datetime.now(UTC).isoformat(),
            )
        )


class TutorTurnFlag(BaseModel):
    """A flag on a specific tutor conversation turn for teacher review."""

    flag_id: str
    session_id: str
    turn_index: int = Field(..., ge=0, description="Index of the message in session.messages.")
    teacher_id: str
    reason: str = Field("", description="Why this turn was flagged.")
    created_at: str
