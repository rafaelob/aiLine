from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "i18n"
_FALLBACK_LOCALE = "en"


@lru_cache(maxsize=8)
def _load_messages(locale: str) -> dict[str, str]:
    path = _DATA_DIR / f"{locale}.json"
    if not path.exists():
        path = _DATA_DIR / f"{_FALLBACK_LOCALE}.json"
    if not path.exists():
        return {}
    data: dict[str, str] = json.loads(path.read_text(encoding="utf-8"))
    return data


def t(key: str, locale: str = "en", **kwargs: Any) -> str:
    """Translate a key to the given locale with optional interpolation."""
    messages = _load_messages(locale)
    template = messages.get(key)
    if template is None and locale != _FALLBACK_LOCALE:
        # Fallback to English
        messages = _load_messages(_FALLBACK_LOCALE)
        template = messages.get(key)
    if template is None:
        return key  # Return the key itself as ultimate fallback
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            return template
    return template
