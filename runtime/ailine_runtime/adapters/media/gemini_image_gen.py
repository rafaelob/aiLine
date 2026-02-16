"""Gemini/Imagen 4 image generation adapter.

Provides AI-generated educational illustrations using Google's Imagen 4
model via the google-genai SDK.  The synchronous ``generate_images`` call
is offloaded to a thread so the event loop is never blocked.

Requires: ``google-genai>=1.0`` (already a project dependency).
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from ...shared.observability import get_logger

if TYPE_CHECKING:
    from google.genai import Client

_log = get_logger("ailine.adapters.media.image_gen")

# Educational prompt templates for consistent, high-quality output.
STYLE_TEMPLATES: dict[str, str] = {
    "educational_illustration": (
        "A clear, colorful educational illustration showing {prompt}. "
        "Clean vector style, suitable for students, with labeled elements. "
        "High quality, professional."
    ),
    "infographic": (
        "A professional infographic about {prompt}. Clean layout with icons, "
        "data visualization, and clear typography. Educational and accessible."
    ),
    "diagram": (
        "A precise educational diagram of {prompt}. Clean lines, labeled "
        "components, arrows showing relationships. Suitable for textbook."
    ),
    "cartoon": (
        "A friendly, engaging cartoon illustration of {prompt}. Warm colors, "
        "inclusive characters, suitable for young learners."
    ),
    "photo_realistic": (
        "A high-quality photorealistic image of {prompt}. "
        "4K HDR, professional photography."
    ),
}

_VALID_ASPECT_RATIOS = {"1:1", "3:4", "4:3", "9:16", "16:9"}
_VALID_SIZES = {"1K", "2K"}


class GeminiImageGenerator:
    """Generate educational images using Google Imagen 4.

    Satisfies the ``ImageGenerator`` protocol from ``domain.ports.media``.

    Parameters
    ----------
    api_key:
        Google API key.  When empty the SDK falls back to the
        ``GOOGLE_API_KEY`` env var or application-default credentials.
    """

    def __init__(self, *, api_key: str = "") -> None:
        from google import genai

        self._client: Client = (
            genai.Client(api_key=api_key) if api_key else genai.Client()
        )

    async def generate(
        self,
        prompt: str,
        *,
        aspect_ratio: str = "16:9",
        style: str = "educational_illustration",
        size: str = "1K",
    ) -> bytes:
        """Generate an image from *prompt* and return raw PNG bytes.

        The synchronous ``generate_images`` SDK method is executed in a
        separate thread via ``asyncio.to_thread`` to avoid blocking.

        Raises
        ------
        ValueError
            If *aspect_ratio* or *size* are not supported values.
        RuntimeError
            If the API returns no images.
        """
        if aspect_ratio not in _VALID_ASPECT_RATIOS:
            raise ValueError(
                f"Invalid aspect_ratio '{aspect_ratio}'. "
                f"Must be one of {sorted(_VALID_ASPECT_RATIOS)}."
            )
        if size not in _VALID_SIZES:
            raise ValueError(
                f"Invalid size '{size}'. Must be one of {sorted(_VALID_SIZES)}."
            )

        template = STYLE_TEMPLATES.get(
            style, STYLE_TEMPLATES["educational_illustration"]
        )
        full_prompt = template.format(prompt=prompt)

        _log.info(
            "image_gen.request",
            style=style,
            aspect_ratio=aspect_ratio,
            size=size,
            prompt_preview=prompt[:80],
        )

        image_bytes = await asyncio.to_thread(
            self._sync_generate, full_prompt, aspect_ratio, size
        )

        _log.info("image_gen.success", byte_length=len(image_bytes))
        return image_bytes

    # -- private sync helper (runs in thread) ---------------------------------

    def _sync_generate(self, full_prompt: str, aspect_ratio: str, size: str) -> bytes:
        from google.genai import types

        response = self._client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=full_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
                image_size=size,
            ),
        )
        if not response.generated_images:
            raise RuntimeError("Imagen 4 returned no images")
        image = response.generated_images[0].image
        if image is None or image.image_bytes is None:
            raise RuntimeError("Imagen 4 returned an empty image")
        result: bytes = image.image_bytes
        return result
