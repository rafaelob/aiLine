"""BiLSTM model for Libras sign language recognition with CTC output.

Architecture (ADR for Libras STT pipeline):
  - Input: (batch, seq_len, 486) — 162 landmarks * 3 (pos+vel+acc)
  - 2-layer BiLSTM with hidden_size=128
  - Linear head: 256 -> vocab_size + 2 (blank + transition)
  - Output: log probabilities for CTC loss

Model size target: <5MB for edge deployment.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .vocabulary import VOCAB_SIZE

# Default architecture parameters
DEFAULT_INPUT_SIZE = 486  # 162 landmarks * 3 (position + velocity + acceleration)
DEFAULT_HIDDEN_SIZE = 128
DEFAULT_NUM_LAYERS = 2
DEFAULT_BIDIRECTIONAL = True


class LibrasRecognitionModel:
    """Lightweight BiLSTM model for Libras gloss recognition.

    This is a numpy-based implementation for inference. For training,
    use the PyTorch-based training pipeline in ml/training/.

    The model performs:
      input (T, 486) -> BiLSTM (2 layers, hidden=128) -> Linear -> log_softmax
    """

    def __init__(
        self,
        input_size: int = DEFAULT_INPUT_SIZE,
        hidden_size: int = DEFAULT_HIDDEN_SIZE,
        num_layers: int = DEFAULT_NUM_LAYERS,
        bidirectional: bool = DEFAULT_BIDIRECTIONAL,
        vocab_size: int = VOCAB_SIZE,
    ) -> None:
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional
        self.vocab_size = vocab_size

        direction_mult = 2 if bidirectional else 1
        self.output_dim = hidden_size * direction_mult  # 256 for bidirectional

        # Initialize random weights for demo/MVP (real weights loaded via from_onnx)
        rng = np.random.default_rng(42)
        self._output_weight = (
            rng.standard_normal((vocab_size, self.output_dim)).astype(np.float32) * 0.01
        )
        self._output_bias = np.zeros(vocab_size, dtype=np.float32)

        self._onnx_session: Any = None

    @classmethod
    def from_onnx(cls, path: str | Path) -> LibrasRecognitionModel:
        """Load model from an ONNX file for inference.

        Args:
            path: Path to the .onnx model file.

        Returns:
            Model instance configured for ONNX inference.
        """
        try:
            import onnxruntime as ort
        except ImportError as exc:
            msg = "onnxruntime is required for ONNX inference: pip install onnxruntime"
            raise ImportError(msg) from exc

        model = cls()
        model._onnx_session = ort.InferenceSession(str(path))
        return model

    def forward(self, x: np.ndarray, lengths: np.ndarray | None = None) -> np.ndarray:
        """Run forward pass, returning log probabilities.

        Args:
            x: Input tensor of shape (batch, seq_len, input_size).
            lengths: Optional sequence lengths per batch element.

        Returns:
            Log probabilities of shape (batch, seq_len, vocab_size).
        """
        if self._onnx_session is not None:
            return self._forward_onnx(x, lengths)
        return self._forward_numpy(x, lengths)

    def _forward_onnx(
        self, x: np.ndarray, lengths: np.ndarray | None = None
    ) -> np.ndarray:
        """Forward pass using ONNX runtime."""
        feeds: dict[str, Any] = {"input": x.astype(np.float32)}
        if lengths is not None:
            feeds["lengths"] = lengths.astype(np.int64)
        outputs = self._onnx_session.run(None, feeds)
        result: np.ndarray = outputs[0]
        return result

    def _forward_numpy(
        self, x: np.ndarray, lengths: np.ndarray | None = None
    ) -> np.ndarray:
        """Simplified forward pass using numpy (demo/placeholder).

        This applies a simple linear projection + log_softmax to simulate
        model output. Real inference should use ONNX or PyTorch.
        """
        if x.ndim == 2:
            x = x[np.newaxis, ...]  # add batch dim

        batch_size, seq_len, _feat_dim = x.shape

        # Simple linear projection as placeholder for BiLSTM
        # Project input features down to output_dim, then to vocab
        # Use a simple hash of the input to produce somewhat varied output
        rng = np.random.default_rng(int(np.abs(x).sum() * 1000) % (2**31))
        hidden = rng.standard_normal((batch_size, seq_len, self.output_dim)).astype(
            np.float32
        )

        # Output linear layer
        logits = hidden @ self._output_weight.T + self._output_bias

        # Log softmax along vocab dimension
        logits_max = logits.max(axis=-1, keepdims=True)
        log_sum_exp = np.log(np.exp(logits - logits_max).sum(axis=-1, keepdims=True))
        log_probs: np.ndarray = logits - logits_max - log_sum_exp

        return log_probs
