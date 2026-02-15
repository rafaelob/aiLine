"""Whisper STT adapter using faster-whisper (local inference).

Uses CTranslate2-backed Whisper V3 Turbo for fast, accurate
speech-to-text.  The model is loaded lazily on first call to avoid
import overhead when the adapter is not in use (ADR-020).

Requires: ``faster-whisper>=1.2.1`` (pinned in pyproject.toml[media]).
For GPU acceleration: CUDA 12 + cuDNN 9.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import tempfile
from typing import Any


class WhisperSTT:
    """STT using faster-whisper (local inference).

    Satisfies the ``STT`` protocol from ``domain.ports.media``.

    Parameters
    ----------
    model_size:
        Model size string accepted by faster-whisper.
        ``"turbo"`` maps to Whisper V3 Turbo (ADR-020).
    device:
        ``"cpu"`` or ``"cuda"``.  CPU is the safe default.
    compute_type:
        Quantisation level.  ``"int8"`` is recommended for CPU (ADR-020).
    """

    def __init__(
        self,
        *,
        model_size: str = "turbo",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model: Any = None

    def _ensure_model(self) -> None:
        """Lazy-load the WhisperModel on first use."""
        if self._model is not None:
            return
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise ImportError(
                "faster-whisper is required for WhisperSTT. Install with: pip install 'faster-whisper>=1.2.1'"
            ) from exc
        self._model = WhisperModel(
            self._model_size,
            device=self._device,
            compute_type=self._compute_type,
        )

    async def transcribe(self, audio_bytes: bytes, *, language: str = "pt") -> str:
        """Transcribe audio bytes to text.

        Delegates to a thread-pool executor because faster-whisper is
        synchronous and CPU/GPU-bound.
        """
        self._ensure_model()
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_transcribe, audio_bytes, language)

    def _sync_transcribe(self, audio_bytes: bytes, language: str) -> str:
        """Blocking transcription called from the executor."""
        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp.flush()
                tmp_path = tmp.name

            segments, _info = self._model.transcribe(tmp_path, language=language)
            return " ".join(seg.text for seg in segments).strip()
        finally:
            if tmp_path is not None:
                with contextlib.suppress(OSError):
                    os.unlink(tmp_path)
