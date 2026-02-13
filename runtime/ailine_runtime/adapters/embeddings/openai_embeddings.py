"""OpenAI embedding adapter using the official openai SDK.

Uses ``text-embedding-3-large`` which supports a native ``dimensions``
parameter for Matryoshka truncation.  The returned vector is then
L2-normalized for consistency with the project convention.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from ...shared.observability import get_logger

if TYPE_CHECKING:
    from openai import AsyncOpenAI

_log = get_logger("ailine.adapters.embeddings.openai")

_BATCH_LIMIT = 2048  # OpenAI embeddings API max input count


class OpenAIEmbeddings:
    """Embeddings adapter backed by OpenAI embedding models.

    Args:
        model: Model identifier (default ``text-embedding-3-large``).
        api_key: OpenAI API key.  When empty, the SDK falls back to
            ``OPENAI_API_KEY`` env var.
        dimensions: Target embedding dimensionality.  Passed natively
            to the API via the ``dimensions`` parameter.
    """

    def __init__(
        self,
        *,
        model: str = "text-embedding-3-large",
        api_key: str = "",
        dimensions: int = 1536,
    ) -> None:
        from openai import AsyncOpenAI

        self._model = model
        self._dimensions = dimensions
        self._client: AsyncOpenAI = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()

    # -- Protocol properties --------------------------------------------------

    @property
    def dimensions(self) -> int:
        """Target embedding dimensionality."""
        return self._dimensions

    @property
    def model_name(self) -> str:
        """Underlying model identifier."""
        return self._model

    # -- Internal helpers -----------------------------------------------------

    @staticmethod
    def _l2_normalize(vec: np.ndarray) -> list[float]:
        """L2-normalize a vector, returning a plain list of floats."""
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec = vec / norm
        result: list[float] = vec.tolist()
        return result

    # -- Public API (matches Embeddings protocol) -----------------------------

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string.

        Returns:
            L2-normalized embedding of length ``self.dimensions``.
        """
        _log.debug("embed_text", model=self._model, text_len=len(text))

        response = await self._client.embeddings.create(
            model=self._model,
            input=text,
            dimensions=self._dimensions,
        )

        raw = np.array(response.data[0].embedding, dtype=np.float32)
        return self._l2_normalize(raw)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts, respecting the API batch limit.

        Returns:
            List of L2-normalized embeddings, one per input text.
        """
        _log.debug("embed_batch", model=self._model, count=len(texts))

        results: list[list[float]] = []

        for offset in range(0, len(texts), _BATCH_LIMIT):
            batch = texts[offset : offset + _BATCH_LIMIT]
            response = await self._client.embeddings.create(
                model=self._model,
                input=batch,
                dimensions=self._dimensions,
            )
            # The API returns data sorted by index
            sorted_data = sorted(response.data, key=lambda d: d.index)
            for item in sorted_data:
                vec = np.array(item.embedding, dtype=np.float32)
                results.append(self._l2_normalize(vec))

        return results
