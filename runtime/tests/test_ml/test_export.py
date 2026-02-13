"""Tests for ONNX export utilities.

Covers:
- export_to_onnx (delegates to create_placeholder)
- create_placeholder_onnx (requires onnx package)
- ImportError handling when onnx is not installed
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ailine_runtime.ml.model import LibrasRecognitionModel


class TestExportToOnnx:
    def test_creates_output_directory(self, tmp_path: Path):
        """export_to_onnx should create parent dirs if missing."""
        # Mock onnx package since it may not be installed
        mock_onnx = MagicMock()
        mock_helper = MagicMock()
        mock_numpy_helper = MagicMock()
        mock_onnx.helper = mock_helper
        mock_onnx.numpy_helper = mock_numpy_helper
        mock_onnx.TensorProto = MagicMock()
        mock_onnx.TensorProto.FLOAT = 1

        modules = {"onnx": mock_onnx, "onnx.helper": mock_helper, "onnx.numpy_helper": mock_numpy_helper}
        with patch.dict(sys.modules, modules):
            from ailine_runtime.ml.export import export_to_onnx

            model = LibrasRecognitionModel()
            output = tmp_path / "models" / "test_model.onnx"
            export_to_onnx(model, output)
            # Parent dir should be created
            assert output.parent.exists()

    def test_import_error_without_onnx(self, tmp_path: Path):
        """Should raise ImportError when onnx is not installed."""
        with patch.dict(sys.modules, {"onnx": None}):
            # Need to reimport to pick up the mocked module
            import importlib

            import ailine_runtime.ml.export as export_mod
            importlib.reload(export_mod)

            with pytest.raises(ImportError, match="onnx"):
                export_mod.create_placeholder_onnx(tmp_path / "test.onnx")


class TestCreatePlaceholderOnnx:
    def test_creates_file_with_mock(self, tmp_path: Path):
        """Test placeholder creation flow with mocked onnx."""
        mock_onnx = MagicMock()
        mock_helper = MagicMock()
        mock_numpy_helper = MagicMock()
        mock_onnx.helper = mock_helper
        mock_onnx.numpy_helper = mock_numpy_helper
        mock_onnx.TensorProto = MagicMock()
        mock_onnx.TensorProto.FLOAT = 1

        with patch.dict(sys.modules, {"onnx": mock_onnx}):
            from ailine_runtime.ml.export import create_placeholder_onnx

            output = tmp_path / "placeholder.onnx"
            result = create_placeholder_onnx(output)
            assert result == output
            mock_onnx.save.assert_called_once()

    def test_custom_vocab_size(self, tmp_path: Path):
        """Placeholder should respect custom vocab_size."""
        mock_onnx = MagicMock()
        mock_helper = MagicMock()
        mock_numpy_helper = MagicMock()
        mock_onnx.helper = mock_helper
        mock_onnx.numpy_helper = mock_numpy_helper
        mock_onnx.TensorProto = MagicMock()
        mock_onnx.TensorProto.FLOAT = 1

        with patch.dict(sys.modules, {"onnx": mock_onnx}):
            from ailine_runtime.ml.export import create_placeholder_onnx

            output = tmp_path / "custom.onnx"
            create_placeholder_onnx(output, vocab_size=50)
            # The function should complete without error
            mock_onnx.save.assert_called_once()
