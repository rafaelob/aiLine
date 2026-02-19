"""Tests for all domain entity models.

Verifies Pydantic validation, default values, enums, and model behavior
across plan, tutor, material, curriculum, accessibility, and run entities.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from ailine_runtime.domain.entities.accessibility import (
    AccessibilityNeed,
    SupportIntensity,
)
from ailine_runtime.domain.entities.curriculum import (
    CurriculumObjective,
    CurriculumSystem,
)
from ailine_runtime.domain.entities.material import Material, MaterialChunk
from ailine_runtime.domain.entities.plan import (
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
from ailine_runtime.domain.entities.run import PipelineRun, RunEvent
from ailine_runtime.domain.entities.tutor import (
    LearnerProfile,
    TutorAgentSpec,
    TutorMaterialsScope,
    TutorMessage,
    TutorPersona,
    TutorSession,
    TutorTurnOutput,
)

# ---------------------------------------------------------------------------
# Plan entities
# ---------------------------------------------------------------------------


class TestRunStage:
    def test_enum_values(self) -> None:
        assert RunStage.PLANNER == "planner"
        assert RunStage.VALIDATE == "validate"
        assert RunStage.REFINE == "refine"
        assert RunStage.EXECUTOR == "executor"
        assert RunStage.DONE == "done"
        assert RunStage.FAILED == "failed"

    def test_all_values_are_strings(self) -> None:
        for stage in RunStage:
            assert isinstance(stage.value, str)


class TestExportFormat:
    def test_all_12_variants(self) -> None:
        assert len(ExportFormat) == 12

    def test_standard_html(self) -> None:
        assert ExportFormat.STANDARD_HTML == "standard_html"

    def test_audio_script(self) -> None:
        assert ExportFormat.AUDIO_SCRIPT == "audio_script"


class TestObjective:
    def test_basic_objective(self) -> None:
        obj = Objective(id=None, text="Understand fractions")
        assert obj.text == "Understand fractions"
        assert obj.id is None

    def test_objective_with_code(self) -> None:
        obj = Objective(id="EF06MA01", text="Identify fractions")
        assert obj.id == "EF06MA01"

    def test_objective_requires_text(self) -> None:
        with pytest.raises(ValidationError):
            Objective()  # type: ignore[call-arg]


class TestPlanStep:
    def test_basic_step(self) -> None:
        step = PlanStep(
            minutes=15,
            title="Introduction",
            instructions=["Present the topic."],
        )
        assert step.minutes == 15
        assert step.activities == []
        assert step.assessment == []

    def test_step_minutes_minimum(self) -> None:
        with pytest.raises(ValidationError):
            PlanStep(minutes=0, title="T", instructions=["Do X."])

    def test_step_requires_instructions(self) -> None:
        with pytest.raises(ValidationError):
            PlanStep(minutes=5, title="T")  # type: ignore[call-arg]


class TestStudentStep:
    def test_defaults(self) -> None:
        step = StudentStep(minutes=10, title="Practice", instructions=["Do exercise."])
        assert step.check_for_understanding == []
        assert step.self_regulation_prompts == []


class TestStudentPlan:
    def test_empty_defaults(self) -> None:
        plan = StudentPlan()
        assert plan.summary == []
        assert plan.steps == []
        assert plan.glossary == []
        assert plan.alternative_response_options == []


class TestAccessibilityAdaptation:
    def test_basic_adaptation(self) -> None:
        a = AccessibilityAdaptation(
            target="autism",
            strategies=["Use visual schedule"],
            do_not=["Use figurative language"],
        )
        assert a.target == "autism"
        assert len(a.strategies) == 1
        assert len(a.do_not) == 1
        assert a.notes == []


class TestAccessibilityPackDraft:
    def test_defaults(self) -> None:
        pack = AccessibilityPackDraft()
        assert pack.applied_adaptations == []
        assert pack.human_review_required is False
        assert pack.human_review_reasons == []


class TestStudyPlanDraft:
    def test_minimal_draft(self) -> None:
        draft = StudyPlanDraft(
            title="Fracoes",
            grade="5o ano",
            standard="BNCC",
            objectives=[Objective(id=None, text="Learn fractions")],
            steps=[PlanStep(minutes=10, title="Intro", instructions=["Start."])],
        )
        assert draft.title == "Fracoes"
        assert len(draft.objectives) == 1
        assert len(draft.steps) == 1
        assert draft.accessibility_pack_draft.human_review_required is False
        assert draft.student_plan.summary == []
        assert draft.evidence_requests == []

    def test_requires_objectives(self) -> None:
        with pytest.raises(ValidationError):
            StudyPlanDraft(
                title="T",
                grade="5",
                standard="BNCC",
                steps=[PlanStep(minutes=5, title="T", instructions=["X"])],
            )  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Tutor entities
# ---------------------------------------------------------------------------


class TestLearnerProfile:
    def test_basic(self) -> None:
        lp = LearnerProfile(name="Aluno A", age=None, language="pt-BR")
        assert lp.name == "Aluno A"
        assert lp.language == "pt-BR"
        assert lp.needs == []
        assert lp.strengths == []
        assert lp.age is None

    def test_age_boundaries(self) -> None:
        lp = LearnerProfile(name="A", age=3, language="pt-BR")
        assert lp.age == 3
        lp = LearnerProfile(name="A", age=25, language="pt-BR")
        assert lp.age == 25

    def test_age_below_minimum(self) -> None:
        with pytest.raises(ValidationError):
            LearnerProfile(name="A", age=2, language="pt-BR")

    def test_age_above_maximum(self) -> None:
        with pytest.raises(ValidationError):
            LearnerProfile(name="A", age=26, language="pt-BR")


class TestTutorPersona:
    def test_defaults(self) -> None:
        p = TutorPersona(system_prompt="You are a tutor.")
        assert p.response_contract == "json"
        assert p.notes == []


class TestTutorMaterialsScope:
    def test_basic(self) -> None:
        scope = TutorMaterialsScope(teacher_id="t1", subject="Math")
        assert scope.material_ids == []
        assert scope.tags == []


class TestTutorAgentSpec:
    def test_full_spec(self) -> None:
        spec = TutorAgentSpec(
            tutor_id="tutor-1",
            created_at="2026-01-01T00:00:00Z",
            teacher_id="teacher-1",
            subject="Matematica",
            grade="6o ano",
            student_profile=LearnerProfile(name="Aluno X", age=None, needs=["adhd"], language="pt-BR"),
            materials_scope=TutorMaterialsScope(
                teacher_id="teacher-1", subject="Matematica"
            ),
            persona=TutorPersona(system_prompt="Be kind."),
        )
        assert spec.style == "socratic"
        assert spec.standard == "BNCC"
        assert spec.human_review_required is False


class TestTutorTurnOutput:
    def test_defaults(self) -> None:
        out = TutorTurnOutput(answer_markdown="Hello!")
        assert out.step_by_step == []
        assert out.check_for_understanding == []
        assert out.self_regulation_prompt is None
        assert out.teacher_note is None


class TestTutorSession:
    def test_empty_session(self) -> None:
        s = TutorSession(
            session_id="s1",
            tutor_id="t1",
            created_at="2026-01-01T00:00:00Z",
        )
        assert s.messages == []

    def test_append_messages(self) -> None:
        s = TutorSession(
            session_id="s1",
            tutor_id="t1",
            created_at="2026-01-01T00:00:00Z",
        )
        s.append("user", "Hello")
        s.append("assistant", "Hi there!")
        assert len(s.messages) == 2
        assert s.messages[0].role == "user"
        assert s.messages[0].content == "Hello"
        assert s.messages[1].role == "assistant"

    def test_append_sets_timestamp(self) -> None:
        s = TutorSession(
            session_id="s1",
            tutor_id="t1",
            created_at="2026-01-01T00:00:00Z",
        )
        s.append("user", "test")
        # Timestamp should be a valid ISO format
        ts = s.messages[0].created_at
        assert ts  # non-empty
        # Should be parseable
        datetime.fromisoformat(ts)


class TestTutorMessage:
    def test_basic(self) -> None:
        m = TutorMessage(
            role="user", content="Hello", created_at="2026-01-01T00:00:00Z"
        )
        assert m.role == "user"
        assert m.content == "Hello"


# ---------------------------------------------------------------------------
# Material entities
# ---------------------------------------------------------------------------


class TestMaterial:
    def test_basic(self) -> None:
        m = Material(
            material_id="m1",
            teacher_id="t1",
            subject="Math",
            title="Fractions",
            content="About fractions",
            created_at="2026-01-01T00:00:00Z",
        )
        assert m.material_id == "m1"
        assert m.tags == []

    def test_with_tags(self) -> None:
        m = Material(
            material_id="m2",
            teacher_id="t1",
            subject="Math",
            title="T",
            content="C",
            tags=["bncc", "fracoes"],
            created_at="2026-01-01T00:00:00Z",
        )
        assert len(m.tags) == 2


class TestMaterialChunk:
    def test_basic(self) -> None:
        c = MaterialChunk(
            chunk_id="c1",
            material_id="m1",
            chunk_index=0,
            content="First chunk text",
        )
        assert c.embedding is None
        assert c.metadata == {}


# ---------------------------------------------------------------------------
# Curriculum entities
# ---------------------------------------------------------------------------


class TestCurriculumSystem:
    def test_enum_values(self) -> None:
        assert CurriculumSystem.BNCC == "bncc"
        assert CurriculumSystem.CCSS == "ccss"
        assert CurriculumSystem.NGSS == "ngss"


class TestCurriculumObjective:
    def test_basic(self) -> None:
        obj = CurriculumObjective(
            code="EF06MA01",
            system=CurriculumSystem.BNCC,
            subject="Matematica",
            grade="6o ano",
            description="Understand fractions.",
            bloom_level=None,
        )
        assert obj.code == "EF06MA01"
        assert obj.domain == ""
        assert obj.keywords == []


# ---------------------------------------------------------------------------
# Accessibility entities
# ---------------------------------------------------------------------------


class TestAccessibilityNeed:
    def test_all_needs(self) -> None:
        needs = list(AccessibilityNeed)
        assert len(needs) == 7
        assert AccessibilityNeed.AUTISM == "autism"
        assert AccessibilityNeed.MOTOR == "motor"


class TestSupportIntensity:
    def test_valid_values(self) -> None:
        # SupportIntensity is a Literal type, not an enum
        valid: list[SupportIntensity] = ["none", "low", "medium", "high"]
        assert len(valid) == 4


# ---------------------------------------------------------------------------
# Run entities
# ---------------------------------------------------------------------------


class TestRunEvent:
    def test_basic(self) -> None:
        ev = RunEvent(
            event_id="e1",
            run_id="r1",
            stage=RunStage.PLANNER,
            event_type="start",
            timestamp="2026-01-01T00:00:00Z",
        )
        assert ev.data == {}


class TestPipelineRun:
    def test_defaults(self) -> None:
        run = PipelineRun(run_id="r1")
        assert run.plan_id is None
        assert run.trigger == "api"
        assert run.status == "pending"
        assert run.events == []
        assert run.started_at is None
        assert run.completed_at is None
