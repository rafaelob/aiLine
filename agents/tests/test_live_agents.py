"""Live API tests for Pydantic AI agents with real LLM backends.

These tests call REAL external APIs. They are excluded from CI by default
(ADR-051) and must be run manually with:

    uv run pytest tests/test_live_agents.py -m live_llm -v

Environment variables required (loaded from .env):
    ANTHROPIC_API_KEY   - Anthropic platform key
    OPENAI_API_KEY      - OpenAI platform key (optional)
    GEMINI_API_KEY      - Gemini key (optional)

Tests use cheaper models (Haiku/Flash) to minimize cost.
"""

from __future__ import annotations

import os

import pytest

from ailine_agents.agents.executor import build_executor_agent
from ailine_agents.agents.planner import build_planner_agent
from ailine_agents.agents.quality_gate import build_quality_gate_agent
from ailine_agents.agents.tutor import build_tutor_agent
from ailine_agents.deps import AgentDeps
from ailine_agents.models import ExecutorResult, QualityAssessment

# ---------------------------------------------------------------------------
# Availability flags
# ---------------------------------------------------------------------------

_HAS_ANTHROPIC = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
_HAS_OPENAI = bool(os.environ.get("OPENAI_API_KEY", "").strip())
_HAS_GEMINI = bool(os.environ.get("GEMINI_API_KEY", "").strip())

skip_no_anthropic = pytest.mark.skipif(not _HAS_ANTHROPIC, reason="ANTHROPIC_API_KEY not set")
skip_no_openai = pytest.mark.skipif(not _HAS_OPENAI, reason="OPENAI_API_KEY not set")
skip_no_gemini = pytest.mark.skipif(not _HAS_GEMINI, reason="GEMINI_API_KEY not set")

# Cheap models for testing
_ANTHROPIC_CHEAP = "anthropic:claude-haiku-4-5-20251001"
_OPENAI_CHEAP = "openai:gpt-4o-mini"
_GEMINI_CHEAP = "google-gla:gemini-2.0-flash"


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def live_deps() -> AgentDeps:
    """AgentDeps for live tests."""
    return AgentDeps(
        teacher_id="live-teacher",
        run_id="live-run-001",
        subject="Matematica",
    )


# =========================================================================
# QualityGateAgent — simplest output type, best for cross-provider testing
# =========================================================================


@pytest.mark.live_llm
@skip_no_anthropic
class TestQualityGateAnthropicLive:
    """QualityGateAgent with real Anthropic API (Haiku)."""

    def test_produces_quality_assessment(self, allow_model_requests, live_deps):
        agent = build_quality_gate_agent()
        result = agent.run_sync(
            "Avalie este plano de aula: Título: Frações para 5o ano. "
            "Objetivos: EF05MA03 - Comparar frações. "
            "Passos: 1) Introdução 15min 2) Atividade 20min 3) Avaliação 10min.",
            deps=live_deps,
            model=_ANTHROPIC_CHEAP,
        )
        assert isinstance(result.output, QualityAssessment)
        assert 0 <= result.output.score <= 100
        assert result.output.status in ("accept", "refine-if-budget", "must-refine")

    def test_quality_gate_has_checklist(self, allow_model_requests, live_deps):
        agent = build_quality_gate_agent()
        result = agent.run_sync(
            "Avalie: plano simples sem objetivos claros nem etapas detalhadas. "
            "Tema: ciencias, 3o ano. Sem adaptações de acessibilidade.",
            deps=live_deps,
            model=_ANTHROPIC_CHEAP,
        )
        qa = result.output
        assert isinstance(qa, QualityAssessment)
        # A bad plan should get a lower score or recommendations
        assert qa.score < 90 or len(qa.recommendations) > 0 or len(qa.warnings) > 0


@pytest.mark.live_llm
@skip_no_openai
class TestQualityGateOpenAILive:
    """QualityGateAgent with real OpenAI API (gpt-4o-mini)."""

    def test_produces_quality_assessment(self, allow_model_requests, live_deps):
        agent = build_quality_gate_agent()
        result = agent.run_sync(
            "Avalie este plano: Título: Ecossistemas. Grade: 7o ano. "
            "Objetivos: Compreender cadeia alimentar. "
            "Passos: 1) Explicação 20min 2) Dinâmica 15min.",
            deps=live_deps,
            model=_OPENAI_CHEAP,
        )
        assert isinstance(result.output, QualityAssessment)
        assert 0 <= result.output.score <= 100


@pytest.mark.live_llm
@skip_no_gemini
class TestQualityGateGeminiLive:
    """QualityGateAgent with real Gemini API (Flash)."""

    def test_produces_quality_assessment(self, allow_model_requests, live_deps):
        agent = build_quality_gate_agent()
        result = agent.run_sync(
            "Avalie este plano: Título: Poesia brasileira. Grade: 8o ano. "
            "Objetivos: Identificar figuras de linguagem. "
            "Passos: 1) Leitura 15min 2) Análise 20min 3) Produção 15min.",
            deps=live_deps,
            model=_GEMINI_CHEAP,
        )
        assert isinstance(result.output, QualityAssessment)
        assert 0 <= result.output.score <= 100


