"""LangGraph-based tutor chat workflow using Pydantic AI TutorAgent.

Classify -> (RAG | Generate) -> TutorAgent validates output via output_type.
ADR-042: Explicit recursion_limit=25.
ADR-048: No Claude Agent SDK -- direct Pydantic AI agent.

Resilience features:
- Retry with exponential backoff on transient LLM errors.
- Circuit breaker prevents cascading failures.
- Workflow timeout aborts gracefully after max_workflow_duration_seconds.
- Structured logging with run_id, stage, model, and duration.
"""

from __future__ import annotations

import time
from typing import Any

import structlog
from ailine_runtime.domain.entities.tutor import TutorTurnOutput
from ailine_runtime.shared.observability import log_event, log_pipeline_stage
from langgraph.graph import END, StateGraph

from ..agents.tutor import get_tutor_agent
from ..deps import AgentDeps
from ..model_selection.bridge import PydanticAIModelSelector
from ..resilience import CircuitOpenError
from ._retry import with_retry
from ._state import TutorGraphState

log = structlog.get_logger(__name__)

# Intent classification (rule-based, no LLM call)

_GREETINGS = frozenset([
    "oi", "ola", "olá", "hello", "hi", "hey",
    "bom dia", "boa tarde", "boa noite",
    "e aí", "e ai", "tudo bem",
])

_OFFTOPIC_MARKERS = frozenset([
    "piada", "joke", "meme", "futebol", "jogo",
    "namorada", "namorado", "tiktok", "instagram",
])


def _classify_intent(message: str) -> str:
    """Rule-based intent classifier (fast, no LLM call)."""
    msg = message.lower().strip()

    for g in _GREETINGS:
        if msg == g or msg.startswith(g + " ") or msg.startswith(g + ","):
            return "greeting"
        if msg.startswith(g + "!") or msg.startswith(g + "."):
            return "greeting"

    for marker in _OFFTOPIC_MARKERS:
        if marker in msg:
            return "offtopic"

    clarification_signals = [
        "não entendi", "nao entendi", "pode explicar",
        "como assim", "o que é", "o que e",
        "repete", "de novo", "mais uma vez",
    ]
    for signal in clarification_signals:
        if signal in msg:
            return "clarification"

    return "question"


