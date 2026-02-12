"""Tests for LLM adapters: anthropic, openai, gemini.

Patches at the attribute level (not sys.modules) so tests work regardless
of module import order in the full test suite.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ailine_runtime.domain.ports.llm import WebSearchResult, WebSearchSource


class TestAnthropicChatLLM:
    @pytest.fixture
    def mock_client(self):
        return AsyncMock()

    def test_init_with_key(self, mock_client):
        with patch(
            "ailine_runtime.adapters.llm.anthropic_llm.AsyncAnthropic",
            return_value=mock_client,
        ):
            from ailine_runtime.adapters.llm.anthropic_llm import AnthropicChatLLM

            llm = AnthropicChatLLM(model="claude-sonnet-4-5-20250929", api_key="sk-test")
            assert llm.model_name == "claude-sonnet-4-5-20250929"
            assert llm.capabilities["provider"] == "anthropic"

    def test_init_without_key(self, mock_client):
        with patch(
            "ailine_runtime.adapters.llm.anthropic_llm.AsyncAnthropic",
            return_value=mock_client,
        ):
            from ailine_runtime.adapters.llm.anthropic_llm import AnthropicChatLLM

            llm = AnthropicChatLLM()
            assert llm.model_name == "claude-opus-4-6"

    @pytest.mark.asyncio
    async def test_generate(self, mock_client):
        mock_content = MagicMock()
        mock_content.text = "Hello from Anthropic"
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch(
            "ailine_runtime.adapters.llm.anthropic_llm.AsyncAnthropic",
            return_value=mock_client,
        ):
            from ailine_runtime.adapters.llm.anthropic_llm import AnthropicChatLLM

            llm = AnthropicChatLLM(api_key="sk-test")
            result = await llm.generate([{"role": "user", "content": "Hi"}])
            assert result == "Hello from Anthropic"

    @pytest.mark.asyncio
    async def test_generate_empty_content(self, mock_client):
        mock_response = MagicMock()
        mock_response.content = []
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch(
            "ailine_runtime.adapters.llm.anthropic_llm.AsyncAnthropic",
            return_value=mock_client,
        ):
            from ailine_runtime.adapters.llm.anthropic_llm import AnthropicChatLLM

            llm = AnthropicChatLLM(api_key="sk-test")
            result = await llm.generate([{"role": "user", "content": "Hi"}])
            assert result == ""

    @pytest.mark.asyncio
    async def test_stream(self, mock_client):
        class MockStream:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            @property
            def text_stream(self):
                async def gen():
                    yield "Hello "
                    yield "world"

                return gen()

        mock_client.messages.stream = MagicMock(return_value=MockStream())

        with patch(
            "ailine_runtime.adapters.llm.anthropic_llm.AsyncAnthropic",
            return_value=mock_client,
        ):
            from ailine_runtime.adapters.llm.anthropic_llm import AnthropicChatLLM

            llm = AnthropicChatLLM(api_key="sk-test")
            chunks = []
            async for chunk in llm.stream([{"role": "user", "content": "Hi"}]):
                chunks.append(chunk)
            assert "".join(chunks) == "Hello world"


class TestOpenAIChatLLM:
    @pytest.fixture
    def mock_openai(self):
        mock_module = MagicMock()
        mock_client = AsyncMock()
        mock_module.AsyncOpenAI.return_value = mock_client
        return mock_module, mock_client

    def test_init_with_key(self, mock_openai):
        mock_module, _ = mock_openai
        with patch.dict("sys.modules", {"openai": mock_module}):
            from ailine_runtime.adapters.llm.openai_llm import OpenAIChatLLM

            llm = OpenAIChatLLM(model="gpt-4o", api_key="sk-test")
            assert llm.model_name == "gpt-4o"
            assert llm.capabilities["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_generate(self, mock_openai):
        mock_module, mock_client = mock_openai
        mock_message = MagicMock()
        mock_message.content = "Hello from OpenAI"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch.dict("sys.modules", {"openai": mock_module}):
            from ailine_runtime.adapters.llm.openai_llm import OpenAIChatLLM

            llm = OpenAIChatLLM(api_key="sk-test")
            result = await llm.generate([{"role": "user", "content": "Hi"}])
            assert result == "Hello from OpenAI"

    @pytest.mark.asyncio
    async def test_generate_empty_content(self, mock_openai):
        mock_module, mock_client = mock_openai
        mock_message = MagicMock()
        mock_message.content = None
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch.dict("sys.modules", {"openai": mock_module}):
            from ailine_runtime.adapters.llm.openai_llm import OpenAIChatLLM

            llm = OpenAIChatLLM(api_key="sk-test")
            result = await llm.generate([{"role": "user", "content": "Hi"}])
            assert result == ""

    @pytest.mark.asyncio
    async def test_stream(self, mock_openai):
        mock_module, mock_client = mock_openai

        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta = MagicMock()
        chunk1.choices[0].delta.content = "Hello "

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta = MagicMock()
        chunk2.choices[0].delta.content = "world"

        chunk3 = MagicMock()
        chunk3.choices = [MagicMock()]
        chunk3.choices[0].delta = MagicMock()
        chunk3.choices[0].delta.content = None  # empty delta

        async def mock_stream():
            for c in [chunk1, chunk2, chunk3]:
                yield c

        mock_client.chat.completions.create = AsyncMock(return_value=mock_stream())

        with patch.dict("sys.modules", {"openai": mock_module}):
            from ailine_runtime.adapters.llm.openai_llm import OpenAIChatLLM

            llm = OpenAIChatLLM(api_key="sk-test")
            chunks = []
            async for chunk in llm.stream([{"role": "user", "content": "Hi"}]):
                chunks.append(chunk)
            assert "".join(chunks) == "Hello world"


class TestGeminiChatLLM:
    @pytest.fixture
    def mock_genai(self):
        mock_google = MagicMock()
        mock_genai = MagicMock()
        mock_google.genai = mock_genai
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_genai.types = MagicMock()
        return mock_google, mock_genai, mock_client

    def test_init(self, mock_genai):
        mock_google, mock_genai_mod, _ = mock_genai
        with patch.dict("sys.modules", {"google": mock_google, "google.genai": mock_genai_mod}):
            from ailine_runtime.adapters.llm.gemini_llm import GeminiChatLLM

            llm = GeminiChatLLM(model="gemini-2.5-flash", api_key="gk-test")
            assert llm.model_name == "gemini-2.5-flash"
            assert llm.capabilities["provider"] == "gemini"

    @pytest.mark.asyncio
    async def test_generate(self, mock_genai):
        mock_google, mock_genai_mod, mock_client = mock_genai
        mock_response = MagicMock()
        mock_response.text = "Hello from Gemini"
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with patch.dict("sys.modules", {"google": mock_google, "google.genai": mock_genai_mod}):
            from ailine_runtime.adapters.llm.gemini_llm import GeminiChatLLM

            llm = GeminiChatLLM(api_key="gk-test")
            result = await llm.generate([{"role": "user", "content": "Hi"}])
            assert result == "Hello from Gemini"

    @pytest.mark.asyncio
    async def test_generate_empty(self, mock_genai):
        mock_google, mock_genai_mod, mock_client = mock_genai
        mock_response = MagicMock()
        mock_response.text = None
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with patch.dict("sys.modules", {"google": mock_google, "google.genai": mock_genai_mod}):
            from ailine_runtime.adapters.llm.gemini_llm import GeminiChatLLM

            llm = GeminiChatLLM(api_key="gk-test")
            result = await llm.generate([{"role": "user", "content": "Hi"}])
            assert result == ""

    @pytest.mark.asyncio
    async def test_stream(self, mock_genai):
        mock_google, mock_genai_mod, mock_client = mock_genai

        chunk1 = MagicMock()
        chunk1.text = "Hello "
        chunk2 = MagicMock()
        chunk2.text = "world"
        chunk3 = MagicMock()
        chunk3.text = None  # empty chunk

        async def _gen():
            for c in [chunk1, chunk2, chunk3]:
                yield c

        async def mock_stream_coro(*args, **kwargs):
            return _gen()

        mock_client.aio.models.generate_content_stream = mock_stream_coro

        with patch.dict("sys.modules", {"google": mock_google, "google.genai": mock_genai_mod}):
            from ailine_runtime.adapters.llm.gemini_llm import GeminiChatLLM

            llm = GeminiChatLLM(api_key="gk-test")
            chunks = []
            async for chunk in llm.stream([{"role": "user", "content": "Hi"}]):
                chunks.append(chunk)
            assert "".join(chunks) == "Hello world"


class TestGeminiConvertMessages:
    def test_user_message(self):
        from ailine_runtime.adapters.llm.gemini_llm import _convert_messages

        result = _convert_messages([{"role": "user", "content": "Hello"}])
        assert result[0]["role"] == "user"
        assert result[0]["parts"][0]["text"] == "Hello"

    def test_assistant_message(self):
        from ailine_runtime.adapters.llm.gemini_llm import _convert_messages

        result = _convert_messages([{"role": "assistant", "content": "Hi"}])
        assert result[0]["role"] == "model"


# ===========================================================================
# Web Search Tests
# ===========================================================================


class TestWebSearchDataClasses:
    """Test WebSearchResult and WebSearchSource data classes."""

    def test_web_search_source(self):
        src = WebSearchSource(url="https://example.com", title="Example", snippet="A snippet")
        assert src.url == "https://example.com"
        assert src.title == "Example"
        assert src.snippet == "A snippet"

    def test_web_search_source_defaults(self):
        src = WebSearchSource(url="https://example.com", title="Example")
        assert src.snippet == ""

    def test_web_search_result(self):
        result = WebSearchResult(
            text="Answer text",
            sources=[WebSearchSource(url="https://a.com", title="A")],
        )
        assert result.text == "Answer text"
        assert len(result.sources) == 1

    def test_web_search_result_defaults(self):
        result = WebSearchResult(text="Just text")
        assert result.sources == []


class TestFakeLLMWebSearch:
    """Test FakeChatLLM web search capability."""

    @pytest.mark.asyncio
    async def test_fake_generate_with_search(self):
        from ailine_runtime.adapters.llm.fake_llm import FakeChatLLM

        llm = FakeChatLLM()
        assert llm.capabilities["web_search"] is True

        result = await llm.generate_with_search("educação inclusiva")
        assert isinstance(result, WebSearchResult)
        assert "educação inclusiva" in result.text
        assert len(result.sources) == 2
        assert result.sources[0].url.startswith("https://")


class TestAnthropicWebSearch:
    """Test AnthropicChatLLM web search."""

    @pytest.mark.asyncio
    async def test_generate_with_search(self):
        mock_client = AsyncMock()

        # Build mock response with text and citations
        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = "Claude Shannon was born in 1916."
        mock_citation = MagicMock()
        mock_citation.type = "web_search_result_location"
        mock_citation.url = "https://en.wikipedia.org/wiki/Claude_Shannon"
        mock_citation.title = "Claude Shannon - Wikipedia"
        mock_citation.cited_text = "Claude Elwood Shannon (April 30, 1916)"
        mock_text_block.citations = [mock_citation]

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch(
            "ailine_runtime.adapters.llm.anthropic_llm.AsyncAnthropic",
            return_value=mock_client,
        ):
            from ailine_runtime.adapters.llm.anthropic_llm import AnthropicChatLLM

            llm = AnthropicChatLLM(api_key="sk-test")
            assert llm.capabilities["web_search"] is True

            result = await llm.generate_with_search("When was Claude Shannon born?")
            assert isinstance(result, WebSearchResult)
            assert "1916" in result.text
            assert len(result.sources) == 1
            assert "wikipedia" in result.sources[0].url


class TestOpenAIWebSearch:
    """Test OpenAIChatLLM web search via Responses API."""

    @pytest.mark.asyncio
    async def test_generate_with_search(self):
        mock_module = MagicMock()
        mock_client = AsyncMock()
        mock_module.AsyncOpenAI.return_value = mock_client

        # Build mock Responses API response
        mock_annotation = MagicMock()
        mock_annotation.type = "url_citation"
        mock_annotation.url = "https://example.com/article"
        mock_annotation.title = "Article"

        mock_content = MagicMock()
        mock_content.type = "output_text"
        mock_content.text = "The answer is 42."
        mock_content.annotations = [mock_annotation]

        mock_message = MagicMock()
        mock_message.type = "message"
        mock_message.content = [mock_content]

        mock_response = MagicMock()
        mock_response.output = [mock_message]
        mock_response.output_text = "The answer is 42."
        mock_client.responses.create = AsyncMock(return_value=mock_response)

        with patch.dict("sys.modules", {"openai": mock_module}):
            from ailine_runtime.adapters.llm.openai_llm import OpenAIChatLLM

            llm = OpenAIChatLLM(api_key="sk-test", provider="openai")
            assert llm.capabilities["web_search"] is True

            result = await llm.generate_with_search("What is the meaning of life?")
            assert isinstance(result, WebSearchResult)
            assert "42" in result.text
            assert len(result.sources) == 1

    @pytest.mark.asyncio
    async def test_web_search_not_available_openrouter(self):
        mock_module = MagicMock()
        mock_client = AsyncMock()
        mock_module.AsyncOpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_module}):
            from ailine_runtime.adapters.llm.openai_llm import OpenAIChatLLM

            llm = OpenAIChatLLM(api_key="sk-test", provider="openrouter")
            assert llm.capabilities["web_search"] is False

            result = await llm.generate_with_search("test query")
            assert "not available" in result.text.lower()
            assert result.sources == []


class TestGeminiWebSearch:
    """Test GeminiChatLLM web search via Google Search grounding."""

    @pytest.mark.asyncio
    async def test_generate_with_search(self):
        mock_google = MagicMock()
        mock_genai = MagicMock()
        mock_google.genai = mock_genai
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        # Build mock response with grounding metadata
        mock_web = MagicMock()
        mock_web.uri = "https://example.com/edu"
        mock_web.title = "Education Resource"
        mock_chunk = MagicMock()
        mock_chunk.web = mock_web
        mock_metadata = MagicMock()
        mock_metadata.grounding_chunks = [mock_chunk]
        mock_candidate = MagicMock()
        mock_candidate.grounding_metadata = mock_metadata
        mock_response = MagicMock()
        mock_response.text = "Education is important."
        mock_response.candidates = [mock_candidate]

        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with patch.dict("sys.modules", {"google": mock_google, "google.genai": mock_genai}):
            from ailine_runtime.adapters.llm.gemini_llm import GeminiChatLLM

            llm = GeminiChatLLM(api_key="gk-test")
            assert llm.capabilities["web_search"] is True

            result = await llm.generate_with_search("importance of education")
            assert isinstance(result, WebSearchResult)
            assert "Education" in result.text
            assert len(result.sources) == 1
            assert result.sources[0].url == "https://example.com/edu"
