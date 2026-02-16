"""Extended tests for tutoring.builder -- covers auto_persona and edge cases."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ailine_runtime.tutoring.builder import (
    _generate_persona_with_llm,
    create_tutor_agent,
    load_tutor_spec,
)


class TestGeneratePersonaWithLLM:
    @pytest.mark.asyncio
    async def test_valid_json_response(self):
        llm = AsyncMock()
        llm.generate = AsyncMock(
            return_value='{"system_prompt": "Be helpful.", "notes": ["note1"]}'
        )
        persona = await _generate_persona_with_llm(llm, "Create a tutor")
        assert persona.system_prompt == "Be helpful."
        assert "note1" in persona.notes

    @pytest.mark.asyncio
    async def test_json_embedded_in_text(self):
        llm = AsyncMock()
        llm.generate = AsyncMock(
            return_value='Here is the result: {"system_prompt": "Embedded.", "notes": []} done.'
        )
        persona = await _generate_persona_with_llm(llm, "Create a tutor")
        assert persona.system_prompt == "Embedded."

    @pytest.mark.asyncio
    async def test_plain_text_response(self):
        llm = AsyncMock()
        llm.generate = AsyncMock(
            return_value="Just a plain text system prompt without JSON."
        )
        persona = await _generate_persona_with_llm(llm, "Create a tutor")
        assert persona.system_prompt == "Just a plain text system prompt without JSON."
        assert persona.notes == []

    @pytest.mark.asyncio
    async def test_invalid_json_with_braces(self):
        llm = AsyncMock()
        llm.generate = AsyncMock(return_value="Some {invalid json} here")
        persona = await _generate_persona_with_llm(llm, "Create a tutor")
        assert persona.system_prompt == "Some {invalid json} here"


class TestCreateTutorAgentAutoPersona:
    @pytest.mark.asyncio
    async def test_auto_persona(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(tmp_path))

        llm = AsyncMock()
        llm.generate = AsyncMock(
            return_value='{"system_prompt": "AI generated prompt.", "notes": ["adaptive"]}'
        )

        spec = await create_tutor_agent(
            cfg=None,
            teacher_id="t1",
            subject="Math",
            grade="4",
            student_profile={"name": "Aluno Teste", "needs": [], "strengths": []},
            auto_persona=True,
            llm=llm,
        )

        assert spec.persona.system_prompt == "AI generated prompt."
        llm.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_persona_without_llm_falls_back(self, tmp_path, monkeypatch):
        """auto_persona=True but llm=None -> uses deterministic template."""
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(tmp_path))

        spec = await create_tutor_agent(
            cfg=None,
            teacher_id="t1",
            subject="Math",
            grade="4",
            student_profile={"name": "Aluno Teste", "needs": [], "strengths": []},
            auto_persona=True,
            llm=None,
        )

        # Should have the deterministic template
        assert spec.persona.system_prompt != ""
        assert (
            "Math" in spec.persona.system_prompt
            or "Tutor" in spec.persona.system_prompt
        )


class TestLoadTutorSpec:
    def test_load_corrupted_file(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(tmp_path))
        tutors_dir = tmp_path / "tutors"
        tutors_dir.mkdir()
        (tutors_dir / "bad-id.json").write_text("not json", encoding="utf-8")
        result = load_tutor_spec("bad-id")
        assert result is None
