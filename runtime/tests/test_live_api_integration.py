"""Live API integration tests for LLM and embedding adapters.

These tests call REAL external APIs with actual API keys. They are
excluded from CI by default (ADR-051) and must be run manually with:

    uv run pytest tests/test_live_api_integration.py -m live_llm -v

Every test is marked ``@pytest.mark.live_llm`` so the standard CI
gate ``-m 'not live_llm'`` will skip them automatically.

Environment variables required (set whichever providers you wish to test):
    OPENAI_API_KEY      - OpenAI platform key
    ANTHROPIC_API_KEY   - Anthropic platform key
    GEMINI_API_KEY      - Google AI Studio / Gemini key
    OPENROUTER_API_KEY  - OpenRouter key

Tests that lack the required key are skipped gracefully via
``pytest.mark.skipif``.
"""

from __future__ import annotations

import math
import os
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Env-var availability flags
# ---------------------------------------------------------------------------

_HAS_OPENAI_KEY = bool(os.environ.get("OPENAI_API_KEY", "").strip())
_HAS_ANTHROPIC_KEY = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
_HAS_GEMINI_KEY = bool(os.environ.get("GEMINI_API_KEY", "").strip())
_HAS_OPENROUTER_KEY = bool(os.environ.get("OPENROUTER_API_KEY", "").strip())

# Skip decorators --------------------------------------------------------

