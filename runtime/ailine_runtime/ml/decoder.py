"""CTC decoding for Libras gloss recognition.

Provides greedy and beam search decoders, plus a GlossBuffer for
managing partial/committed gloss sequences in real-time streaming.
"""

from __future__ import annotations

import numpy as np

from .vocabulary import BLANK_TOKEN, LIBRAS_VOCABULARY, TRANSITION_TOKEN


def ctc_greedy_decode(
    log_probs: np.ndarray,
    vocabulary: dict[int, str] | None = None,
) -> list[str]:
    """Greedy CTC decoding: take argmax at each timestep, collapse repeats.

    Args:
        log_probs: Array of shape (T, vocab_size) with log probabilities.
        vocabulary: Optional mapping from token ID to label.
            Defaults to LIBRAS_VOCABULARY.

    Returns:
        List of decoded gloss labels.
    """
    if vocabulary is None:
        vocabulary = LIBRAS_VOCABULARY

    if log_probs.ndim != 2:
        msg = f"Expected 2D log_probs (T, vocab_size), got shape {log_probs.shape}"
        raise ValueError(msg)

    if log_probs.shape[0] == 0:
        return []

    best_path = np.argmax(log_probs, axis=-1)  # (T,)

    # Collapse repeated tokens and remove blanks/transitions
    decoded: list[str] = []
    prev_token = -1
    for token_id in best_path:
        token_id = int(token_id)
        if token_id == prev_token:
            continue
        prev_token = token_id
        if token_id in (BLANK_TOKEN, TRANSITION_TOKEN):
            continue
        label = vocabulary.get(token_id)
        if label is not None:
            decoded.append(label)

    return decoded


def ctc_beam_search(
    log_probs: np.ndarray,
    vocabulary: dict[int, str] | None = None,
    beam_width: int = 10,
) -> list[tuple[list[str], float]]:
    """Beam search CTC decoding.

    Args:
        log_probs: Array of shape (T, vocab_size) with log probabilities.
        vocabulary: Optional mapping from token ID to label.
        beam_width: Number of beams to maintain.

    Returns:
        List of (glosses, score) tuples sorted by score descending.
    """
    if vocabulary is None:
        vocabulary = LIBRAS_VOCABULARY

    if log_probs.ndim != 2:
        msg = f"Expected 2D log_probs (T, vocab_size), got shape {log_probs.shape}"
        raise ValueError(msg)

    if log_probs.shape[0] == 0:
        return []

    n_steps, n_vocab = log_probs.shape

    # Each beam: (prefix_tuple, last_token, cumulative_log_prob)
    # prefix_tuple stores the collapsed token sequence (excluding blanks)
    beams: list[tuple[tuple[int, ...], int, float]] = [((), BLANK_TOKEN, 0.0)]

    for t in range(n_steps):
        candidates: dict[tuple[tuple[int, ...], int], float] = {}

        for prefix, last_token, score in beams:
            for c in range(n_vocab):
                new_score = score + float(log_probs[t, c])

                if c in (BLANK_TOKEN, TRANSITION_TOKEN):
                    key = (prefix, BLANK_TOKEN)
                elif c == last_token:
                    # Repeated token: don't extend prefix
                    key = (prefix, c)
                else:
                    key = ((*prefix, c), c)

                if key not in candidates or candidates[key] < new_score:
                    candidates[key] = new_score

        # Keep top beam_width candidates
        sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
        beams = [
            (prefix, last_tok, sc)
            for (prefix, last_tok), sc in sorted_candidates[:beam_width]
        ]

    # Convert token sequences to gloss labels
    results: list[tuple[list[str], float]] = []
    seen_prefixes: set[tuple[int, ...]] = set()

    for prefix, _, score in beams:
        if prefix in seen_prefixes:
            continue
        seen_prefixes.add(prefix)

        glosses = []
        for token_id in prefix:
            label = vocabulary.get(token_id)
            if label is not None:
                glosses.append(label)

        results.append((glosses, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


class GlossBuffer:
    """Buffer for managing partial and committed gloss sequences.

    Used in real-time streaming to accumulate partial recognitions
    and commit stable sequences once confidence is sufficient.
    """

    def __init__(self, commit_threshold: float = 0.80) -> None:
        """Initialize the buffer.

        Args:
            commit_threshold: Minimum confidence to auto-commit glosses.
        """
        self._commit_threshold = commit_threshold
        self._committed: list[str] = []
        self._partial: list[str] = []
        self._partial_confidence: float = 0.0

    def add_partial(self, glosses: list[str], confidence: float) -> None:
        """Add a partial recognition result.

        Args:
            glosses: Decoded gloss labels from the latest window.
            confidence: Confidence score for this partial result.
        """
        self._partial = list(glosses)
        self._partial_confidence = confidence

        if confidence >= self._commit_threshold and glosses:
            self._committed.extend(glosses)
            self._partial = []
            self._partial_confidence = 0.0

    def commit(self) -> list[str]:
        """Return and clear committed glosses.

        Returns:
            List of committed gloss labels since last commit() call.
        """
        committed = list(self._committed)
        self._committed = []
        return committed

    def get_partial(self) -> list[str]:
        """Return current unconfirmed partial glosses.

        Returns:
            List of partial gloss labels (not yet committed).
        """
        return list(self._partial)

    @property
    def partial_confidence(self) -> float:
        """Current confidence of the partial buffer."""
        return self._partial_confidence

    def reset(self) -> None:
        """Clear all state."""
        self._committed = []
        self._partial = []
        self._partial_confidence = 0.0
