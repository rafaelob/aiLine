"""Gemini embedding adapter using google-genai SDK.

Uses Matryoshka truncation via native output_dimensionality parameter,
then L2-normalizes the truncated vector.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from ...shared.observability import get_logger

if TYPE_CHECKING:
    from google.genai import Client

_log = get_logger("ailine.adapters.embeddings.gemini")

_BATCH_LIMIT = 100  # Gemini API max contents per request


class GeminiEmbeddings:
    """Embeddings adapter backed by Gemini embedding models.

    Args:
        model: Model identifier (default ``gemini-embedding-001``).
        api_key: Google API key. When empty, the SDK falls back to
            ``GOOGLE_API_KEY`` env var or application-default credentials.
        dimensions: Target embedding dimensionality after Matryoshka
            truncation. The model natively supports this via
            ``output_dimensionality``.
    """

    def __init__(
        self,
        *,
        model: str = "gemini-embedding-001",
        api_key: str = "",
        dimensions: int = 3072,
    ) -> None:
        from google import genai

        self._model = model
        self._dimensions = dimensions
        self._client: Client = (
            genai.Client(api_key=api_key) if api_key else genai.Client()
        )

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

    def _embed_config(self):
        """Build an EmbedContentConfig with the target dimensionality."""
        from google.genai import types

        return types.EmbedContentConfig(output_dimensionality=self._dimensions)

    # -- Public API (matches Embeddings protocol) -----------------------------

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string.

        Returns:
            L2-normalized embedding of length ``self.dimensions``.
        """
        _log.debug("embed_text", model=self._model, text_len=len(text))

        response = await self._client.aio.models.embed_content(
            model=self._model,
            contents=text,
            config=self._embed_config(),
        )

        embeddings = response.embeddings
        if not embeddings:
            msg = "Gemini embed_content returned no embeddings"
            raise ValueError(msg)
        raw = np.array(embeddings[0].values, dtype=np.float32)
        return self._l2_normalize(raw)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts, respecting the API batch limit.

        Texts are split into chunks of up to 100 and sent sequentially.

        Returns:
            List of L2-normalized embeddings, one per input text.
        """
        _log.debug("embed_batch", model=self._model, count=len(texts))

        results: list[list[float]] = []
        config = self._embed_config()

        for offset in range(0, len(texts), _BATCH_LIMIT):
            batch = texts[offset : offset + _BATCH_LIMIT]
            response = await self._client.aio.models.embed_content(
                model=self._model,
                contents=batch,  # type: ignore[arg-type]  # google-genai accepts list[str]
                config=config,
            )
            for emb in response.embeddings or []:
                vec = np.array(emb.values, dtype=np.float32)
                results.append(self._l2_normalize(vec))

        return results