def build_tutor_workflow(
    deps: AgentDeps,
    *,
    rag_service: Any = None,
    model_selector: PydanticAIModelSelector | None = None,
) -> Any:
    """Build and compile the tutor LangGraph workflow.

    Args:
        deps: AgentDeps (from AgentDepsFactory).
        rag_service: Optional RAG service (must have async search()).
        model_selector: Optional SmartRouter -> Pydantic AI model bridge.

    Returns:
        Compiled LangGraph CompiledStateGraph.
    """
    graph = StateGraph(TutorGraphState)
    tutor = get_tutor_agent()

    async def classify_node(state: TutorGraphState) -> dict[str, Any]:
        try:
            msg = state.get("user_message", "")
            intent = _classify_intent(msg)

            # Set started_at for timeout tracking
            updates: dict[str, Any] = {"intent": intent}
            if state.get("started_at") is None:
                updates["started_at"] = time.monotonic()

            return updates
        except Exception as exc:
            return {
                "intent": "question",
                "error": f"classify_intent failed: {exc}",
                "started_at": time.monotonic(),
            }

    async def rag_node(state: TutorGraphState) -> dict[str, list[dict[str, Any]] | str | None]:
        stage_start = time.monotonic()
        session_id = state.get("session_id", "")

        try:
            if rag_service is None:
                return {"rag_results": []}

            intent = state.get("intent", "question")
            if intent not in ("question", "clarification"):
                return {"rag_results": []}

            spec = state.get("spec") or {}
            materials_scope = spec.get("materials_scope") or {}

            results = await rag_service.search(
                query=state.get("user_message", ""),
                teacher_id=materials_scope.get("teacher_id"),
                subject=materials_scope.get("subject") or spec.get("subject"),
                k=3,
            )

            duration_ms = (time.monotonic() - stage_start) * 1000
            log_event(
                "tutor.rag_search.complete",
                session_id=session_id,
                stage="rag_search",
                results_count=len(results),
                duration_ms=round(duration_ms, 2),
            )
            return {"rag_results": results}
        except Exception as exc:
            duration_ms = (time.monotonic() - stage_start) * 1000
            log_event(
                "tutor.rag_search.failed",
                session_id=session_id,
                stage="rag_search",
                error=str(exc),
                duration_ms=round(duration_ms, 2),
            )
            return {"rag_results": [], "error": f"rag_search failed: {exc}"}

    async def generate_node(state: TutorGraphState) -> dict[str, dict[str, Any] | str | None]:
        """Use TutorAgent for generation with validated structured output."""
        session_id = state.get("session_id", "")
        stage_start = time.monotonic()

        # Check timeout
        started_at = state.get("started_at")
        if started_at is not None:
            elapsed = time.monotonic() - started_at
            if elapsed > deps.max_workflow_duration_seconds:
                log.error(
                    "tutor.workflow.timeout",
                    session_id=session_id,
                    stage="generate",
                    elapsed_seconds=round(elapsed, 1),
                    limit_seconds=deps.max_workflow_duration_seconds,
                )
                fallback = TutorTurnOutput(
                    answer_markdown="Desculpe, o tempo limite foi atingido. Tente novamente.",
                    step_by_step=[],
                    check_for_understanding=[],
                    options_to_respond=[],
                    citations=[],
                    flags=["timeout_error"],
                )
                return {
                    "validated_output": fallback.model_dump(),
                    "error": f"Workflow timeout after {elapsed:.1f}s",
                }

        # Check circuit breaker
        if not deps.circuit_breaker.check():
            log_event("tutor.circuit_open", session_id=session_id)
            fallback = TutorTurnOutput(
                answer_markdown=(
                    "Desculpe, o servico esta temporariamente indisponivel. "
                    "Tente novamente em alguns instantes."
                ),
                step_by_step=[],
                check_for_understanding=[],
                options_to_respond=[],
                citations=[],
                flags=["circuit_open"],
            )
            return {
                "validated_output": fallback.model_dump(),
                "error": "Circuit breaker open",
            }

        try:
            spec = state.get("spec") or {}
            history = state.get("history") or []
            rag_results = state.get("rag_results") or []
            intent = state.get("intent", "question")

            prompt = _build_tutor_prompt(
                user_message=state.get("user_message", ""),
                intent=intent,
                history=history,
                rag_results=rag_results,
                spec=spec,
            )

            model_override = None
            model_name = "default"
            if model_selector:
                # Tutor uses cheap tier for fast responses
                model_override = model_selector.select_model(tier="cheap")
                model_name = str(model_override) if model_override else "default"

            async def _run_tutor():
                return await tutor.run(
                    prompt,
                    deps=deps,
                    **({"model": model_override} if model_override else {}),
                )

            result = await with_retry(
                _run_tutor,
                max_attempts=3,
                initial_delay=1.0,
                backoff_factor=2.0,
                operation_name="tutor.run",
                run_id=session_id,
            )

            deps.circuit_breaker.record_success()

            duration_ms = (time.monotonic() - stage_start) * 1000
            log_event(
                "tutor.generate.complete",
                session_id=session_id,
                stage="generate",
                model=model_name,
                intent=intent,
                duration_ms=round(duration_ms, 2),
            )
            log_pipeline_stage(
                stage="tutor_generate",
                run_id=session_id,
                duration_ms=duration_ms,
                status="success",
                metadata={"model": model_name, "intent": intent},
            )

            # output_type=TutorTurnOutput means result.output is already validated
            return {
                "validated_output": result.output.model_dump(),
                "error": None,
            }

        except CircuitOpenError:
            fallback = TutorTurnOutput(
                answer_markdown="Desculpe, o servico esta temporariamente indisponivel.",
                step_by_step=[],
                check_for_understanding=[],
                options_to_respond=[],
                citations=[],
                flags=["circuit_open"],
            )
            return {
                "validated_output": fallback.model_dump(),
                "error": "Circuit breaker opened during call",
            }
        except Exception as exc:
            deps.circuit_breaker.record_failure()
            duration_ms = (time.monotonic() - stage_start) * 1000
            log_event(
                "tutor.generate.failed",
                session_id=session_id,
                stage="generate",
                error=str(exc),
                duration_ms=round(duration_ms, 2),
            )
            log_pipeline_stage(
                stage="tutor_generate",
                run_id=session_id,
                duration_ms=duration_ms,
                status="failed",
                metadata={"error": str(exc)},
            )
            # Fallback: return error in state
            fallback = TutorTurnOutput(
                answer_markdown=f"Desculpe, ocorreu um erro. Tente novamente. ({exc})",
                step_by_step=[],
                check_for_understanding=[],
                options_to_respond=[],
                citations=[],
                flags=["generation_error"],
            )
            return {
                "validated_output": fallback.model_dump(),
                "error": f"generate_response failed: {exc}",
            }

    def route_after_intent(state: TutorGraphState) -> str:
        intent = state.get("intent", "question")
        if intent in ("question", "clarification"):
            return "rag_search"
        return "generate_response"

    graph.add_node("classify_intent", classify_node)
    graph.add_node("rag_search", rag_node)
    graph.add_node("generate_response", generate_node)

    graph.set_entry_point("classify_intent")
    graph.add_conditional_edges(
        "classify_intent",
        route_after_intent,
        {"rag_search": "rag_search", "generate_response": "generate_response"},
    )
    graph.add_edge("rag_search", "generate_response")
    graph.add_edge("generate_response", END)

    return graph.compile()


