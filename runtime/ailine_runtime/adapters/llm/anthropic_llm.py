"""Anthropic ChatLLM adapter.

Implements the ChatLLM port using the Anthropic Python SDK.
Supports native web search via the web_search_20250305 server tool.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from anthropic import AsyncAnthropic

from ...domain.ports.llm import WebSearchResult, WebSearchSource
from ...shared.observability import get_logger

_log = get_logger("ailine.adapters.llm.anthropic")


class AnthropicChatLLM:
    """ChatLLM implementation backed by Anthropic's Messages API."""

    def __init__(self, *, model: str = "claude-opus-4-6", api_key: str = "") -> None:
        self._model = model
        self._client = AsyncAnthropic(api_key=api_key) if api_key else AsyncAnthropic()

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def capabilities(self) -> dict[str, Any]:
        return {
            "provider": "anthropic",
            "streaming": True,
            "tool_use": True,
            "vision": True,
            "web_search": True,
            "max_output_tokens": 8192,
        }

    async def generate(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str:
        response = await self._client.messages.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.content[0].text if response.content else ""

    async def stream(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        async with self._client.messages.stream(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def generate_with_search(
        self,
        query: str,
        *,
        max_results: int = 5,
        **kwargs: Any,
    ) -> WebSearchResult:
        """Search the web using Anthropic's native web_search_20250305 tool."""
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            messages=[{"role": "user", "content": query}],
            tools=[
                {
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": max_results,
                }
            ],
        )

        text_parts: list[str] = []
        sources: list[WebSearchSource] = []

        for block in response.content:
            if getattr(block, "type", None) == "text":
                text_parts.append(block.text)
                # Extract citations if present
                for citation in getattr(block, "citations", []) or []:
                    if getattr(citation, "type", None) == "web_search_result_location":
                        sources.append(
                            WebSearchSource(
                                url=citation.url,
                                title=getattr(citation, "title", ""),
                                snippet=getattr(citation, "cited_text", ""),
                            )
                        )
            elif getattr(block, "type", None) == "web_search_tool_result":
                for result in getattr(block, "content", []) or []:
                    if getattr(result, "type", None) == "web_search_result":
                        sources.append(
                            WebSearchSource(
                                url=result.url,
                                title=getattr(result, "title", ""),
                                snippet="",
                            )
                        )

        # Deduplicate sources by URL
        seen_urls: set[str] = set()
        unique_sources: list[WebSearchSource] = []
        for src in sources:
            if src.url not in seen_urls:
                seen_urls.add(src.url)
                unique_sources.append(src)

        return WebSearchResult(
            text=" ".join(text_parts),
            sources=unique_sources,
        )


assert isinstance(AnthropicChatLLM, type), "AnthropicChatLLM must be a class"
