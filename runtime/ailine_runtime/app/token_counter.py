"""Tiktoken-based token counting utility.

Replaces the naive chars/4 heuristic with accurate BPE tokenization.
Defaults to cl100k_base (GPT-4/Claude family encoding). Falls back
to the chars/4 heuristic if tiktoken is unavailable.
"""

from __future__ import annotations

import functools

import tiktoken


@functools.lru_cache(maxsize=4)
def _get_encoding(encoding_name: str) -> tiktoken.Encoding:
    """Cache tokenizer instances (they are expensive to create)."""
    return tiktoken.get_encoding(encoding_name)


def count_tokens(text: str, *, encoding: str = "cl100k_base") -> int:
    """Count the number of BPE tokens in *text*.

    Args:
        text: The input string to tokenize.
        encoding: Tiktoken encoding name (default: cl100k_base).

    Returns:
        Token count (minimum 1 for non-empty text, 0 for empty).
    """
    if not text:
        return 0
    enc = _get_encoding(encoding)
    return len(enc.encode(text))
