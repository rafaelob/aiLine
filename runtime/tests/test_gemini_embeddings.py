"""Tests for GeminiEmbeddings adapter -- covers all uncovered lines.

Targets:
- Lines 53, 58 (dimensions, model_name properties)
- Lines 65-68 (_l2_normalize static method)
- Lines 72-74 (_embed_config helper)
- Lines 84-93 (embed_text method)
- Lines 103-119 (embed_batch method)

Mocks google.genai SDK since it is not installed.
"""

from __future__ import annotations

import importlib
import math
import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Fixtures: build a mock google.genai module hierarchy
# ---------------------------------------------------------------------------


def _make_mock_google_genai():
    """Create a mock google + google.genai + google.genai.types hierarchy."""
    mock_google = ModuleType("google")
    mock_genai = ModuleType("google.genai")

    # Client mock
    mock_client_cls = MagicMock(name="Client")
    mock_genai.Client = mock_client_cls

    # types mock with EmbedContentConfig
    mock_types = ModuleType("google.genai.types")
    mock_types.EmbedContentConfig = MagicMock(name="EmbedContentConfig")
    mock_genai.types = mock_types

    mock_google.genai = mock_genai
    return mock_google, mock_genai, mock_types, mock_client_cls


@pytest.fixture()
def gemini_env():
    """Provide a fully mocked google.genai environment and return the adapter class."""
    mock_google, mock_genai, mock_types, mock_client_cls = _make_mock_google_genai()

    modules_patch = {
        "google": mock_google,
        "google.genai": mock_genai,
        "google.genai.types": mock_types,
    }

    with patch.dict(sys.modules, modules_patch):
        # Force reimport so the module picks up mocked google.genai
        mod_key = "ailine_runtime.adapters.embeddings.gemini_embeddings"
        saved = sys.modules.pop(mod_key, None)
        try:
            import ailine_runtime.adapters.embeddings.gemini_embeddings as gem_mod

            importlib.reload(gem_mod)
            yield gem_mod, mock_client_cls, mock_types
        finally:
            if saved is not None:
                sys.modules[mod_key] = saved


# ===========================================================================
# Property tests (lines 53, 58)
# ===========================================================================


class TestGeminiEmbeddingsProperties:
    def test_dimensions_property(self, gemini_env):
        gem_mod, _mock_client_cls, _ = gemini_env
        emb = gem_mod.GeminiEmbeddings(model="test-model", api_key="k", dimensions=768)
        assert emb.dimensions == 768

    def test_model_name_property(self, gemini_env):
        gem_mod, _mock_client_cls, _ = gemini_env
        emb = gem_mod.GeminiEmbeddings(model="my-gemini-model", api_key="k")
        assert emb.model_name == "my-gemini-model"

    def test_default_dimensions(self, gemini_env):
        gem_mod, _mock_client_cls, _ = gemini_env
        emb = gem_mod.GeminiEmbeddings(api_key="k")
        assert emb.dimensions == 3072

    def test_default_model(self, gemini_env):
        gem_mod, _mock_client_cls, _ = gemini_env
        emb = gem_mod.GeminiEmbeddings(api_key="k")
        assert emb.model_name == "gemini-embedding-001"


# ===========================================================================
# _l2_normalize tests (lines 65-68)
# ===========================================================================


class TestL2Normalize:
    def test_normalizes_vector(self, gemini_env):
        gem_mod, _, _ = gemini_env
        cls = gem_mod.GeminiEmbeddings
        vec = np.array([3.0, 4.0], dtype=np.float32)
        result = cls._l2_normalize(vec)
        assert isinstance(result, list)
        norm = math.sqrt(sum(v * v for v in result))
        assert abs(norm - 1.0) < 1e-5

    def test_zero_vector_unchanged(self, gemini_env):
        """A zero vector should return all zeros (no division by zero)."""
        gem_mod, _, _ = gemini_env
        cls = gem_mod.GeminiEmbeddings
        vec = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        result = cls._l2_normalize(vec)
        assert result == [0.0, 0.0, 0.0]

    def test_already_normalized(self, gemini_env):
        gem_mod, _, _ = gemini_env
        cls = gem_mod.GeminiEmbeddings
        vec = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        result = cls._l2_normalize(vec)
        assert abs(result[0] - 1.0) < 1e-6
        assert abs(result[1]) < 1e-6


