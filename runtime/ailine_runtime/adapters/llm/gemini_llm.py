"""Google Gemini ChatLLM adapter.

Implements the ChatLLM port using the google-genai SDK.
Supports native web search via Google Search grounding tool.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from ...domain.ports.llm import WebSearchResult, WebSearchSource
from ...shared.observability import get_logger

_log = get_logger("ailine.adapters.llm.gemini")


class GeminiChatLLM:
    """ChatLLM implementation backed by Gemini via google-genai."""

    def __init__(
        self, *, model: str = "gemini-3-flash-preview", api_key: str = ""
    ) -> None:
        from google import genai

        # Strip provider prefix if present (e.g. "google-gla:gemini-3-flash-preview" → "gemini-3-flash-preview")
        self._model = model.removeprefix("google-gla:").removeprefix("google-vertex:")
        self._client = genai.Client(api_key=api_key) if api_key else genai.Client()

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def capabilities(self) -> dict[str, Any]:
        return {
            "provider": "gemini",
            "streaming": True,
            "tool_use": True,
            "vision": True,
            "thinking": True,
            "web_search": True,
        }

    async def generate(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str:
        from google import genai

        contents = _convert_messages(messages)
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=contents,  # type: ignore[arg-type]  # google-genai accepts dict format
            config=genai.types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text or ""

    async def stream(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        from google import genai

        contents = _convert_messages(messages)
        response_stream = await self._client.aio.models.generate_content_stream(
            model=self._model,
            contents=contents,  # type: ignore[arg-type]  # google-genai accepts dict format
            config=genai.types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        async for chunk in response_stream:
            if chunk.text:
                yield chunk.text

    async def generate_with_search(
        self,
        query: str,
        *,
        max_results: int = 5,
        **kwargs: Any,
    ) -> WebSearchResult:
        """Search the web using Gemini's Google Search grounding tool."""
        from google import genai

        grounding_tool = genai.types.Tool(google_search=genai.types.GoogleSearch())
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=query,
            config=genai.types.GenerateContentConfig(
                tools=[grounding_tool],
            ),
        )

        text = response.text or ""
        sources: list[WebSearchSource] = []

        # Extract grounding metadata from response
        if response.candidates:
            metadata = getattr(response.candidates[0], "grounding_metadata", None)
            if metadata:
                chunks = getattr(metadata, "grounding_chunks", []) or []
                for chunk in chunks:
                    web = getattr(chunk, "web", None)
                    if web:
                        sources.append(
                            WebSearchSource(
                                url=getattr(web, "uri", ""),
                                title=getattr(web, "title", ""),
                                snippet="",
                            )
                        )

        return WebSearchResult(text=text, sources=sources)


def _convert_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert OpenAI-style messages to Gemini contents format."""
    contents: list[dict[str, Any]] = []
    for msg in messages:
        role = "model" if msg.get("role") == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})
    return contents