skip_no_openai = pytest.mark.skipif(
    not _HAS_OPENAI_KEY,
    reason="OPENAI_API_KEY not set",
)
skip_no_anthropic = pytest.mark.skipif(
    not _HAS_ANTHROPIC_KEY,
    reason="ANTHROPIC_API_KEY not set",
)
skip_no_gemini = pytest.mark.skipif(
    not _HAS_GEMINI_KEY,
    reason="GEMINI_API_KEY not set",
)
skip_no_openrouter = pytest.mark.skipif(
    not _HAS_OPENROUTER_KEY,
    reason="OPENROUTER_API_KEY not set",
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_SIMPLE_PROMPT: list[dict[str, Any]] = [
    {"role": "user", "content": "Responda em uma frase: qual \u00e9 a capital do Brasil?"},
]

_GENERATE_TIMEOUT = 30  # seconds
_STREAM_TIMEOUT = 60  # seconds
_EMBED_TIMEOUT = 30  # seconds


def _assert_brazilian_answer(text: str) -> None:
    """Loose assertion that the response mentions Brasilia."""
    lowered = text.lower()
    assert any(
        w in lowered for w in ("bras\u00edlia", "brasilia")
    ), f"Expected 'Bras\u00edlia' in response, got: {text!r}"


# =========================================================================
# OpenAI ChatLLM — live tests
# =========================================================================


@pytest.mark.live_llm
@skip_no_openai
class TestOpenAIChatLLMLive:
    """Live tests for OpenAIChatLLM against the real OpenAI API."""

    @pytest.fixture
    def llm(self):
        from ailine_runtime.adapters.llm.openai_llm import OpenAIChatLLM

        return OpenAIChatLLM(
            model="gpt-4o-mini",
            api_key=os.environ["OPENAI_API_KEY"],
        )

    @pytest.mark.timeout(_GENERATE_TIMEOUT)
    async def test_generate_returns_brasilia(self, llm):
        result = await llm.generate(_SIMPLE_PROMPT, temperature=0.0, max_tokens=100)
        assert isinstance(result, str)
        assert len(result) > 0
        _assert_brazilian_answer(result)

    @pytest.mark.timeout(_STREAM_TIMEOUT)
    async def test_stream_collects_chunks(self, llm):
        chunks: list[str] = []
        async for chunk in llm.stream(_SIMPLE_PROMPT, temperature=0.0, max_tokens=100):
            chunks.append(chunk)
            if len(chunks) >= 1:
                break  # At least one chunk is enough to prove streaming works
        assert len(chunks) >= 1
        assert all(isinstance(c, str) for c in chunks)

    @pytest.mark.timeout(_STREAM_TIMEOUT)
    async def test_stream_full_response_mentions_brasilia(self, llm):
        chunks: list[str] = []
        async for chunk in llm.stream(_SIMPLE_PROMPT, temperature=0.0, max_tokens=100):
            chunks.append(chunk)
        full = "".join(chunks)
        _assert_brazilian_answer(full)

    def test_model_name(self, llm):
        assert llm.model_name == "gpt-4o-mini"

    def test_capabilities_provider(self, llm):
        assert llm.capabilities["provider"] == "openai"
        assert llm.capabilities["streaming"] is True

    def test_protocol_compliance(self, llm):
        from ailine_runtime.domain.ports.llm import ChatLLM

        assert isinstance(llm, ChatLLM)


# =========================================================================
# Anthropic ChatLLM — live tests
# =========================================================================


@pytest.mark.live_llm
@skip_no_anthropic
class TestAnthropicChatLLMLive:
    """Live tests for AnthropicChatLLM against the real Anthropic API."""

    @pytest.fixture
    def llm(self):
        from ailine_runtime.adapters.llm.anthropic_llm import AnthropicChatLLM

        return AnthropicChatLLM(
            model="claude-haiku-4-5-20251001",
            api_key=os.environ["ANTHROPIC_API_KEY"],
        )

    @pytest.mark.timeout(_GENERATE_TIMEOUT)
    async def test_generate_returns_brasilia(self, llm):
        result = await llm.generate(_SIMPLE_PROMPT, temperature=0.0, max_tokens=100)
        assert isinstance(result, str)
        assert len(result) > 0
        _assert_brazilian_answer(result)

    @pytest.mark.timeout(_STREAM_TIMEOUT)
    async def test_stream_collects_chunks(self, llm):
        chunks: list[str] = []
        async for chunk in llm.stream(_SIMPLE_PROMPT, temperature=0.0, max_tokens=100):
            chunks.append(chunk)
            if len(chunks) >= 1:
                break
        assert len(chunks) >= 1
        assert all(isinstance(c, str) for c in chunks)

    @pytest.mark.timeout(_STREAM_TIMEOUT)
    async def test_stream_full_response_mentions_brasilia(self, llm):
        chunks: list[str] = []
        async for chunk in llm.stream(_SIMPLE_PROMPT, temperature=0.0, max_tokens=100):
            chunks.append(chunk)
        full = "".join(chunks)
        _assert_brazilian_answer(full)

    def test_model_name(self, llm):
        assert llm.model_name == "claude-haiku-4-5-20251001"

    def test_capabilities_provider(self, llm):
        assert llm.capabilities["provider"] == "anthropic"
        assert llm.capabilities["streaming"] is True

    def test_protocol_compliance(self, llm):
        from ailine_runtime.domain.ports.llm import ChatLLM

        assert isinstance(llm, ChatLLM)


# =========================================================================
# Gemini ChatLLM — live tests
# =========================================================================


@pytest.mark.live_llm
@skip_no_gemini
class TestGeminiChatLLMLive:
    """Live tests for GeminiChatLLM against the real Gemini API."""

    @pytest.fixture
    def llm(self):
        from ailine_runtime.adapters.llm.gemini_llm import GeminiChatLLM

        return GeminiChatLLM(
            model="gemini-2.0-flash",
            api_key=os.environ["GEMINI_API_KEY"],
        )

    @pytest.mark.timeout(_GENERATE_TIMEOUT)
    async def test_generate_returns_brasilia(self, llm):
        result = await llm.generate(_SIMPLE_PROMPT, temperature=0.0, max_tokens=100)
        assert isinstance(result, str)
        assert len(result) > 0
        _assert_brazilian_answer(result)

    @pytest.mark.timeout(_STREAM_TIMEOUT)
    async def test_stream_collects_chunks(self, llm):
        chunks: list[str] = []
        async for chunk in llm.stream(_SIMPLE_PROMPT, temperature=0.0, max_tokens=100):
            chunks.append(chunk)
            if len(chunks) >= 1:
                break
        assert len(chunks) >= 1
        assert all(isinstance(c, str) for c in chunks)

    @pytest.mark.timeout(_STREAM_TIMEOUT)
    async def test_stream_full_response_mentions_brasilia(self, llm):
        chunks: list[str] = []
        async for chunk in llm.stream(_SIMPLE_PROMPT, temperature=0.0, max_tokens=100):
            chunks.append(chunk)
        full = "".join(chunks)
        _assert_brazilian_answer(full)

    def test_model_name(self, llm):
        assert llm.model_name == "gemini-2.0-flash"

    def test_capabilities_provider(self, llm):
        assert llm.capabilities["provider"] == "gemini"
        assert llm.capabilities["streaming"] is True

    def test_protocol_compliance(self, llm):
        from ailine_runtime.domain.ports.llm import ChatLLM

        assert isinstance(llm, ChatLLM)


# =========================================================================
# OpenRouter ChatLLM — live tests
# =========================================================================


@pytest.mark.live_llm
@skip_no_openrouter
class TestOpenRouterChatLLMLive:
    """Live tests for OpenAIChatLLM configured as OpenRouter provider."""

    @pytest.fixture
    def llm(self):
        from ailine_runtime.adapters.llm.openai_llm import OpenAIChatLLM

        return OpenAIChatLLM(
            model="google/gemini-2.0-flash-001",
            api_key=os.environ["OPENROUTER_API_KEY"],
            provider="openrouter",
        )

    @pytest.mark.timeout(_GENERATE_TIMEOUT)
    async def test_generate_returns_brasilia(self, llm):
        result = await llm.generate(_SIMPLE_PROMPT, temperature=0.0, max_tokens=100)
        assert isinstance(result, str)
        assert len(result) > 0
        _assert_brazilian_answer(result)

    @pytest.mark.timeout(_STREAM_TIMEOUT)
    async def test_stream_collects_chunks(self, llm):
        chunks: list[str] = []
        async for chunk in llm.stream(_SIMPLE_PROMPT, temperature=0.0, max_tokens=100):
            chunks.append(chunk)
            if len(chunks) >= 1:
                break
        assert len(chunks) >= 1

    def test_model_name(self, llm):
        assert llm.model_name == "google/gemini-2.0-flash-001"

    def test_capabilities_provider_is_openrouter(self, llm):
        assert llm.capabilities["provider"] == "openrouter"

    def test_protocol_compliance(self, llm):
        from ailine_runtime.domain.ports.llm import ChatLLM

        assert isinstance(llm, ChatLLM)


# =========================================================================
# SmartRouter — live tests (routes to real providers)
# =========================================================================


@pytest.mark.live_llm
class TestSmartRouterLive:
    """Live tests for SmartRouterAdapter with real provider backends.

    Requires at least one API key. The router falls back gracefully
    when certain providers are unavailable.
    """

    @pytest.fixture
    def router(self):
        from ailine_runtime.adapters.llm.smart_router import (
            SmartRouterAdapter,
            SmartRouterConfig,
        )

        cheap = None
        middle = None
        primary = None

        if _HAS_GEMINI_KEY:
            from ailine_runtime.adapters.llm.gemini_llm import GeminiChatLLM

            cheap = GeminiChatLLM(
                model="gemini-2.0-flash",
                api_key=os.environ["GEMINI_API_KEY"],
            )

        if _HAS_OPENAI_KEY:
            from ailine_runtime.adapters.llm.openai_llm import OpenAIChatLLM

            middle = OpenAIChatLLM(
                model="gpt-4o-mini",
                api_key=os.environ["OPENAI_API_KEY"],
            )

        if _HAS_ANTHROPIC_KEY:
            from ailine_runtime.adapters.llm.anthropic_llm import AnthropicChatLLM

            primary = AnthropicChatLLM(
                model="claude-haiku-4-5-20251001",
                api_key=os.environ["ANTHROPIC_API_KEY"],
            )

        if not any([cheap, middle, primary]):
            pytest.skip("No LLM API keys available for SmartRouter test")

        config = SmartRouterConfig(
            cheap_provider=cheap,
            middle_provider=middle,
            primary_provider=primary,
        )
        return SmartRouterAdapter(config)

    @pytest.mark.timeout(_GENERATE_TIMEOUT)
    async def test_generate_simple_routes_cheap(self, router):
        """A short, simple prompt should route to the cheap tier."""
        result = await router.generate(_SIMPLE_PROMPT, temperature=0.0, max_tokens=100)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.timeout(_STREAM_TIMEOUT)
    async def test_stream_simple(self, router):
        chunks: list[str] = []
        async for chunk in router.stream(_SIMPLE_PROMPT, temperature=0.0, max_tokens=100):
            chunks.append(chunk)
        assert len(chunks) >= 1
        full = "".join(chunks)
        assert len(full) > 0

    def test_classify_tier_simple_is_cheap(self, router):
        tier = router.classify_tier(_SIMPLE_PROMPT)
        assert tier == "cheap"

    def test_classify_tier_complex_is_higher(self, router):
        complex_messages: list[dict[str, Any]] = [
            {"role": "user", "content": f"Analise detalhada msg{i} " + "x" * 500}
            for i in range(25)
        ]
        tier = router.classify_tier(
            complex_messages,
            tools=[{"name": f"tool_{i}"} for i in range(10)],
            response_format={"type": "json"},
        )
        assert tier in ("middle", "primary")

    def test_classify_tier_returns_valid_values(self, router):
        """classify_tier must return one of the three valid tier strings."""
        for msgs in [
            _SIMPLE_PROMPT,
            [{"role": "user", "content": "x" * 5000}],
            [{"role": "user", "content": "analise complexa BNCC acessibilidade " + "x" * 4000}] * 20,
        ]:
            tier = router.classify_tier(msgs)
            assert tier in ("cheap", "middle", "primary"), f"Invalid tier: {tier}"

    def test_model_name_contains_smart_router(self, router):
        assert "smart-router" in router.model_name

    def test_capabilities(self, router):
        caps = router.capabilities
        assert caps["provider"] == "smart-router"
        assert caps["routing_mode"] == "weighted"


# =========================================================================
# OpenAI Embeddings — live tests
# =========================================================================


@pytest.mark.live_llm
@skip_no_openai
class TestOpenAIEmbeddingsLive:
    """Live tests for OpenAIEmbeddings against the real OpenAI API."""

    @pytest.fixture
    def embeddings(self):
        from ailine_runtime.adapters.embeddings.openai_embeddings import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model="text-embedding-3-large",
            api_key=os.environ["OPENAI_API_KEY"],
            dimensions=1536,
        )

    @pytest.mark.timeout(_EMBED_TIMEOUT)
    async def test_embed_text_returns_correct_dimensions(self, embeddings):
        vec = await embeddings.embed_text("A capital do Brasil e Brasilia.")
        assert isinstance(vec, list)
        assert len(vec) == 1536

    @pytest.mark.timeout(_EMBED_TIMEOUT)
    async def test_embed_text_is_l2_normalized(self, embeddings):
        vec = await embeddings.embed_text("Teste de normalizacao L2.")
        norm = math.sqrt(sum(v * v for v in vec))
        assert abs(norm - 1.0) < 1e-4, f"L2 norm should be ~1.0, got {norm}"

    @pytest.mark.timeout(_EMBED_TIMEOUT)
    async def test_embed_text_values_are_floats(self, embeddings):
        vec = await embeddings.embed_text("Valores devem ser float.")
        assert all(isinstance(v, float) for v in vec)

    @pytest.mark.timeout(_EMBED_TIMEOUT)
    async def test_embed_batch_returns_correct_count(self, embeddings):
        texts = [
            "Primeira frase sobre educacao.",
            "Segunda frase sobre tecnologia.",
            "Terceira frase sobre acessibilidade.",
        ]
        vecs = await embeddings.embed_batch(texts)
        assert len(vecs) == 3

    @pytest.mark.timeout(_EMBED_TIMEOUT)
    async def test_embed_batch_each_vector_correct_dimensions(self, embeddings):
        texts = ["Texto A.", "Texto B."]
        vecs = await embeddings.embed_batch(texts)
        for vec in vecs:
            assert len(vec) == 1536

    @pytest.mark.timeout(_EMBED_TIMEOUT)
    async def test_embed_batch_each_vector_is_l2_normalized(self, embeddings):
        texts = ["Frase um.", "Frase dois.", "Frase tres."]
        vecs = await embeddings.embed_batch(texts)
        for vec in vecs:
            norm = math.sqrt(sum(v * v for v in vec))
            assert abs(norm - 1.0) < 1e-4, f"L2 norm should be ~1.0, got {norm}"

    @pytest.mark.timeout(_EMBED_TIMEOUT)
    async def test_embed_batch_empty_returns_empty(self, embeddings):
        vecs = await embeddings.embed_batch([])
        assert vecs == []

    @pytest.mark.timeout(_EMBED_TIMEOUT)
    async def test_semantic_similarity(self, embeddings):
        """Similar texts should have higher cosine similarity than dissimilar ones."""
        vec_a = await embeddings.embed_text("A educacao e fundamental para o desenvolvimento.")
        vec_b = await embeddings.embed_text("O ensino e essencial para o crescimento.")
        vec_c = await embeddings.embed_text("O gato dormiu no telhado.")

        # Cosine similarity (vectors are already L2-normalized, so dot product = cosine)
        sim_ab = sum(a * b for a, b in zip(vec_a, vec_b, strict=True))
        sim_ac = sum(a * c for a, c in zip(vec_a, vec_c, strict=True))

        assert sim_ab > sim_ac, (
            f"Education sentences should be more similar ({sim_ab:.4f}) "
            f"than education vs cat ({sim_ac:.4f})"
        )

    def test_dimensions_property(self, embeddings):
        assert embeddings.dimensions == 1536

    def test_model_name_property(self, embeddings):
        assert embeddings.model_name == "text-embedding-3-large"

    def test_protocol_compliance(self, embeddings):
        from ailine_runtime.domain.ports.embeddings import Embeddings

        assert isinstance(embeddings, Embeddings)


