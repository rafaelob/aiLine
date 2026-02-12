"""Tests for FINDING-13: OpenRouter base_url differentiation."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch


class TestOpenRouterBaseUrl:
    def test_openrouter_provider_sets_base_url(self):
        """When provider is 'openrouter', base_url points to OpenRouter API."""
        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.AsyncOpenAI.return_value = mock_client

        with patch.dict(sys.modules, {"openai": mock_openai}):
            from ailine_runtime.adapters.llm.openai_llm import OpenAIChatLLM

            OpenAIChatLLM(
                model="openai/gpt-4o",
                api_key="sk-or-test",
                provider="openrouter",
            )

        # Verify AsyncOpenAI was called with base_url and headers
        call_kwargs = mock_openai.AsyncOpenAI.call_args
        assert call_kwargs.kwargs["base_url"] == "https://openrouter.ai/api/v1"
        assert "HTTP-Referer" in call_kwargs.kwargs["default_headers"]

    def test_openai_provider_no_base_url(self):
        """When provider is 'openai', no base_url override."""
        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.AsyncOpenAI.return_value = mock_client

        with patch.dict(sys.modules, {"openai": mock_openai}):
            from ailine_runtime.adapters.llm.openai_llm import OpenAIChatLLM

            OpenAIChatLLM(
                model="gpt-4o",
                api_key="sk-test",
                provider="openai",
            )

        call_kwargs = mock_openai.AsyncOpenAI.call_args
        assert "base_url" not in call_kwargs.kwargs

    def test_openrouter_capabilities_provider(self):
        """Capabilities dict reports 'openrouter' as the provider."""
        mock_openai = MagicMock()
        mock_openai.AsyncOpenAI.return_value = MagicMock()

        with patch.dict(sys.modules, {"openai": mock_openai}):
            from ailine_runtime.adapters.llm.openai_llm import OpenAIChatLLM

            llm = OpenAIChatLLM(
                model="openai/gpt-4o",
                api_key="sk-or-test",
                provider="openrouter",
            )
            assert llm.capabilities["provider"] == "openrouter"

    def test_default_provider_is_openai(self):
        """Default provider parameter is 'openai'."""
        mock_openai = MagicMock()
        mock_openai.AsyncOpenAI.return_value = MagicMock()

        with patch.dict(sys.modules, {"openai": mock_openai}):
            from ailine_runtime.adapters.llm.openai_llm import OpenAIChatLLM

            llm = OpenAIChatLLM(api_key="sk-test")
            assert llm.capabilities["provider"] == "openai"


class TestContainerOpenRouterWiring:
    def test_container_passes_provider_to_openai_llm(self):
        """Container passes provider='openrouter' when LLM provider is openrouter."""
        mock_openai = MagicMock()
        mock_openai.AsyncOpenAI.return_value = MagicMock()

        from ailine_runtime.shared.config import Settings
        from ailine_runtime.shared.container import _build_llm

        settings = Settings(
            llm={"provider": "openrouter", "api_key": "sk-or-test"},
        )

        with patch.dict(sys.modules, {"openai": mock_openai}):
            llm = _build_llm(settings)

        assert type(llm).__name__ == "OpenAIChatLLM"
        # Verify the AsyncOpenAI constructor received base_url
        call_kwargs = mock_openai.AsyncOpenAI.call_args
        assert call_kwargs.kwargs["base_url"] == "https://openrouter.ai/api/v1"
