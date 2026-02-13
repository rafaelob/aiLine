"""Input sanitization utilities for API boundaries.

Provides reusable functions to sanitize user-supplied text, validate
identifiers, and clean metadata before passing them to domain logic.

Security rationale:
- Prompt injection surface reduction (null bytes, extreme length)
- UUID format enforcement to prevent path traversal / ID confusion
- Metadata depth limiting to prevent DoS via deeply nested payloads
"""

from __future__ import annotations

import re
import unicodedata


# Precompiled patterns for performance.
_NULL_BYTE_RE = re.compile(r"\x00")
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def sanitize_prompt(text: str, *, max_length: int = 50_000) -> str:
    """Sanitize a user-submitted prompt string.

    1. Strip null bytes (common injection vector for C-backed parsers).
    2. Normalize unicode to NFC (canonical decomposition + composition).
    3. Strip leading/trailing whitespace.
    4. Truncate to *max_length* characters.

    Args:
        text: Raw user text.
        max_length: Maximum allowed character count (default 50 000).

    Returns:
        Cleaned text, safe for downstream processing.
    """
    # Remove null bytes
    cleaned = _NULL_BYTE_RE.sub("", text)
    # NFC normalization collapses equivalent codepoint sequences
    cleaned = unicodedata.normalize("NFC", cleaned)
    # Strip surrounding whitespace
    cleaned = cleaned.strip()
    # Enforce length limit
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def validate_teacher_id(teacher_id: str) -> str:
    """Validate that *teacher_id* is a well-formed UUID or simple identifier.

    Accepts:
    - Standard UUID format (8-4-4-4-12 hex digits).
    - Simple alphanumeric + hyphen identifiers up to 128 chars
      (e.g. ``teacher-001``) for backward compatibility with dev fixtures.

    Raises:
        ValueError: If the value is empty, too long, or contains
            characters outside ``[a-zA-Z0-9_-]``.

    Returns:
        The validated teacher_id (stripped).
    """
    tid = teacher_id.strip()
    if not tid:
        raise ValueError("teacher_id must not be empty")
    if len(tid) > 128:
        raise ValueError("teacher_id exceeds maximum length (128)")

    # Fast path: valid UUID
    if _UUID_RE.match(tid):
        return tid

    # Fallback: simple identifier (letters, digits, hyphens, underscores)
    if not re.match(r"^[a-zA-Z0-9_-]+$", tid):
        raise ValueError(
            "teacher_id must be a UUID or contain only alphanumeric "
            "characters, hyphens, and underscores"
        )
    return tid


def sanitize_metadata(
    meta: dict,
    *,
    max_depth: int = 3,
    _current_depth: int = 0,
) -> dict:
    """Deep-clean string values in a metadata dictionary.

    - String values: null bytes removed, NFC-normalized, stripped, truncated to 10 000 chars.
    - Nested dicts: recursed up to *max_depth* levels; deeper levels are dropped.
    - Lists: each element is cleaned (strings) or recursed (dicts), capped at 100 items.
    - Other scalar types (int, float, bool, None): passed through unchanged.

    Args:
        meta: The raw metadata dictionary.
        max_depth: Maximum nesting depth (default 3).

    Returns:
        A new dictionary with sanitized values.
    """
    if _current_depth >= max_depth:
        return {}

    result: dict = {}
    for key, value in meta.items():
        # Sanitize the key itself (must be a string)
        if not isinstance(key, str):
            continue
        clean_key = _sanitize_short_string(key, max_len=256)
        if not clean_key:
            continue

        result[clean_key] = _sanitize_value(
            value,
            max_depth=max_depth,
            current_depth=_current_depth,
        )
    return result


def _sanitize_value(
    value: object,
    *,
    max_depth: int,
    current_depth: int,
) -> object:
    """Recursively sanitize a single value."""
    if isinstance(value, str):
        return _sanitize_short_string(value, max_len=10_000)
    if isinstance(value, dict):
        return sanitize_metadata(
            value,
            max_depth=max_depth,
            _current_depth=current_depth + 1,
        )
    if isinstance(value, list):
        cleaned: list[object] = []
        for item in value[:100]:  # cap list length
            cleaned.append(
                _sanitize_value(
                    item,
                    max_depth=max_depth,
                    current_depth=current_depth + 1,
                )
            )
        return cleaned
    # Scalars: int, float, bool, None — pass through
    if isinstance(value, (int, float, bool, type(None))):
        return value
    # Unknown types: convert to string representation
    return _sanitize_short_string(str(value), max_len=1_000)


def _sanitize_short_string(text: str, *, max_len: int = 10_000) -> str:
    """Sanitize a short metadata string value."""
    cleaned = _NULL_BYTE_RE.sub("", text)
    cleaned = unicodedata.normalize("NFC", cleaned)
    cleaned = cleaned.strip()
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len]
    return cleaned
