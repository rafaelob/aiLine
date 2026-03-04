from __future__ import annotations

from typing import Tuple


def head_tail(text: str, head_chars: int = 2000, tail_chars: int = 800) -> str:
    if len(text) <= head_chars + tail_chars + 50:
        return text
    return text[:head_chars] + "\n\n… (truncado) …\n\n" + text[-tail_chars:]


def clamp(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…"
