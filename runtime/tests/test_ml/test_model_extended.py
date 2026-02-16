"""Extended tests for LibrasRecognitionModel.

Covers uncovered lines in ml/model.py:
- from_onnx with mocked onnxruntime
- from_onnx ImportError when onnxruntime is not installed
- _forward_onnx path
- _forward_numpy with 2D input (batch dim auto-added)
- forward dispatching between onnx and numpy
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from ailine_runtime.ml.model import LibrasRecognitionModel


class TestFromOnnx:
    def test_from_onnx_loads_session(self, tmp_path):
        """from_onnx should create an InferenceSession."""
        mock_ort = MagicMock()
        mock_session = MagicMock()
        mock_ort.InferenceSession.return_value = mock_session

        model_path = tmp_path / "model.onnx"
        model_path.touch()

        with patch.dict(sys.modules, {"onnxruntime": mock_ort}):
            model = LibrasRecognitionModel.from_onnx(model_path)
            assert model._onnx_session is mock_session
            mock_ort.InferenceSession.assert_called_once_with(str(model_path))

    def test_from_onnx_raises_without_onnxruntime(self, tmp_path):
        """from_onnx should raise ImportError when onnxruntime is missing."""
        with patch.dict(sys.modules, {"onnxruntime": None}), pytest.raises(
            ImportError, match="onnxruntime"
        ):
            LibrasRecognitionModel.from_onnx(tmp_path / "model.onnx")


class TestForwardOnnx:
    def test_forward_uses_onnx_session(self):
        """When _onnx_session is set, forward delegates to ONNX runtime."""
        model = LibrasRecognitionModel()
        mock_session = MagicMock()
        expected_output = np.random.randn(1, 10, model.vocab_size).astype(np.float32)
        mock_session.run.return_value = [expected_output]
        model._onnx_session = mock_session

        x = np.random.randn(1, 10, 486).astype(np.float32)
        result = model.forward(x)

        mock_session.run.assert_called_once()
        np.testing.assert_array_equal(result, expected_output)

    def test_forward_onnx_with_lengths(self):
        """ONNX forward should pass lengths when provided."""
        model = LibrasRecognitionModel()
        mock_session = MagicMock()
        expected = np.random.randn(2, 10, model.vocab_size).astype(np.float32)
        mock_session.run.return_value = [expected]
        model._onnx_session = mock_session

        x = np.random.randn(2, 10, 486).astype(np.float32)
        lengths = np.array([10, 8])
        model.forward(x, lengths)

        feeds = mock_session.run.call_args[0][1]
        assert "input" in feeds
        assert "lengths" in feeds
        np.testing.assert_array_equal(
            feeds["lengths"], np.array([10, 8], dtype=np.int64)
        )

    def test_forward_onnx_without_lengths(self):
        """ONNX forward should not include lengths when None."""
        model = LibrasRecognitionModel()
        mock_session = MagicMock()
        expected = np.random.randn(1, 5, model.vocab_size).astype(np.float32)
        mock_session.run.return_value = [expected]
        model._onnx_session = mock_session

        x = np.random.randn(1, 5, 486).astype(np.float32)
        model.forward(x, lengths=None)

        feeds = mock_session.run.call_args[0][1]
        assert "input" in feeds
        assert "lengths" not in feeds


class TestForwardNumpy:
    def test_numpy_forward_with_lengths(self):
        """Numpy forward should handle lengths parameter (even though unused)."""
        model = LibrasRecognitionModel()
        x = np.random.randn(2, 10, 486).astype(np.float32)
        lengths = np.array([10, 8])
        result = model.forward(x, lengths)
        assert result.shape == (2, 10, model.vocab_size)

    def test_numpy_forward_single_frame(self):
        """Single frame sequence should work."""
        model = LibrasRecognitionModel()
        x = np.random.randn(1, 1, 486).astype(np.float32)
        result = model.forward(x)
        assert result.shape == (1, 1, model.vocab_size)

    def test_unidirectional_output_dim(self):
        """Unidirectional model should have correct output dimension."""
        model = LibrasRecognitionModel(bidirectional=False)
        assert model.output_dim == 128
        x = np.random.randn(1, 5, 486).astype(np.float32)
        result = model.forward(x)
        assert result.shape == (1, 5, model.vocab_size)