async def run_tutor_turn(
    *,
    workflow: Any,
    tutor_id: str,
    session_id: str,
    user_message: str,
    history: list[dict[str, Any]],
    spec: dict[str, Any],
) -> dict[str, Any]:
    """Run a single tutor turn through the compiled workflow.

    Enforces recursion_limit=25 per ADR-042.
    """
    initial_state: TutorGraphState = {
        "tutor_id": tutor_id,
        "session_id": session_id,
        "user_message": user_message,
        "history": history,
        "spec": spec,
        "intent": "",
        "rag_results": [],
        "response": "",
        "validated_output": None,
        "error": None,
    }

    result = await workflow.ainvoke(
        initial_state,
        config={"recursion_limit": 25},
    )
    return dict(result)


def _build_tutor_prompt(
    user_message: str,
    intent: str,
    history: list[dict[str, Any]],
    rag_results: list[dict[str, Any]],
    spec: dict[str, Any],
) -> str:
    """Build contextual prompt for the TutorAgent."""
    parts: list[str] = []

    # Intent instruction
    if intent == "greeting":
        parts.append("O aluno esta cumprimentando. Responda acolhedoramente e pergunte como ajudar.")
    elif intent == "offtopic":
        parts.append("O aluno fez pergunta fora do tema. Redirecione gentilmente.")
    elif intent == "clarification":
        parts.append("O aluno pediu esclarecimento. Explique de forma diferente, com exemplos.")

    # RAG context
    if rag_results:
        parts.append("\n## Material relevante")
        for r in rag_results:
            text = r.get("text", "")[:300]
            parts.append(f"- {text}")

    # History
    history_entries = (history or [])[-8:]
    if history_entries:
        parts.append("\n## Historico")
        for m in history_entries:
            role_label = "ALUNO" if m.get("role") == "user" else "TUTOR"
            parts.append(f"{role_label}: {m.get('content', '')}")

    # Current message
    parts.append(f"\n## Pergunta atual\n{user_message}")

    return "\n".join(parts)
