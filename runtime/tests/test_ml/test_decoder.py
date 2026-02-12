"""Tests for CTC decoding and GlossBuffer."""

from __future__ import annotations

import numpy as np
import pytest

from ailine_runtime.ml.decoder import GlossBuffer, ctc_beam_search, ctc_greedy_decode
from ailine_runtime.ml.vocabulary import BLANK_TOKEN, TRANSITION_TOKEN


def _make_log_probs(tokens: list[int], vocab_size: int = 32) -> np.ndarray:
    """Create log_probs where each timestep has a strong peak at the given token."""
    n_steps = len(tokens)
    log_probs = np.full((n_steps, vocab_size), -10.0, dtype=np.float32)
    for t, tok in enumerate(tokens):
        log_probs[t, tok] = 0.0  # log(1) = 0 is the peak
    return log_probs


class TestCtcGreedyDecode:
    """Tests for greedy CTC decoding."""

    def test_empty_input(self):
        log_probs = np.empty((0, 32), dtype=np.float32)
        assert ctc_greedy_decode(log_probs) == []

    def test_invalid_dimensions_raises(self):
        with pytest.raises(ValueError, match="Expected 2D"):
            ctc_greedy_decode(np.zeros((2, 3, 4)))

    def test_all_blanks(self):
        log_probs = _make_log_probs([BLANK_TOKEN] * 5)
        assert ctc_greedy_decode(log_probs) == []

    def test_single_gloss(self):
        # Token 2 = "OI"
        log_probs = _make_log_probs([BLANK_TOKEN, 2, 2, 2, BLANK_TOKEN])
        result = ctc_greedy_decode(log_probs)
        assert result == ["OI"]

    def test_two_glosses_with_blank_separator(self):
        # 2="OI", 6="SIM"
        log_probs = _make_log_probs([2, 2, BLANK_TOKEN, 6, 6])
        result = ctc_greedy_decode(log_probs)
        assert result == ["OI", "SIM"]

    def test_transition_token_ignored(self):
        log_probs = _make_log_probs([2, TRANSITION_TOKEN, 6])
        result = ctc_greedy_decode(log_probs)
        assert result == ["OI", "SIM"]

    def test_repeated_different_glosses(self):
        log_probs = _make_log_probs([2, 6, 4])  # OI, SIM, OBRIGADO
        result = ctc_greedy_decode(log_probs)
        assert result == ["OI", "SIM", "OBRIGADO"]

    def test_custom_vocabulary(self):
        custom_vocab = {2: "HELLO", 3: "WORLD"}
        log_probs = _make_log_probs([2, BLANK_TOKEN, 3])
        result = ctc_greedy_decode(log_probs, vocabulary=custom_vocab)
        assert result == ["HELLO", "WORLD"]

    def test_unknown_token_skipped(self):
        # Token 99 is not in default vocabulary
        log_probs = _make_log_probs([2, 99, 6], vocab_size=100)
        result = ctc_greedy_decode(log_probs, vocabulary={2: "A", 6: "B"})
        assert result == ["A", "B"]


class TestCtcBeamSearch:
    """Tests for beam search CTC decoding."""

    def test_empty_input(self):
        log_probs = np.empty((0, 32), dtype=np.float32)
        assert ctc_beam_search(log_probs) == []

    def test_invalid_dimensions_raises(self):
        with pytest.raises(ValueError, match="Expected 2D"):
            ctc_beam_search(np.zeros((2, 3, 4)))

    def test_single_gloss_beam(self):
        log_probs = _make_log_probs([BLANK_TOKEN, 2, 2, BLANK_TOKEN])
        results = ctc_beam_search(log_probs, beam_width=5)
        assert len(results) > 0
        # Top result should contain "OI"
        top_glosses, _score = results[0]
        assert "OI" in top_glosses

    def test_returns_sorted_by_score(self):
        log_probs = _make_log_probs([2, BLANK_TOKEN, 6])
        results = ctc_beam_search(log_probs, beam_width=5)
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)

    def test_beam_width_limits_output(self):
        log_probs = _make_log_probs([2, 6, 4])
        results = ctc_beam_search(log_probs, beam_width=3)
        assert len(results) <= 3


class TestGlossBuffer:
    """Tests for partial/committed gloss buffering."""

    def test_initial_state_empty(self):
        buf = GlossBuffer()
        assert buf.commit() == []
        assert buf.get_partial() == []

    def test_low_confidence_stays_partial(self):
        buf = GlossBuffer(commit_threshold=0.80)
        buf.add_partial(["EU", "GOSTAR"], 0.50)
        assert buf.get_partial() == ["EU", "GOSTAR"]
        assert buf.commit() == []

    def test_high_confidence_auto_commits(self):
        buf = GlossBuffer(commit_threshold=0.80)
        buf.add_partial(["EU", "GOSTAR"], 0.90)
        # Should be committed, partial cleared
        assert buf.get_partial() == []
        committed = buf.commit()
        assert committed == ["EU", "GOSTAR"]

    def test_commit_clears_buffer(self):
        buf = GlossBuffer(commit_threshold=0.50)
        buf.add_partial(["OI"], 0.90)
        first = buf.commit()
        second = buf.commit()
        assert first == ["OI"]
        assert second == []

    def test_accumulates_multiple_commits(self):
        buf = GlossBuffer(commit_threshold=0.80)
        buf.add_partial(["OI"], 0.90)
        buf.add_partial(["SIM"], 0.85)
        committed = buf.commit()
        assert committed == ["OI", "SIM"]

    def test_partial_confidence_property(self):
        buf = GlossBuffer()
        assert buf.partial_confidence == 0.0
        buf.add_partial(["EU"], 0.65)
        assert buf.partial_confidence == 0.65

    def test_reset_clears_all(self):
        buf = GlossBuffer(commit_threshold=0.50)
        buf.add_partial(["OI"], 0.90)
        buf.add_partial(["SIM"], 0.30)
        buf.reset()
        assert buf.commit() == []
        assert buf.get_partial() == []
        assert buf.partial_confidence == 0.0

    def test_empty_glosses_not_committed(self):
        buf = GlossBuffer(commit_threshold=0.50)
        buf.add_partial([], 0.99)
        assert buf.commit() == []

    def test_exact_threshold_commits(self):
        buf = GlossBuffer(commit_threshold=0.80)
        buf.add_partial(["OBRIGADO"], 0.80)
        committed = buf.commit()
        assert committed == ["OBRIGADO"]
