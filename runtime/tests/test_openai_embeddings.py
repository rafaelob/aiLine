"""Tests for OpenAIEmbeddings adapter -- covers all uncovered lines.

Targets:
- Lines 53, 58 (dimensions, model_name properties)
- Lines 65-68 (_l2_normalize static method)
- Lines 78-87 (embed_text method)
- Lines 95-112 (embed_batch method)

Mocks the openai SDK since it is not installed.
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
# Fixtures: build a mock openai module
# ---------------------------------------------------------------------------


def _make_mock_openai():
    """Create a mock openai module with AsyncOpenAI."""
    mock_openai = ModuleType("openai")
    mock_async_client_cls = MagicMock(name="AsyncOpenAI")
    mock_openai.AsyncOpenAI = mock_async_client_cls
    return mock_openai, mock_async_client_cls


@pytest.fixture()
def openai_env():
    """Provide a fully mocked openai environment and return the adapter class."""
    mock_openai, mock_async_client_cls = _make_mock_openai()

    with patch.dict(sys.modules, {"openai": mock_openai}):
        mod_key = "ailine_runtime.adapters.embeddings.openai_embeddings"
        saved = sys.modules.pop(mod_key, None)
        try:
            import ailine_runtime.adapters.embeddings.openai_embeddings as oai_mod

            importlib.reload(oai_mod)
            yield oai_mod, mock_async_client_cls
        finally:
            if saved is not None:
                sys.modules[mod_key] = saved


# ===========================================================================
# Property tests (lines 53, 58)
# ===========================================================================


class TestOpenAIEmbeddingsProperties:
    def test_dimensions_property(self, openai_env):
        oai_mod, _ = openai_env
        emb = oai_mod.OpenAIEmbeddings(model="test-model", api_key="k", dimensions=768)
        assert emb.dimensions == 768

    def test_model_name_property(self, openai_env):
        oai_mod, _ = openai_env
        emb = oai_mod.OpenAIEmbeddings(model="my-oai-model", api_key="k")
        assert emb.model_name == "my-oai-model"

    def test_default_dimensions(self, openai_env):
        oai_mod, _ = openai_env
        emb = oai_mod.OpenAIEmbeddings(api_key="k")
        assert emb.dimensions == 1536

    def test_default_model(self, openai_env):
        oai_mod, _ = openai_env
        emb = oai_mod.OpenAIEmbeddings(api_key="k")
        assert emb.model_name == "text-embedding-3-large"


# ===========================================================================
# _l2_normalize tests (lines 65-68)
# ===========================================================================


class TestL2Normalize:
    def test_normalizes_vector(self, openai_env):
        oai_mod, _ = openai_env
        cls = oai_mod.OpenAIEmbeddings
        vec = np.array([3.0, 4.0], dtype=np.float32)
        result = cls._l2_normalize(vec)
        assert isinstance(result, list)
        norm = math.sqrt(sum(v * v for v in result))
        assert abs(norm - 1.0) < 1e-5

    def test_zero_vector_unchanged(self, openai_env):
        """A zero vector should return all zeros (no division by zero)."""
        oai_mod, _ = openai_env
        cls = oai_mod.OpenAIEmbeddings
        vec = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        result = cls._l2_normalize(vec)
        assert result == [0.0, 0.0, 0.0]

    def test_already_normalized(self, openai_env):
        oai_mod, _ = openai_env
        cls = oai_mod.OpenAIEmbeddings
        vec = np.array([0.0, 1.0], dtype=np.float32)
        result = cls._l2_normalize(vec)
        assert abs(result[0]) < 1e-6
        assert abs(result[1] - 1.0) < 1e-6


# ===========================================================================
# embed_text tests (lines 78-87)
# ===========================================================================


class TestEmbedText:
    async def test_embed_text_returns_normalized_vector(self, openai_env):
        oai_mod, _ = openai_env
        emb = oai_mod.OpenAIEmbeddings(api_key="k", dimensions=3)

        mock_data_item = MagicMock()
        mock_data_item.embedding = [3.0, 4.0, 0.0]
        mock_response = MagicMock()
        mock_response.data = [mock_data_item]

        emb._client.embeddings.create = AsyncMock(return_value=mock_response)

        result = await emb.embed_text("hello")

        assert len(result) == 3
        assert all(isinstance(v, float) for v in result)
        norm = math.sqrt(sum(v * v for v in result))
        assert abs(norm - 1.0) < 1e-5

    async def test_embed_text_calls_api_with_correct_params(self, openai_env):
        oai_mod, _ = openai_env
        emb = oai_mod.OpenAIEmbeddings(model="emb-model", api_key="k", dimensions=4)

        mock_data_item = MagicMock()
        mock_data_item.embedding = [1.0, 0.0, 0.0, 0.0]
        mock_response = MagicMock()
        mock_response.data = [mock_data_item]

        emb._client.embeddings.create = AsyncMock(return_value=mock_response)

        await emb.embed_text("test input")

        call_kwargs = emb._client.embeddings.create.call_args.kwargs
        assert call_kwargs["model"] == "emb-model"
        assert call_kwargs["input"] == "test input"
        assert call_kwargs["dimensions"] == 4


# ===========================================================================
# embed_batch tests (lines 95-112)
# ===========================================================================


class TestEmbedBatch:
    async def test_embed_batch_single_batch(self, openai_env):
        oai_mod, _ = openai_env
        emb = oai_mod.OpenAIEmbeddings(api_key="k", dimensions=2)

        item1 = MagicMock()
        item1.index = 0
        item1.embedding = [1.0, 0.0]
        item2 = MagicMock()
        item2.index = 1
        item2.embedding = [0.0, 1.0]
        mock_response = MagicMock()
        mock_response.data = [item2, item1]  # out of order to test sorting

        emb._client.embeddings.create = AsyncMock(return_value=mock_response)

        result = await emb.embed_batch(["hello", "world"])

        assert len(result) == 2
        # First result should correspond to index 0 (item1)
        assert abs(result[0][0] - 1.0) < 1e-5
        # Second result should correspond to index 1 (item2)
        assert abs(result[1][1] - 1.0) < 1e-5

    async def test_embed_batch_multiple_batches(self, openai_env):
        """Test that texts exceeding _BATCH_LIMIT are split into chunks."""
        oai_mod, _ = openai_env
        original_limit = oai_mod._BATCH_LIMIT
        oai_mod._BATCH_LIMIT = 2

        emb = oai_mod.OpenAIEmbeddings(api_key="k", dimensions=2)

        def make_response(items):
            data = []
            for i, _ in enumerate(items):
                m = MagicMock()
                m.index = i
                m.embedding = [1.0, 0.0]
                data.append(m)
            resp = MagicMock()
            resp.data = data
            return resp

        # First batch: 2 items, second batch: 1 item
        emb._client.embeddings.create = AsyncMock(
            side_effect=[make_response(["a", "b"]), make_response(["c"])]
        )

        result = await emb.embed_batch(["a", "b", "c"])

        assert len(result) == 3
        assert emb._client.embeddings.create.call_count == 2

        oai_mod._BATCH_LIMIT = original_limit

    async def test_embed_batch_empty(self, openai_env):
        oai_mod, _ = openai_env
        emb = oai_mod.OpenAIEmbeddings(api_key="k", dimensions=2)
        emb._client.embeddings.create = AsyncMock()

        result = await emb.embed_batch([])

        assert result == []
        emb._client.embeddings.create.assert_not_called()
