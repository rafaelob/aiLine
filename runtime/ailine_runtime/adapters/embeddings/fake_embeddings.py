"""Deterministic fake embedding adapter for testing.

Produces repeatable, hash-based, L2-normalized vectors without calling
any external API.  Suitable for unit and integration tests that exercise
the embedding pipeline without requiring real API keys.
"""

from __future__ import annotations

import hashlib

import numpy as np


class FakeEmbeddings:
    """Deterministic, hash-based embedding provider for tests.

    The same text always produces the same embedding vector, making
    assertions stable across test runs.

    Args:
        dimensions: Length of the output vector (default 1536).
        model: Model name reported by ``model_name`` property.
    """

    def __init__(
        self,
        *,
        dimensions: int = 1536,
        model: str = "fake-embeddings-v1",
    ) -> None:
        self._dimensions = dimensions
        self._model = model

    # -- Protocol properties --------------------------------------------------

    @property
    def dimensions(self) -> int:
        """Target embedding dimensionality."""
        return self._dimensions

    @property
    def model_name(self) -> str:
        """Model identifier."""
        return self._model

    # -- Internal helpers -----------------------------------------------------

    def _hash_to_vector(self, text: str) -> list[float]:
        """Derive a deterministic, L2-normalized vector from *text*.

        Strategy: SHA-256 the text repeatedly to generate enough raw
        bytes, interpret each byte as a value in [-1, 1], truncate to
        *dimensions*, then L2-normalize.  Using bytes (not raw float32
        bit patterns) avoids NaN/Inf/overflow issues entirely.
        """
        raw = b""
        seed = text.encode("utf-8")
        while len(raw) < self._dimensions:
            digest = hashlib.sha256(seed + raw[-32:] if raw else seed).digest()
            raw += digest
            seed = digest  # chain for next iteration

        # Map each byte [0, 255] to [-1.0, 1.0]
        values = [(b / 127.5) - 1.0 for b in raw[: self._dimensions]]
        vec = np.array(values, dtype=np.float64)

        # L2-normalize
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec = vec / norm

        return vec.tolist()

    # -- Public API (matches Embeddings protocol) -----------------------------

    async def embed_text(self, text: str) -> list[float]:
        """Return a deterministic embedding for *text*."""
        return self._hash_to_vector(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return deterministic embeddings for each text in *texts*."""
        return [self._hash_to_vector(t) for t in texts]
