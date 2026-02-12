"""Tests for LibrasRecognitionModel forward pass dimensions."""

from __future__ import annotations

import numpy as np

from ailine_runtime.ml.model import (
    DEFAULT_HIDDEN_SIZE,
    DEFAULT_INPUT_SIZE,
    DEFAULT_NUM_LAYERS,
    LibrasRecognitionModel,
)
from ailine_runtime.ml.vocabulary import VOCAB_SIZE


class TestLibrasRecognitionModel:
    """Verify model architecture and output shapes."""

    def test_default_parameters(self):
        model = LibrasRecognitionModel()
        assert model.input_size == DEFAULT_INPUT_SIZE
        assert model.hidden_size == DEFAULT_HIDDEN_SIZE
        assert model.num_layers == DEFAULT_NUM_LAYERS
        assert model.bidirectional is True
        assert model.vocab_size == VOCAB_SIZE

    def test_output_dim_bidirectional(self):
        model = LibrasRecognitionModel()
        assert model.output_dim == DEFAULT_HIDDEN_SIZE * 2  # 256

    def test_output_dim_unidirectional(self):
        model = LibrasRecognitionModel(bidirectional=False)
        assert model.output_dim == DEFAULT_HIDDEN_SIZE  # 128

    def test_forward_3d_input_shape(self):
        model = LibrasRecognitionModel()
        batch_size, seq_len = 2, 30
        x = np.random.randn(batch_size, seq_len, DEFAULT_INPUT_SIZE).astype(np.float32)
        output = model.forward(x)
        assert output.shape == (batch_size, seq_len, VOCAB_SIZE)

    def test_forward_2d_input_adds_batch(self):
        model = LibrasRecognitionModel()
        seq_len = 15
        x = np.random.randn(seq_len, DEFAULT_INPUT_SIZE).astype(np.float32)
        output = model.forward(x)
        assert output.shape == (1, seq_len, VOCAB_SIZE)

    def test_forward_output_is_log_probs(self):
        model = LibrasRecognitionModel()
        x = np.random.randn(1, 10, DEFAULT_INPUT_SIZE).astype(np.float32)
        output = model.forward(x)

        # Log probabilities should sum to ~0 in exp space (i.e., exp(output).sum ~= 1)
        for t in range(10):
            probs = np.exp(output[0, t])
            np.testing.assert_allclose(probs.sum(), 1.0, atol=1e-5)

    def test_forward_different_seq_lengths(self):
        model = LibrasRecognitionModel()
        for seq_len in [1, 10, 60, 120]:
            x = np.random.randn(1, seq_len, DEFAULT_INPUT_SIZE).astype(np.float32)
            output = model.forward(x)
            assert output.shape == (1, seq_len, VOCAB_SIZE)

    def test_custom_vocab_size(self):
        model = LibrasRecognitionModel(vocab_size=50)
        x = np.random.randn(1, 5, DEFAULT_INPUT_SIZE).astype(np.float32)
        output = model.forward(x)
        assert output.shape == (1, 5, 50)

    def test_forward_deterministic_same_input(self):
        model = LibrasRecognitionModel()
        x = np.ones((1, 5, DEFAULT_INPUT_SIZE), dtype=np.float32) * 0.5
        out1 = model.forward(x)
        out2 = model.forward(x)
        np.testing.assert_array_equal(out1, out2)