# =========================================================================
# TutorAgent — structured tutoring output
# =========================================================================


@pytest.mark.live_llm
@skip_no_anthropic
class TestTutorAgentAnthropicLive:
    """TutorAgent with real Anthropic API."""

    def test_produces_tutor_turn_output(self, allow_model_requests, live_deps):
        from ailine_runtime.domain.entities.tutor import TutorTurnOutput

        agent = build_tutor_agent()
        result = agent.run_sync(
            "Oi professor! Não entendi frações. O que é 1/2?",
            deps=live_deps,
            model=_ANTHROPIC_CHEAP,
        )
        assert isinstance(result.output, TutorTurnOutput)
        assert len(result.output.answer_markdown) > 0

    def test_tutor_provides_check_for_understanding(self, allow_model_requests, live_deps):
        from ailine_runtime.domain.entities.tutor import TutorTurnOutput

        agent = build_tutor_agent()
        result = agent.run_sync(
            "Acho que 2/4 é maior que 1/2, certo?",
            deps=live_deps,
            model=_ANTHROPIC_CHEAP,
        )
        output = result.output
        assert isinstance(output, TutorTurnOutput)
        assert len(output.answer_markdown) > 10


# =========================================================================
# ExecutorAgent — plan finalization output
# =========================================================================


@pytest.mark.live_llm
@skip_no_anthropic
class TestExecutorAgentAnthropicLive:
    """ExecutorAgent with real Anthropic API."""

    def test_produces_executor_result(self, allow_model_requests, live_deps):
        agent = build_executor_agent()
        result = agent.run_sync(
            "Finalize este plano de Matemática para 5o ano sobre frações. "
            "O plano já foi validado com score 85. "
            "Gere plan_id='live-test-001', inclua relatório de acessibilidade básico, "
            "e summary_bullets com 2-3 pontos.",
            deps=live_deps,
            model=_ANTHROPIC_CHEAP,
        )
        assert isinstance(result.output, ExecutorResult)
        assert isinstance(result.output.plan_json, dict)


# =========================================================================
# PlannerAgent — complex structured output (StudyPlanDraft)
# =========================================================================


@pytest.mark.live_llm
@skip_no_anthropic
class TestPlannerAgentAnthropicLive:
    """PlannerAgent with real Anthropic API (most complex output type)."""

    def test_produces_study_plan_draft(self, allow_model_requests, live_deps):
        from ailine_runtime.domain.entities.plan import StudyPlanDraft

        agent = build_planner_agent()
        result = agent.run_sync(
            "Crie um plano de estudo de Matemática para 5o ano sobre frações. "
            "Padrão BNCC. Inclua 3 passos de aula com tempos. "
            "Objetivos: EF05MA03 - Comparar e ordenar frações.",
            deps=live_deps,
            model=_ANTHROPIC_CHEAP,
        )
        assert isinstance(result.output, StudyPlanDraft)
        assert len(result.output.title) > 0
        assert len(result.output.objectives) >= 1
        assert len(result.output.steps) >= 1
        # Verify steps have proper structure
        for step in result.output.steps:
            assert step.minutes >= 1
            assert len(step.title) > 0
            assert len(step.instructions) >= 1


# =========================================================================
# Cross-provider consistency
# =========================================================================


@pytest.mark.live_llm
class TestCrossProviderAgentConsistency:
    """Verify that agents produce valid structured output across providers."""

    @staticmethod
    def _available_models() -> list[tuple[str, str]]:
        models = []
        if _HAS_ANTHROPIC:
            models.append(("anthropic", _ANTHROPIC_CHEAP))
        if _HAS_OPENAI:
            models.append(("openai", _OPENAI_CHEAP))
        if _HAS_GEMINI:
            models.append(("gemini", _GEMINI_CHEAP))
        return models

    def test_quality_gate_consistent_across_providers(
        self, allow_model_requests, live_deps
    ):
        models = self._available_models()
        if len(models) < 2:
            pytest.skip("Need at least 2 providers for cross-provider test")

        agent = build_quality_gate_agent()
        prompt = (
            "Avalie: Título: Sistema Solar, 6o ano. "
            "Objetivos: Identificar planetas. "
            "Passos: 1) Vídeo 10min 2) Quiz 15min 3) Maquete 25min."
        )
        for name, model in models:
            result = agent.run_sync(prompt, deps=live_deps, model=model)
            assert isinstance(result.output, QualityAssessment), (
                f"{name}: expected QualityAssessment, got {type(result.output)}"
            )
            assert 0 <= result.output.score <= 100, (
                f"{name}: score {result.output.score} out of range"
            )


# =========================================================================
# Model selection bridge — end-to-end
# =========================================================================


@pytest.mark.live_llm
@skip_no_anthropic
class TestModelSelectionBridgeLive:
    """Verify the model selection bridge builds working models."""

    def test_anthropic_model_works_with_agent(self, allow_model_requests, live_deps):
        """Use the model string format that Pydantic AI expects."""
        agent = build_quality_gate_agent()
        result = agent.run_sync(
            "Avalie: plano básico de história, 4o ano.",
            deps=live_deps,
            model=_ANTHROPIC_CHEAP,
        )
        assert isinstance(result.output, QualityAssessment)
