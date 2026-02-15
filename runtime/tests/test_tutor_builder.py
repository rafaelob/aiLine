"""Tests for the tutor builder and session management.

All tests use FakeChatLLM -- no real API keys required (ADR-051).
Local file storage uses a temporary directory to avoid side effects.
"""

from __future__ import annotations

import json
import os
from typing import Any

import pytest

from ailine_runtime.adapters.llm.fake_llm import FakeChatLLM
from ailine_runtime.domain.entities.tutor import (
    LearnerProfile,
    TutorAgentSpec,
    TutorMaterialsScope,
    TutorPersona,
)
from ailine_runtime.tutoring.builder import (
    create_tutor_agent,
    load_tutor_spec,
    save_tutor_spec,
)
from ailine_runtime.tutoring.playbooks import (
    PLAYBOOK_BY_NEED,
    PLAYBOOK_DYSLEXIA,
    PLAYBOOK_HEARING,
    PLAYBOOK_LOW_VISION,
    PLAYBOOK_TDAH,
    PLAYBOOK_TEA,
    TUTOR_ACCESSIBILITY_PLAYBOOK,
    build_tutor_system_prompt,
    select_playbooks,
)
from ailine_runtime.tutoring.session import (
    create_session,
    load_session,
    save_session,
    tutor_chat_turn,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _use_tmp_store(tmp_path: Any) -> Any:
    """Redirect local store to a temporary directory for all tests."""
    os.environ["AILINE_LOCAL_STORE"] = str(tmp_path / "store")
    yield
    os.environ.pop("AILINE_LOCAL_STORE", None)


def _student_profile_dict() -> dict[str, Any]:
    return {
        "name": "Ana",
        "age": 11,
        "needs": ["autism", "adhd"],
        "strengths": ["visual", "musica"],
        "accommodations": ["pausas frequentes"],
        "language": "pt-BR",
    }


class FakeSettings:
    """Minimal settings-like object for builder tests."""

    executor_model = "fake-llm"
    anthropic_api_key = ""


# ---------------------------------------------------------------------------
# Playbook tests
# ---------------------------------------------------------------------------


class TestPlaybooks:
    """Tests for the accessibility playbooks module."""

    def test_full_playbook_contains_all_sections(self) -> None:
        assert "TEA (autismo)" in TUTOR_ACCESSIBILITY_PLAYBOOK
        assert "TDAH" in TUTOR_ACCESSIBILITY_PLAYBOOK
        assert "dislexia" in TUTOR_ACCESSIBILITY_PLAYBOOK
        assert "auditiva" in TUTOR_ACCESSIBILITY_PLAYBOOK.lower()
        assert "visual" in TUTOR_ACCESSIBILITY_PLAYBOOK.lower()

    def test_individual_playbook_constants(self) -> None:
        assert "TEA" in PLAYBOOK_TEA
        assert "TDAH" in PLAYBOOK_TDAH
        assert "dislexia" in PLAYBOOK_DYSLEXIA.lower()
        assert "auditiva" in PLAYBOOK_HEARING.lower()
        assert "visual" in PLAYBOOK_LOW_VISION.lower()

    def test_select_playbooks_by_needs(self) -> None:
        result = select_playbooks(["autism", "adhd"])
        assert len(result) == 2
        assert PLAYBOOK_TEA in result
        assert PLAYBOOK_TDAH in result

    def test_select_playbooks_deduplication(self) -> None:
        result = select_playbooks(["autism", "tea"])
        # Both map to the same playbook -- should deduplicate
        assert len(result) == 1
        assert PLAYBOOK_TEA in result

    def test_select_playbooks_empty(self) -> None:
        assert select_playbooks([]) == []

    def test_select_playbooks_unknown_need(self) -> None:
        result = select_playbooks(["unknown_need"])
        assert result == []

    def test_select_playbooks_all_known(self) -> None:
        result = select_playbooks(["autism", "adhd", "dyslexia", "hearing", "visual"])
        assert len(result) == 5

    def test_playbook_by_need_mapping(self) -> None:
        assert PLAYBOOK_BY_NEED["autism"] == PLAYBOOK_TEA
        assert PLAYBOOK_BY_NEED["tea"] == PLAYBOOK_TEA
        assert PLAYBOOK_BY_NEED["adhd"] == PLAYBOOK_TDAH
        assert PLAYBOOK_BY_NEED["tdah"] == PLAYBOOK_TDAH
        assert PLAYBOOK_BY_NEED["dyslexia"] == PLAYBOOK_DYSLEXIA
        assert PLAYBOOK_BY_NEED["hearing"] == PLAYBOOK_HEARING
        assert PLAYBOOK_BY_NEED["visual"] == PLAYBOOK_LOW_VISION


# ---------------------------------------------------------------------------
# System prompt builder tests
# ---------------------------------------------------------------------------


class TestBuildTutorSystemPrompt:
    """Tests for the system prompt builder function."""

    def test_prompt_includes_subject_and_grade(self) -> None:
        spec = TutorAgentSpec(
            tutor_id="t1",
            created_at="2026-01-01T00:00:00+00:00",
            teacher_id="teach1",
            subject="Matematica",
            grade="6o ano",
            student_profile=LearnerProfile(name="Ana"),
            materials_scope=TutorMaterialsScope(teacher_id="teach1", subject="Matematica"),
            persona=TutorPersona(system_prompt=""),
        )
        prompt = build_tutor_system_prompt(spec)
        assert "Matematica" in prompt
        assert "6o ano" in prompt

    def test_prompt_includes_student_needs(self) -> None:
        spec = TutorAgentSpec(
            tutor_id="t1",
            created_at="2026-01-01T00:00:00+00:00",
            teacher_id="teach1",
            subject="Ciencias",
            grade="5o ano",
            student_profile=LearnerProfile(
                name="Pedro",
                needs=["autism", "hearing"],
                strengths=["leitura"],
            ),
            materials_scope=TutorMaterialsScope(teacher_id="teach1", subject="Ciencias"),
            persona=TutorPersona(system_prompt=""),
        )
        prompt = build_tutor_system_prompt(spec)
        assert "Pedro" in prompt
        assert "autism" in prompt
        assert "hearing" in prompt
        assert "leitura" in prompt

    def test_prompt_includes_accessibility_playbook(self) -> None:
        spec = TutorAgentSpec(
            tutor_id="t1",
            created_at="2026-01-01T00:00:00+00:00",
            teacher_id="teach1",
            subject="Historia",
            grade="7o ano",
            student_profile=LearnerProfile(name="Maria"),
            materials_scope=TutorMaterialsScope(teacher_id="teach1", subject="Historia"),
            persona=TutorPersona(system_prompt=""),
        )
        prompt = build_tutor_system_prompt(spec)
        # The playbook is embedded in the prompt
        assert "Playbook de Tutoria Inclusiva" in prompt

    def test_prompt_includes_tone_and_style(self) -> None:
        spec = TutorAgentSpec(
            tutor_id="t1",
            created_at="2026-01-01T00:00:00+00:00",
            teacher_id="teach1",
            subject="Portugues",
            grade="4o ano",
            tone="divertido e motivador",
            style="coach",
            student_profile=LearnerProfile(name="Joao"),
            materials_scope=TutorMaterialsScope(teacher_id="teach1", subject="Portugues"),
            persona=TutorPersona(system_prompt=""),
        )
        prompt = build_tutor_system_prompt(spec)
        assert "divertido e motivador" in prompt
        assert "coach" in prompt


# ---------------------------------------------------------------------------
# Builder tests
# ---------------------------------------------------------------------------


class TestCreateTutorAgent:
    """Tests for create_tutor_agent."""

    @pytest.mark.asyncio
    async def test_create_with_deterministic_template(self) -> None:
        spec = await create_tutor_agent(
            cfg=FakeSettings(),
            teacher_id="teacher-001",
            subject="Matematica",
            grade="6o ano",
            student_profile=_student_profile_dict(),
            auto_persona=False,
        )

        assert isinstance(spec, TutorAgentSpec)
        assert spec.teacher_id == "teacher-001"
        assert spec.subject == "Matematica"
        assert spec.grade == "6o ano"
        assert spec.student_profile.name == "Ana"
        assert spec.student_profile.needs == ["autism", "adhd"]
        assert spec.persona.system_prompt != ""
        assert "Matematica" in spec.persona.system_prompt

    @pytest.mark.asyncio
    async def test_create_with_auto_persona_and_fake_llm(self) -> None:
        persona_json = json.dumps(
            {
                "system_prompt": "Voce e um tutor gerado por IA.",
                "notes": ["Gerado automaticamente."],
            }
        )
        llm = FakeChatLLM(responses=[persona_json])

        spec = await create_tutor_agent(
            cfg=FakeSettings(),
            teacher_id="teacher-002",
            subject="Ciencias",
            grade="5o ano",
            student_profile=_student_profile_dict(),
            auto_persona=True,
            llm=llm,
        )

        assert "gerado por IA" in spec.persona.system_prompt
        assert llm._call_count == 1

    @pytest.mark.asyncio
    async def test_create_persists_to_disk(self) -> None:
        spec = await create_tutor_agent(
            cfg=FakeSettings(),
            teacher_id="teacher-003",
            subject="Ingles",
            grade="8o ano",
            student_profile=_student_profile_dict(),
        )

        loaded = load_tutor_spec(spec.tutor_id)
        assert loaded is not None
        assert loaded.tutor_id == spec.tutor_id
        assert loaded.teacher_id == spec.teacher_id
        assert loaded.subject == "Ingles"

    @pytest.mark.asyncio
    async def test_create_with_custom_style_and_tone(self) -> None:
        spec = await create_tutor_agent(
            cfg=FakeSettings(),
            teacher_id="teacher-004",
            subject="Arte",
            grade="3o ano",
            student_profile=_student_profile_dict(),
            style="direct",
            tone="energetico e criativo",
        )

        assert spec.style == "direct"
        assert spec.tone == "energetico e criativo"

    @pytest.mark.asyncio
    async def test_create_with_material_ids_and_tags(self) -> None:
        spec = await create_tutor_agent(
            cfg=FakeSettings(),
            teacher_id="teacher-005",
            subject="Matematica",
            grade="6o ano",
            student_profile=_student_profile_dict(),
            material_ids=["mat-001", "mat-002"],
            tags=["fracoes", "divisao"],
        )

        assert spec.materials_scope.material_ids == ["mat-001", "mat-002"]
        assert spec.materials_scope.tags == ["fracoes", "divisao"]


# ---------------------------------------------------------------------------
# Save/Load spec tests
# ---------------------------------------------------------------------------


class TestSaveLoadSpec:
    """Tests for spec persistence."""

    def test_save_and_load(self) -> None:
        spec = TutorAgentSpec(
            tutor_id="save-test-001",
            created_at="2026-02-12T00:00:00+00:00",
            teacher_id="teach1",
            subject="Geografia",
            grade="9o ano",
            student_profile=LearnerProfile(name="Teste"),
            materials_scope=TutorMaterialsScope(teacher_id="teach1", subject="Geografia"),
            persona=TutorPersona(system_prompt="prompt teste"),
        )

        result = save_tutor_spec(spec)
        assert "tutor_id" in result
        assert result["tutor_id"] == "save-test-001"

        loaded = load_tutor_spec("save-test-001")
        assert loaded is not None
        assert loaded.tutor_id == "save-test-001"
        assert loaded.subject == "Geografia"
        assert loaded.persona.system_prompt == "prompt teste"

    def test_load_nonexistent_returns_none(self) -> None:
        assert load_tutor_spec("nonexistent-id") is None


# ---------------------------------------------------------------------------
# Session tests
# ---------------------------------------------------------------------------


class TestSessionManagement:
    """Tests for session create/save/load."""

    def test_create_session(self) -> None:
        session = create_session("tutor-001")
        assert session.tutor_id == "tutor-001"
        assert session.session_id != ""
        assert len(session.messages) == 0

    def test_save_and_load_session(self) -> None:
        session = create_session("tutor-001")
        session.append("user", "Oi!")
        session.append("assistant", "Ola! Como posso ajudar?")

        save_session(session)
        loaded = load_session(session.session_id)

        assert loaded is not None
        assert loaded.session_id == session.session_id
        assert loaded.tutor_id == "tutor-001"
        assert len(loaded.messages) == 2
        assert loaded.messages[0].role == "user"
        assert loaded.messages[0].content == "Oi!"
        assert loaded.messages[1].role == "assistant"

    def test_load_nonexistent_session_returns_none(self) -> None:
        assert load_session("nonexistent-session") is None

    def test_session_append_timestamps(self) -> None:
        session = create_session("tutor-002")
        session.append("user", "Mensagem 1")
        session.append("assistant", "Resposta 1")

        assert session.messages[0].created_at != ""
        assert session.messages[1].created_at != ""
        # Timestamps should be ISO format
        assert "T" in session.messages[0].created_at


# ---------------------------------------------------------------------------
# Chat turn tests (with FakeLLM)
# ---------------------------------------------------------------------------


class TestTutorChatTurn:
    """Tests for the tutor_chat_turn function."""

    @pytest.mark.asyncio
    async def test_chat_turn_basic(self) -> None:
        # First create and persist a tutor spec
        spec = await create_tutor_agent(
            cfg=FakeSettings(),
            teacher_id="teacher-chat-001",
            subject="Matematica",
            grade="6o ano",
            student_profile=_student_profile_dict(),
        )

        session = create_session(spec.tutor_id)
        save_session(session)

        # Create a valid tutor output for FakeLLM
        tutor_output = json.dumps(
            {
                "answer_markdown": "2+2 e igual a 4.",
                "step_by_step": ["Passo 1"],
                "check_for_understanding": ["Entendeu?"],
                "options_to_respond": ["Sim", "Nao"],
                "citations": [],
                "flags": [],
            }
        )
        llm = FakeChatLLM(responses=[tutor_output])

        result = await tutor_chat_turn(
            cfg=FakeSettings(),
            tutor_id=spec.tutor_id,
            session=session,
            user_message="Quanto e 2+2?",
            llm=llm,
        )

        assert result is not None
        assert "raw_result" in result or "text" in result
        assert result.get("parsed") is not None or result.get("validated") is not None

    @pytest.mark.asyncio
    async def test_chat_turn_persists_session(self) -> None:
        spec = await create_tutor_agent(
            cfg=FakeSettings(),
            teacher_id="teacher-chat-002",
            subject="Historia",
            grade="7o ano",
            student_profile=_student_profile_dict(),
        )

        session = create_session(spec.tutor_id)
        save_session(session)

        tutor_output = json.dumps(
            {
                "answer_markdown": "A Revolucao Francesa foi em 1789.",
                "step_by_step": [],
                "check_for_understanding": [],
                "options_to_respond": [],
                "citations": [],
                "flags": [],
            }
        )
        llm = FakeChatLLM(responses=[tutor_output])

        await tutor_chat_turn(
            cfg=FakeSettings(),
            tutor_id=spec.tutor_id,
            session=session,
            user_message="Quando foi a Revolucao Francesa?",
            llm=llm,
        )

        # Session should have 2 messages (user + assistant)
        loaded = load_session(session.session_id)
        assert loaded is not None
        assert len(loaded.messages) == 2

    @pytest.mark.asyncio
    async def test_chat_turn_nonexistent_tutor_raises(self) -> None:
        session = create_session("nonexistent-tutor")

        with pytest.raises(ValueError, match="TutorAgentSpec not found"):
            await tutor_chat_turn(
                cfg=FakeSettings(),
                tutor_id="nonexistent-tutor",
                session=session,
                user_message="Hello",
            )

    @pytest.mark.asyncio
    async def test_chat_turn_falls_back_to_fake_llm(self) -> None:
        """When no LLM is provided, should fall back to FakeChatLLM."""
        spec = await create_tutor_agent(
            cfg=FakeSettings(),
            teacher_id="teacher-chat-003",
            subject="Ciencias",
            grade="5o ano",
            student_profile=_student_profile_dict(),
        )

        session = create_session(spec.tutor_id)
        save_session(session)

        # Don't pass an LLM -- should use FakeChatLLM internally
        result = await tutor_chat_turn(
            cfg=FakeSettings(),
            tutor_id=spec.tutor_id,
            session=session,
            user_message="O que e fotossintese?",
        )

        assert result is not None
        # FakeLLM produces some response
        assert result.get("text") is not None or result.get("raw_result") is not None
