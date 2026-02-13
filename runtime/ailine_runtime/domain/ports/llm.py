"""Port: LLM chat providers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class WebSearchSource:
    """A single source returned by a web search."""

    url: str
    title: str
    snippet: str = ""


@dataclass(frozen=True)
class WebSearchResult:
    """Result of a web-search-augmented generation."""

    text: str
    sources: list[WebSearchSource] = field(default_factory=list)


@runtime_checkable
class ChatLLM(Protocol):
    """Protocol for LLM chat providers.

    All adapters must match these signatures exactly.
    """

    @property
    def model_name(self) -> str: ...

    @property
    def capabilities(self) -> dict[str, Any]:
        """Feature detection: provider, streaming, vision, tool_use, web_search, etc."""
        ...  # pragma: no cover

    async def generate(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str: ...

    def stream(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[str]: ...

    async def generate_with_search(
        self,
        query: str,
        *,
        max_results: int = 5,
        **kwargs: Any,
    ) -> WebSearchResult:
        """Generate a response augmented with real-time web search.

        Each provider implements this using its native web search tool:
        - Anthropic: web_search_20250305 server tool
        - OpenAI: web_search_preview via Responses API
        - Gemini: Google Search grounding tool
        """
        ...
