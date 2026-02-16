"""Tests for the tutor chat LangGraph workflow."""

from __future__ import annotations

from unittest.mock import patch

from ailine_agents.deps import AgentDeps
from ailine_agents.workflows.tutor_workflow import (
    _build_tutor_prompt,
    _classify_intent,
    build_tutor_workflow,
)


class TestClassifyIntent:
    """_classify_intent() is a rule-based intent classifier (no LLM)."""

    # -- Greetings --
    def test_greeting_oi(self) -> None:
        assert _classify_intent("oi") == "greeting"

    def test_greeting_ola(self) -> None:
        assert _classify_intent("ola") == "greeting"

    def test_greeting_ola_accented(self) -> None:
        assert _classify_intent("olá") == "greeting"

    def test_greeting_bom_dia(self) -> None:
        assert _classify_intent("bom dia") == "greeting"

    def test_greeting_boa_tarde(self) -> None:
        assert _classify_intent("boa tarde") == "greeting"

    def test_greeting_with_exclamation(self) -> None:
        assert _classify_intent("oi!") == "greeting"

    def test_greeting_with_comma_suffix(self) -> None:
        assert _classify_intent("oi, tudo bem?") == "greeting"

    def test_greeting_case_insensitive(self) -> None:
        assert _classify_intent("OI") == "greeting"

    def test_greeting_with_space_suffix(self) -> None:
        assert _classify_intent("hello professor") == "greeting"

    # -- Off-topic --
    def test_offtopic_piada(self) -> None:
        assert _classify_intent("conta uma piada") == "offtopic"

    def test_offtopic_futebol(self) -> None:
        assert _classify_intent("quem ganhou o jogo de futebol?") == "offtopic"

    def test_offtopic_tiktok(self) -> None:
        assert _classify_intent("voce viu no tiktok?") == "offtopic"

    # -- Clarification --
    def test_clarification_nao_entendi(self) -> None:
        assert _classify_intent("nao entendi") == "clarification"

    def test_clarification_pode_explicar(self) -> None:
        assert _classify_intent("pode explicar de novo?") == "clarification"

    def test_clarification_como_assim(self) -> None:
        assert _classify_intent("como assim professor?") == "clarification"

    def test_clarification_repete(self) -> None:
        assert _classify_intent("repete por favor") == "clarification"

    # -- Question (default) --
    def test_question_default(self) -> None:
        assert _classify_intent("quanto e 2 + 2?") == "question"

    def test_question_complex(self) -> None:
        assert (
            _classify_intent("explique como calcular a area de um triangulo")
            == "question"
        )

    def test_question_empty(self) -> None:
        assert _classify_intent("") == "question"


class TestBuildTutorWorkflow:
    """build_tutor_workflow() compiles a LangGraph StateGraph."""

    @patch("ailine_agents.workflows.tutor_workflow.get_tutor_agent")
    def test_compiles_successfully(self, mock_tutor: object) -> None:
        deps = AgentDeps(teacher_id="t-1")
        graph = build_tutor_workflow(deps)
        assert hasattr(graph, "ainvoke")
        assert hasattr(graph, "invoke")

    @patch("ailine_agents.workflows.tutor_workflow.get_tutor_agent")
    def test_graph_has_expected_nodes(self, mock_tutor: object) -> None:
        deps = AgentDeps(teacher_id="t-1")
        graph = build_tutor_workflow(deps)
        node_names = set(graph.get_graph().nodes.keys())
        assert "classify_intent" in node_names
        assert "rag_search" in node_names
        assert "generate_response" in node_names


class TestBuildTutorPrompt:
    """_build_tutor_prompt() formats a contextual prompt for the tutor agent."""

    def test_greeting_intent(self) -> None:
        result = _build_tutor_prompt(
            user_message="oi",
            intent="greeting",
            history=[],
            rag_results=[],
            spec={},
        )
        assert "cumprimentando" in result

    def test_offtopic_intent(self) -> None:
        result = _build_tutor_prompt(
            user_message="conta piada",
            intent="offtopic",
            history=[],
            rag_results=[],
            spec={},
        )
        assert "fora do tema" in result

    def test_clarification_intent(self) -> None:
        result = _build_tutor_prompt(
            user_message="nao entendi",
            intent="clarification",
            history=[],
            rag_results=[],
            spec={},
        )
        assert "esclarecimento" in result

    def test_includes_user_message(self) -> None:
        result = _build_tutor_prompt(
            user_message="quanto e 2+2?",
            intent="question",
            history=[],
            rag_results=[],
            spec={},
        )
        assert "quanto e 2+2?" in result

    def test_includes_rag_results(self) -> None:
        rag = [{"text": "A area do triangulo e base vezes altura dividido por 2."}]
        result = _build_tutor_prompt(
            user_message="como calcular area?",
            intent="question",
            history=[],
            rag_results=rag,
            spec={},
        )
        assert "Material relevante" in result
        assert "triangulo" in result

    def test_includes_history(self) -> None:
        history = [
            {"role": "user", "content": "oi"},
            {"role": "assistant", "content": "Ola! Como posso ajudar?"},
        ]
        result = _build_tutor_prompt(
            user_message="me explica fracoes",
            intent="question",
            history=history,
            rag_results=[],
            spec={},
        )
        assert "Historico" in result
        assert "ALUNO" in result
        assert "TUTOR" in result

    def test_history_truncated_to_8(self) -> None:
        history = [{"role": "user", "content": f"msg-{i}"} for i in range(20)]
        result = _build_tutor_prompt(
            user_message="next question",
            intent="question",
            history=history,
            rag_results=[],
            spec={},
        )
        # Only last 8 messages should appear
        assert "msg-12" in result
        assert "msg-19" in result
        # Earlier messages should not appear
        assert "msg-0" not in result
        assert "msg-11" not in result

    def test_question_intent_no_instruction(self) -> None:
        """question intent does not add a special instruction prefix."""
        result = _build_tutor_prompt(
            user_message="what is 2+2",
            intent="question",
            history=[],
            rag_results=[],
            spec={},
        )
        assert "cumprimentando" not in result
        assert "fora do tema" not in result
        assert "esclarecimento" not in result
