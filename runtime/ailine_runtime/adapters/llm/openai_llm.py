"""OpenAI ChatLLM adapter.

Implements the ChatLLM port using the OpenAI Python SDK.
- Regular generate/stream: Chat Completions API
- Web search: Responses API (web_search_preview tool)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from ...domain.ports.llm import WebSearchResult, WebSearchSource
from ...shared.observability import get_logger

_log = get_logger("ailine.adapters.llm.openai")


class OpenAIChatLLM:
    """ChatLLM implementation backed by OpenAI's APIs.

    Regular calls use Chat Completions API. Web search uses Responses API.
    When provider is "openrouter", the client is configured with the
    OpenRouter base URL and required HTTP-Referer header.
    """

    def __init__(
        self,
        *,
        model: str = "gpt-4o",
        api_key: str = "",
        provider: str = "openai",
    ) -> None:
        from openai import AsyncOpenAI

        self._model = model
        self._provider = provider
        self._api_key = api_key

        kwargs: dict = {}
        if api_key:
            kwargs["api_key"] = api_key
        if provider == "openrouter":
            kwargs["base_url"] = "https://openrouter.ai/api/v1"
            kwargs["default_headers"] = {
                "HTTP-Referer": "https://ailine.app",
            }

        self._client = AsyncOpenAI(**kwargs)

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def capabilities(self) -> dict[str, Any]:
        # Web search only available on native OpenAI (not OpenRouter)
        return {
            "provider": self._provider,
            "streaming": True,
            "tool_use": True,
            "vision": True,
            "web_search": self._provider == "openai",
        }

    async def generate(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.choices[0].message.content or ""

    async def stream(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    async def generate_with_search(
        self,
        query: str,
        *,
        max_results: int = 5,
        **kwargs: Any,
    ) -> WebSearchResult:
        """Search the web using OpenAI's Responses API web_search_preview tool."""
        if self._provider != "openai":
            return WebSearchResult(
                text="Web search not available via OpenRouter.",
                sources=[],
            )

        response = await self._client.responses.create(
            model=self._model,
            tools=[{"type": "web_search_preview"}],
            input=query,
        )

        text_parts: list[str] = []
        sources: list[WebSearchSource] = []

        for item in response.output:
            if getattr(item, "type", None) == "message":
                for content in getattr(item, "content", []):
                    if getattr(content, "type", None) == "output_text":
                        text_parts.append(content.text)
                        # Extract annotations/citations
                        for ann in getattr(content, "annotations", []) or []:
                            if getattr(ann, "type", None) == "url_citation":
                                sources.append(
                                    WebSearchSource(
                                        url=ann.url,
                                        title=getattr(ann, "title", ""),
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
            text=" ".join(text_parts) if text_parts else response.output_text,
            sources=unique_sources,
        )
