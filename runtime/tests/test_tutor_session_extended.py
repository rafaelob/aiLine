"""Extended tests for tutoring.session -- covers edge cases."""

from __future__ import annotations

import pytest

from ailine_runtime.tutoring.session import (
    _extract_json,
    _format_history,
    create_session,
    load_session,
    save_session,
    tutor_chat_turn,
)


class TestExtractJson:
    def test_valid_json(self):
        result = _extract_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_embedded_in_text(self):
        result = _extract_json('Here is the result: {"key": "value"} end.')
        assert result == {"key": "value"}

    def test_no_json(self):
        result = _extract_json("Just plain text with no braces")
        assert result is None

    def test_invalid_json_with_braces(self):
        result = _extract_json("Some {invalid json} here")
        assert result is None

    def test_whitespace(self):
        result = _extract_json('  {"k": 1}  ')
        assert result == {"k": 1}


class TestFormatHistory:
    def test_empty_session(self):
        session = create_session("tutor-1")
        result = _format_history(session)
        assert result == ""

    def test_history_with_messages(self):
        session = create_session("tutor-1")
        session.append("user", "Ola")
        session.append("assistant", "Oi, como posso ajudar?")
        result = _format_history(session)
        assert "ALUNO: Ola" in result
        assert "TUTOR: Oi, como posso ajudar?" in result

    def test_max_turns_truncation(self):
        session = create_session("tutor-1")
        for i in range(20):
            session.append("user", f"msg {i}")
        result = _format_history(session, max_turns=3)
        lines = [line for line in result.strip().split("\n") if line.strip()]
        assert len(lines) == 3


class TestSessionPersistence:
    def test_save_and_load(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(tmp_path))
        session = create_session("tutor-1")
        session.append("user", "Hello")
        save_session(session)

        loaded = load_session(session.session_id)
        assert loaded is not None
        assert loaded.session_id == session.session_id
        assert len(loaded.messages) == 1

    def test_load_nonexistent(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(tmp_path))
        result = load_session("nonexistent-id")
        assert result is None

    def test_load_corrupted(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(tmp_path))
        sessions_dir = tmp_path / "tutor_sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "bad.json").write_text("not json", encoding="utf-8")
        result = load_session("bad")
        assert result is None


class TestTutorChatTurn:
    @pytest.mark.asyncio
    async def test_tutor_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(tmp_path))
        session = create_session("nonexistent-tutor")
        with pytest.raises(ValueError, match="not found"):
            await tutor_chat_turn(
                cfg=None,
                tutor_id="nonexistent-tutor",
                session=session,
                user_message="Hello",
            )

    @pytest.mark.asyncio
    async def test_chat_turn_with_fake_llm(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(tmp_path))

        # Create a tutor spec
        from ailine_runtime.tutoring.builder import create_tutor_agent

        spec = await create_tutor_agent(
            cfg=None,
            teacher_id="t1",
            subject="Math",
            grade="4",
            student_profile={"name": "Aluno Teste", "needs": [], "strengths": []},
        )

        # Create a session
        session = create_session(spec.tutor_id)

        # Run a chat turn with explicit FakeLLM
        from ailine_runtime.adapters.llm.fake_llm import FakeChatLLM

        fake_llm = FakeChatLLM()
        result = await tutor_chat_turn(
            cfg=None,
            tutor_id=spec.tutor_id,
            session=session,
            user_message="What are fractions?",
            llm=fake_llm,
        )

        assert "text" in result
        assert "session_id" in result
        assert result["session_id"] == session.session_id

    @pytest.mark.asyncio
    async def test_chat_turn_uses_container_llm(self, tmp_path, monkeypatch):
        """When cfg._container has an llm attribute, it is used (line 105)."""
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(tmp_path))

        from ailine_runtime.adapters.llm.fake_llm import FakeChatLLM
        from ailine_runtime.tutoring.builder import create_tutor_agent

        spec = await create_tutor_agent(
            cfg=None,
            teacher_id="t1",
            subject="Math",
            grade="4",
            student_profile={"name": "Aluno Teste", "needs": [], "strengths": []},
        )

        session = create_session(spec.tutor_id)

        from unittest.mock import MagicMock
        container_llm = FakeChatLLM(model="container-llm")
        container = MagicMock()
        container.llm = container_llm

        cfg = MagicMock()
        cfg.executor_model = "anthropic:claude-opus-4-6"
        cfg._container = container

        result = await tutor_chat_turn(
            cfg=cfg,
            tutor_id=spec.tutor_id,
            session=session,
            user_message="Hello",
        )
        assert result["session_id"] == session.session_id
        # Verify the container's llm was actually used
        assert container_llm._call_count == 1

    @pytest.mark.asyncio
    async def test_chat_turn_fallback_to_fake_llm(self, tmp_path, monkeypatch):
        """When no LLM is provided and cfg has no container, fall back to FakeLLM."""
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(tmp_path))

        from ailine_runtime.tutoring.builder import create_tutor_agent

        spec = await create_tutor_agent(
            cfg=None,
            teacher_id="t1",
            subject="Math",
            grade="4",
            student_profile={"name": "Aluno Teste", "needs": [], "strengths": []},
        )

        session = create_session(spec.tutor_id)

        # Pass a simple mock cfg with no container
        from unittest.mock import MagicMock
        cfg = MagicMock()
        cfg.executor_model = "anthropic:claude-opus-4-6"
        cfg._container = None

        result = await tutor_chat_turn(
            cfg=cfg,
            tutor_id=spec.tutor_id,
            session=session,
            user_message="Hello",
        )
        assert result["session_id"] == session.session_id