# ===========================================================================
# _embed_config tests (lines 72-74)
# ===========================================================================


class TestEmbedConfig:
    def test_embed_config_creates_config(self, gemini_env):
        gem_mod, _, mock_types = gemini_env
        emb = gem_mod.GeminiEmbeddings(api_key="k", dimensions=512)
        emb._embed_config()
        mock_types.EmbedContentConfig.assert_called_with(output_dimensionality=512)


# ===========================================================================
# embed_text tests (lines 84-93)
# ===========================================================================


class TestEmbedText:
    async def test_embed_text_returns_normalized_vector(self, gemini_env):
        gem_mod, _mock_client_cls, _ = gemini_env
        emb = gem_mod.GeminiEmbeddings(api_key="k", dimensions=3)

        # Mock the response chain
        mock_embedding = MagicMock()
        mock_embedding.values = [3.0, 4.0, 0.0]
        mock_response = MagicMock()
        mock_response.embeddings = [mock_embedding]

        emb._client.aio.models.embed_content = AsyncMock(return_value=mock_response)

        result = await emb.embed_text("hello")

        assert len(result) == 3
        assert all(isinstance(v, float) for v in result)
        norm = math.sqrt(sum(v * v for v in result))
        assert abs(norm - 1.0) < 1e-5

    async def test_embed_text_calls_api_with_correct_params(self, gemini_env):
        gem_mod, _, _ = gemini_env
        emb = gem_mod.GeminiEmbeddings(model="test-m", api_key="k", dimensions=4)

        mock_embedding = MagicMock()
        mock_embedding.values = [1.0, 0.0, 0.0, 0.0]
        mock_response = MagicMock()
        mock_response.embeddings = [mock_embedding]

        emb._client.aio.models.embed_content = AsyncMock(return_value=mock_response)

        await emb.embed_text("test input")

        call_kwargs = emb._client.aio.models.embed_content.call_args
        assert call_kwargs.kwargs["model"] == "test-m"
        assert call_kwargs.kwargs["contents"] == "test input"


# ===========================================================================
# embed_batch tests (lines 103-119)
# ===========================================================================


class TestEmbedBatch:
    async def test_embed_batch_single_batch(self, gemini_env):
        gem_mod, _, _ = gemini_env
        emb = gem_mod.GeminiEmbeddings(api_key="k", dimensions=2)

        mock_emb1 = MagicMock()
        mock_emb1.values = [1.0, 0.0]
        mock_emb2 = MagicMock()
        mock_emb2.values = [0.0, 1.0]
        mock_response = MagicMock()
        mock_response.embeddings = [mock_emb1, mock_emb2]

        emb._client.aio.models.embed_content = AsyncMock(return_value=mock_response)

        result = await emb.embed_batch(["hello", "world"])

        assert len(result) == 2
        for vec in result:
            assert len(vec) == 2
            norm = math.sqrt(sum(v * v for v in vec))
            assert abs(norm - 1.0) < 1e-5

    async def test_embed_batch_multiple_batches(self, gemini_env):
        """Test that texts exceeding _BATCH_LIMIT are split into chunks."""
        gem_mod, _, _ = gemini_env
        # Patch the batch limit to 2 for testing
        original_limit = gem_mod._BATCH_LIMIT
        gem_mod._BATCH_LIMIT = 2

        emb = gem_mod.GeminiEmbeddings(api_key="k", dimensions=2)

        def make_response(count):
            embeddings = []
            for _ in range(count):
                m = MagicMock()
                m.values = [1.0, 0.0]
                embeddings.append(m)
            resp = MagicMock()
            resp.embeddings = embeddings
            return resp

        emb._client.aio.models.embed_content = AsyncMock(
            side_effect=[make_response(2), make_response(1)]
        )

        result = await emb.embed_batch(["a", "b", "c"])

        assert len(result) == 3
        assert emb._client.aio.models.embed_content.call_count == 2

        gem_mod._BATCH_LIMIT = original_limit

    async def test_embed_batch_empty(self, gemini_env):
        gem_mod, _, _ = gemini_env
        emb = gem_mod.GeminiEmbeddings(api_key="k", dimensions=2)
        emb._client.aio.models.embed_content = AsyncMock()

        result = await emb.embed_batch([])

        assert result == []
        emb._client.aio.models.embed_content.assert_not_called()
