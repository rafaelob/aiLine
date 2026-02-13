"""Fake ChatLLM adapter for testing and CI.

Returns deterministic responses without calling any external API.
Used when no API keys are configured (ADR-051).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from ...domain.ports.llm import WebSearchResult, WebSearchSource


class FakeChatLLM:
    """ChatLLM implementation that returns canned responses for testing.

    Supports two response modes:
      1. **Ordered list** (``responses=["a", "b"]``): cycles through in order.
      2. **Keyword mapping** (``response_map={"plan": "...", "refine": "..."}``):
         selects response by matching keywords in the last user message.
         Falls through to ordered list if no keyword matches.
    """

    def __init__(
        self,
        *,
        model: str = "fake-llm",
        responses: list[str] | None = None,
        response_map: dict[str, str] | None = None,
    ) -> None:
        self._model = model
        self._responses = responses or []
        self._response_map = response_map or {}
        self._call_count = 0

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def capabilities(self) -> dict[str, Any]:
        return {
            "provider": "fake",
            "streaming": True,
            "tool_use": False,
            "vision": False,
            "web_search": True,
        }

    @staticmethod
    def _last_user_content(messages: list[dict[str, Any]]) -> str:
        """Extract the content of the last user message."""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return str(msg.get("content", ""))[:100]
        return ""

    def _next_response(self, messages: list[dict[str, Any]]) -> str:
        """Return the next canned response, or generate a deterministic one.

        Priority: response_map keyword match > ordered responses list > deterministic JSON.
        """
        # Try keyword-based response map first
        if self._response_map:
            last_user = self._last_user_content(messages)
            lower = last_user.lower()
            for keyword, mapped_response in self._response_map.items():
                if keyword.lower() in lower:
                    self._call_count += 1
                    return mapped_response

        if self._responses:
            response = self._responses[self._call_count % len(self._responses)]
        else:
            # Generate a deterministic JSON response based on the last user message
            last_user = self._last_user_content(messages)
            response = json.dumps(
                {
                    "title": f"Plano de Aula — {last_user[:50]}",
                    "grade": "6o ano",
                    "standard": "BNCC",
                    "objectives": [
                        {"id": "EF06MA01", "text": "Objetivo de aprendizagem gerado para teste."}
                    ],
                    "steps": [
                        {
                            "minutes": 15,
                            "title": "Introdução",
                            "instructions": ["Apresentar o tema.", "Ativar conhecimentos prévios."],
                            "activities": ["Discussão em grupo."],
                            "assessment": ["Verificar compreensão inicial."],
                        },
                        {
                            "minutes": 25,
                            "title": "Desenvolvimento",
                            "instructions": ["Explicar conceito.", "Praticar com exercícios."],
                            "activities": ["Exercício individual."],
                            "assessment": ["Checagem rápida."],
                        },
                        {
                            "minutes": 10,
                            "title": "Fechamento",
                            "instructions": ["Resumir aprendizados.", "Tarefa para casa."],
                            "activities": [],
                            "assessment": ["Autoavaliação."],
                        },
                    ],
                    "student_plan": {
                        "summary": ["Hoje vamos aprender sobre o tema proposto."],
                        "steps": [
                            {
                                "minutes": 15,
                                "title": "Introdução",
                                "instructions": ["Vamos começar conversando sobre o tema."],
                                "check_for_understanding": ["O que você já sabe sobre isso?"],
                                "self_regulation_prompts": [],
                            }
                        ],
                        "glossary": ["termo: definição simples"],
                        "alternative_response_options": ["Pode desenhar ou responder oralmente."],
                    },
                    "accessibility_pack_draft": {
                        "applied_adaptations": [],
                        "media_requirements": [],
                        "ui_recommendations": ["Usar fonte legível."],
                        "visual_schedule_notes": [],
                        "teacher_review_points": [],
                        "human_review_required": False,
                        "human_review_reasons": [],
                    },
                    "evidence_requests": [],
                },
                ensure_ascii=False,
            )
        self._call_count += 1
        return response

    async def generate(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str:
        return self._next_response(messages)

    async def stream(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        response = self._next_response(messages)
        # Simulate streaming by yielding chunks
        chunk_size = 50
        for i in range(0, len(response), chunk_size):
            yield response[i : i + chunk_size]

    async def generate_with_search(
        self,
        query: str,
        *,
        max_results: int = 5,
        **kwargs: Any,
    ) -> WebSearchResult:
        """Return deterministic fake web search results."""
        return WebSearchResult(
            text=f"Resultado de pesquisa para: {query}. "
            "De acordo com fontes educacionais, este é um tópico relevante "
            "para o contexto de aprendizagem inclusiva.",
            sources=[
                WebSearchSource(
                    url="https://example.com/education/article-1",
                    title="Artigo Educacional Relevante",
                    snippet="Trecho relevante sobre o tema pesquisado.",
                ),
                WebSearchSource(
                    url="https://example.com/education/article-2",
                    title="Recurso Pedagógico Complementar",
                    snippet="Informações complementares sobre práticas inclusivas.",
                ),
            ],
        )