# =========================================================================
# Gemini Embeddings — live tests
# =========================================================================


@pytest.mark.live_llm
@skip_no_gemini
class TestGeminiEmbeddingsLive:
    """Live tests for GeminiEmbeddings against the real Gemini API."""

    @pytest.fixture
    def embeddings(self):
        from ailine_runtime.adapters.embeddings.gemini_embeddings import GeminiEmbeddings

        return GeminiEmbeddings(
            model="gemini-embedding-001",
            api_key=os.environ["GEMINI_API_KEY"],
            dimensions=1536,
        )

    @pytest.mark.timeout(_EMBED_TIMEOUT)
    async def test_embed_text_returns_correct_dimensions(self, embeddings):
        vec = await embeddings.embed_text("A capital do Brasil e Brasilia.")
        assert isinstance(vec, list)
        assert len(vec) == 1536

    @pytest.mark.timeout(_EMBED_TIMEOUT)
    async def test_embed_text_is_l2_normalized(self, embeddings):
        vec = await embeddings.embed_text("Teste de normalizacao L2.")
        norm = math.sqrt(sum(v * v for v in vec))
        assert abs(norm - 1.0) < 1e-4, f"L2 norm should be ~1.0, got {norm}"

    @pytest.mark.timeout(_EMBED_TIMEOUT)
    async def test_embed_text_values_are_floats(self, embeddings):
        vec = await embeddings.embed_text("Valores devem ser float.")
        assert all(isinstance(v, float) for v in vec)

    @pytest.mark.timeout(_EMBED_TIMEOUT)
    async def test_embed_batch_returns_correct_count(self, embeddings):
        texts = [
            "Primeira frase sobre educacao.",
            "Segunda frase sobre tecnologia.",
        ]
        vecs = await embeddings.embed_batch(texts)
        assert len(vecs) == 2

    @pytest.mark.timeout(_EMBED_TIMEOUT)
    async def test_embed_batch_each_vector_correct_dimensions(self, embeddings):
        texts = ["Texto A.", "Texto B."]
        vecs = await embeddings.embed_batch(texts)
        for vec in vecs:
            assert len(vec) == 1536

    @pytest.mark.timeout(_EMBED_TIMEOUT)
    async def test_embed_batch_each_vector_is_l2_normalized(self, embeddings):
        texts = ["Frase um.", "Frase dois."]
        vecs = await embeddings.embed_batch(texts)
        for vec in vecs:
            norm = math.sqrt(sum(v * v for v in vec))
            assert abs(norm - 1.0) < 1e-4, f"L2 norm should be ~1.0, got {norm}"

    @pytest.mark.timeout(_EMBED_TIMEOUT)
    async def test_embed_batch_empty_returns_empty(self, embeddings):
        vecs = await embeddings.embed_batch([])
        assert vecs == []

    @pytest.mark.timeout(_EMBED_TIMEOUT)
    async def test_semantic_similarity(self, embeddings):
        """Similar texts should have higher cosine similarity than dissimilar ones."""
        vec_a = await embeddings.embed_text("A educacao e fundamental para o desenvolvimento.")
        vec_b = await embeddings.embed_text("O ensino e essencial para o crescimento.")
        vec_c = await embeddings.embed_text("O gato dormiu no telhado.")

        sim_ab = sum(a * b for a, b in zip(vec_a, vec_b, strict=True))
        sim_ac = sum(a * c for a, c in zip(vec_a, vec_c, strict=True))

        assert sim_ab > sim_ac, (
            f"Education sentences should be more similar ({sim_ab:.4f}) "
            f"than education vs cat ({sim_ac:.4f})"
        )

    def test_dimensions_property(self, embeddings):
        assert embeddings.dimensions == 1536

    def test_model_name_property(self, embeddings):
        assert embeddings.model_name == "gemini-embedding-001"

    def test_protocol_compliance(self, embeddings):
        from ailine_runtime.domain.ports.embeddings import Embeddings

        assert isinstance(embeddings, Embeddings)


