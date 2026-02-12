"""LangGraph-based tutor chat workflow using Pydantic AI TutorAgent.

Classify -> (RAG | Generate) -> TutorAgent validates output via output_type.
ADR-042: Explicit recursion_limit=25.
ADR-048: No Claude Agent SDK — direct Pydantic AI agent.
"""

from __future__ import annotations

from typing import Any

from ailine_runtime.domain.entities.tutor import TutorTurnOutput
from langgraph.graph import END, StateGraph

from ..agents.tutor import get_tutor_agent
from ..deps import AgentDeps
from ..model_selection.bridge import PydanticAIModelSelector
from ._state import TutorGraphState

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

    async def classify_node(state: TutorGraphState) -> dict[str, str | None]:
        try:
            msg = state.get("user_message", "")
            intent = _classify_intent(msg)
            return {"intent": intent}
        except Exception as exc:
            return {"intent": "question", "error": f"classify_intent failed: {exc}"}

    async def rag_node(state: TutorGraphState) -> dict[str, list[dict[str, Any]] | str | None]:
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
            return {"rag_results": results}
        except Exception as exc:
            return {"rag_results": [], "error": f"rag_search failed: {exc}"}

    async def generate_node(state: TutorGraphState) -> dict[str, dict[str, Any] | str | None]:
        """Use TutorAgent for generation with validated structured output."""
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
            if model_selector:
                # Tutor uses cheap tier for fast responses
                model_override = model_selector.select_model(tier="cheap")

            result = await tutor.run(
                prompt,
                deps=deps,
                **({"model": model_override} if model_override else {}),
            )

            # output_type=TutorTurnOutput means result.output is already validated
            return {
                "validated_output": result.output.model_dump(),
                "error": None,
            }

        except Exception as exc:
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
