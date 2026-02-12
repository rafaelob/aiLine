"""Tests for embedding adapters.

Covers:
- FakeEmbeddings determinism, normalization, dimensions, protocol conformance.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from ailine_runtime.adapters.embeddings.fake_embeddings import FakeEmbeddings
from ailine_runtime.domain.ports.embeddings import Embeddings

# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def fake_embeddings() -> FakeEmbeddings:
    return FakeEmbeddings(dimensions=1536)


@pytest.fixture
def small_embeddings() -> FakeEmbeddings:
    """Smaller dimensions for faster assertion loops."""
    return FakeEmbeddings(dimensions=64)


# -- Protocol conformance ----------------------------------------------------


class TestProtocolConformance:
    """Verify FakeEmbeddings satisfies the Embeddings protocol."""

    def test_is_runtime_checkable(self):
        emb = FakeEmbeddings()
        assert isinstance(emb, Embeddings)

    def test_has_dimensions_property(self, fake_embeddings: FakeEmbeddings):
        assert fake_embeddings.dimensions == 1536

    def test_has_model_name_property(self, fake_embeddings: FakeEmbeddings):
        assert fake_embeddings.model_name == "fake-embeddings-v1"

    def test_custom_model_name(self):
        emb = FakeEmbeddings(model="my-test-model")
        assert emb.model_name == "my-test-model"

    def test_custom_dimensions(self):
        emb = FakeEmbeddings(dimensions=256)
        assert emb.dimensions == 256


# -- Determinism --------------------------------------------------------------


class TestDeterminism:
    """Same text must always produce the same embedding."""

    async def test_embed_text_deterministic(self, fake_embeddings: FakeEmbeddings):
        v1 = await fake_embeddings.embed_text("hello world")
        v2 = await fake_embeddings.embed_text("hello world")
        assert v1 == v2

    async def test_embed_batch_deterministic(self, fake_embeddings: FakeEmbeddings):
        texts = ["alpha", "beta", "gamma"]
        batch1 = await fake_embeddings.embed_batch(texts)
        batch2 = await fake_embeddings.embed_batch(texts)
        assert batch1 == batch2

    async def test_embed_text_matches_batch_element(self, fake_embeddings: FakeEmbeddings):
        """embed_text(x) must equal embed_batch([x])[0]."""
        text = "consistency check"
        single = await fake_embeddings.embed_text(text)
        batch = await fake_embeddings.embed_batch([text])
        assert single == batch[0]

    async def test_different_texts_different_vectors(self, fake_embeddings: FakeEmbeddings):
        v1 = await fake_embeddings.embed_text("cat")
        v2 = await fake_embeddings.embed_text("dog")
        assert v1 != v2


# -- Normalization ------------------------------------------------------------


class TestNormalization:
    """Vectors must be L2-normalized (unit length)."""

    async def test_unit_norm(self, small_embeddings: FakeEmbeddings):
        vec = await small_embeddings.embed_text("normalize me")
        norm = math.sqrt(sum(v * v for v in vec))
        assert abs(norm - 1.0) < 1e-5

    async def test_batch_all_unit_norm(self, small_embeddings: FakeEmbeddings):
        texts = ["one", "two", "three", "four"]
        batch = await small_embeddings.embed_batch(texts)
        for vec in batch:
            norm = math.sqrt(sum(v * v for v in vec))
            assert abs(norm - 1.0) < 1e-5


# -- Dimension correctness ---------------------------------------------------


class TestDimensions:
    """Output vectors must have exactly the configured dimensions."""

    async def test_embed_text_length(self, fake_embeddings: FakeEmbeddings):
        vec = await fake_embeddings.embed_text("test")
        assert len(vec) == 1536

    async def test_embed_batch_lengths(self, fake_embeddings: FakeEmbeddings):
        batch = await fake_embeddings.embed_batch(["a", "b"])
        for vec in batch:
            assert len(vec) == 1536

    async def test_small_dimensions(self, small_embeddings: FakeEmbeddings):
        vec = await small_embeddings.embed_text("small")
        assert len(vec) == 64

    async def test_various_dimensions(self):
        for dim in [32, 128, 256, 768, 3072]:
            emb = FakeEmbeddings(dimensions=dim)
            vec = await emb.embed_text("test")
            assert len(vec) == dim


# -- Edge cases ---------------------------------------------------------------


class TestEdgeCases:
    """Edge cases for robustness."""

    async def test_empty_string(self, small_embeddings: FakeEmbeddings):
        vec = await small_embeddings.embed_text("")
        assert len(vec) == 64
        norm = math.sqrt(sum(v * v for v in vec))
        assert abs(norm - 1.0) < 1e-5

    async def test_empty_batch(self, small_embeddings: FakeEmbeddings):
        result = await small_embeddings.embed_batch([])
        assert result == []

    async def test_single_element_batch(self, small_embeddings: FakeEmbeddings):
        result = await small_embeddings.embed_batch(["only"])
        assert len(result) == 1
        assert len(result[0]) == 64

    async def test_unicode_text(self, small_embeddings: FakeEmbeddings):
        vec = await small_embeddings.embed_text("educacao inclusiva")
        assert len(vec) == 64
        norm = math.sqrt(sum(v * v for v in vec))
        assert abs(norm - 1.0) < 1e-5

    async def test_very_long_text(self, small_embeddings: FakeEmbeddings):
        long_text = "word " * 10_000
        vec = await small_embeddings.embed_text(long_text)
        assert len(vec) == 64

    async def test_all_values_are_floats(self, small_embeddings: FakeEmbeddings):
        vec = await small_embeddings.embed_text("types")
        assert all(isinstance(v, float) for v in vec)

    async def test_no_nan_or_inf(self, fake_embeddings: FakeEmbeddings):
        """Vectors must not contain NaN or Inf values."""
        vec = await fake_embeddings.embed_text("safety check")
        arr = np.array(vec)
        assert not np.any(np.isnan(arr))
        assert not np.any(np.isinf(arr))