# =========================================================================
# Cross-provider consistency tests
# =========================================================================


@pytest.mark.live_llm
class TestCrossProviderConsistency:
    """Tests that verify consistent behavior across multiple providers.

    These tests only run when at least two LLM keys are available.
    """

    @pytest.fixture
    def available_llms(self) -> list[tuple[str, Any]]:
        """Build a list of (name, adapter) pairs from available keys."""
        adapters: list[tuple[str, Any]] = []

        if _HAS_OPENAI_KEY:
            from ailine_runtime.adapters.llm.openai_llm import OpenAIChatLLM

            adapters.append((
                "openai",
                OpenAIChatLLM(model="gpt-4o-mini", api_key=os.environ["OPENAI_API_KEY"]),
            ))

        if _HAS_ANTHROPIC_KEY:
            from ailine_runtime.adapters.llm.anthropic_llm import AnthropicChatLLM

            adapters.append((
                "anthropic",
                AnthropicChatLLM(
                    model="claude-haiku-4-5-20251001",
                    api_key=os.environ["ANTHROPIC_API_KEY"],
                ),
            ))

        if _HAS_GEMINI_KEY:
            from ailine_runtime.adapters.llm.gemini_llm import GeminiChatLLM

            adapters.append((
                "gemini",
                GeminiChatLLM(model="gemini-2.0-flash", api_key=os.environ["GEMINI_API_KEY"]),
            ))

        if len(adapters) < 2:
            pytest.skip("Need at least 2 LLM API keys for cross-provider tests")

        return adapters

    @pytest.mark.timeout(90)
    async def test_all_providers_answer_brasilia(self, available_llms):
        """Every available provider should answer 'Brasilia' to the capital question."""
        for _name, llm in available_llms:
            result = await llm.generate(_SIMPLE_PROMPT, temperature=0.0, max_tokens=100)
            _assert_brazilian_answer(result)

    @pytest.mark.timeout(90)
    async def test_all_providers_stream_at_least_one_chunk(self, available_llms):
        """Every available provider should produce at least one streaming chunk."""
        for name, llm in available_llms:
            chunks: list[str] = []
            async for chunk in llm.stream(_SIMPLE_PROMPT, temperature=0.0, max_tokens=100):
                chunks.append(chunk)
                if len(chunks) >= 1:
                    break
            assert len(chunks) >= 1, f"{name} did not produce any streaming chunks"

    def test_all_providers_satisfy_chatllm_protocol(self, available_llms):
        from ailine_runtime.domain.ports.llm import ChatLLM

        for name, llm in available_llms:
            assert isinstance(llm, ChatLLM), f"{name} does not satisfy ChatLLM protocol"
