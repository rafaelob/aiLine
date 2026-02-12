"""ONNX export utilities for the Libras recognition model.

Provides export_to_onnx for converting the PyTorch model to ONNX format,
and create_placeholder_onnx for generating a demo model with random weights
that the frontend can use for testing inference.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .model import LibrasRecognitionModel
from .vocabulary import VOCAB_SIZE


def export_to_onnx(
    model: LibrasRecognitionModel,
    output_path: Path | str,
    quantize: bool = True,
) -> Path:
    """Export the model to ONNX format.

    For MVP, this creates a placeholder ONNX model. In production,
    this would export a trained PyTorch model.

    Args:
        model: The LibrasRecognitionModel instance.
        output_path: Where to save the .onnx file.
        quantize: Whether to apply dynamic quantization (reduces size).

    Returns:
        Path to the saved ONNX file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # For MVP, delegate to placeholder creation
    return create_placeholder_onnx(output_path, model.vocab_size)


def create_placeholder_onnx(
    output_path: Path | str,
    vocab_size: int = VOCAB_SIZE,
) -> Path:
    """Create a minimal placeholder ONNX model for frontend testing.

    The model takes input shape (batch, seq_len, 486) and outputs
    (batch, seq_len, vocab_size) log probabilities via a simple
    MatMul + Softmax + Log graph.

    Args:
        output_path: Where to save the .onnx file.
        vocab_size: Number of output classes.

    Returns:
        Path to the saved ONNX file.
    """
    try:
        import onnx
        from onnx import TensorProto, helper
    except ImportError as exc:
        msg = "onnx package required for export: pip install onnx"
        raise ImportError(msg) from exc

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    input_size = 486

    # Random projection weights (input_size -> vocab_size)
    rng = np.random.default_rng(42)
    weight_data = (rng.standard_normal((input_size, vocab_size)) * 0.01).astype(
        np.float32
    )
    bias_data = np.zeros(vocab_size, dtype=np.float32)

    # Build ONNX graph
    input_info = helper.make_tensor_value_info("input", TensorProto.FLOAT, [None, None, input_size])
    output_info = helper.make_tensor_value_info("output", TensorProto.FLOAT, [None, None, vocab_size])

    weight_init = onnx.numpy_helper.from_array(weight_data, name="weight")
    bias_init = onnx.numpy_helper.from_array(bias_data, name="bias")

    matmul_node = helper.make_node("MatMul", ["input", "weight"], ["matmul_out"])
    add_node = helper.make_node("Add", ["matmul_out", "bias"], ["logits"])
    softmax_node = helper.make_node("Softmax", ["logits"], ["probs"], axis=-1)
    log_node = helper.make_node("Log", ["probs"], ["output"])

    graph = helper.make_graph(
        [matmul_node, add_node, softmax_node, log_node],
        "libras_placeholder",
        [input_info],
        [output_info],
        initializer=[weight_init, bias_init],
    )

    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 9

    onnx.save(model, str(output_path))
    return output_path
