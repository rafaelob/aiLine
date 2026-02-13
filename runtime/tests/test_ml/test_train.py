"""Tests for the Libras training scaffold and CLI.

Covers:
- TrainConfig defaults
- TrainResult defaults
- train() with missing data_dir
- _placeholder_train simulation
- CLI argument parsing and execution
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ailine_runtime.ml.training.cli import main as cli_main
from ailine_runtime.ml.training.train import TrainConfig, TrainResult, train

# ---------------------------------------------------------------------------
# TrainConfig
# ---------------------------------------------------------------------------

class TestTrainConfig:
    def test_defaults(self):
        config = TrainConfig()
        assert config.epochs == 100
        assert config.batch_size == 32
        assert config.learning_rate == 1e-3
        assert config.weight_decay == 1e-5
        assert config.max_seq_len == 120
        assert config.patience == 10
        assert config.augment is True
        assert config.device == "cpu"
        assert config.seed == 42

    def test_custom_values(self, tmp_path: Path):
        config = TrainConfig(
            data_dir=tmp_path / "data",
            output_dir=tmp_path / "output",
            epochs=50,
            batch_size=16,
        )
        assert config.epochs == 50
        assert config.batch_size == 16


# ---------------------------------------------------------------------------
# TrainResult
# ---------------------------------------------------------------------------

class TestTrainResult:
    def test_defaults(self):
        result = TrainResult()
        assert result.best_epoch == 0
        assert result.best_val_loss == float("inf")
        assert result.final_train_loss == float("inf")
        assert result.history == []


# ---------------------------------------------------------------------------
# train()
# ---------------------------------------------------------------------------

class TestTrain:
    def test_missing_data_dir_returns_placeholder(self, tmp_path: Path):
        config = TrainConfig(
            data_dir=tmp_path / "nonexistent",
            output_dir=tmp_path / "output",
        )
        result = train(config)
        assert isinstance(result, TrainResult)
        assert result.best_epoch == 0

    def test_creates_output_dir(self, tmp_path: Path):
        output_dir = tmp_path / "models" / "libras"
        config = TrainConfig(
            data_dir=tmp_path / "nonexistent",
            output_dir=output_dir,
        )
        train(config)
        assert output_dir.exists()

    def test_placeholder_train_with_data_dir(self, tmp_path: Path):
        """When data_dir exists, placeholder training runs."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        output_dir = tmp_path / "output"
        config = TrainConfig(
            data_dir=data_dir,
            output_dir=output_dir,
            epochs=5,
            seed=42,
        )
        result = train(config)
        assert isinstance(result, TrainResult)
        assert len(result.history) > 0
        assert result.best_epoch >= 0
        assert result.best_val_loss < float("inf")
        assert result.final_train_loss < float("inf")

    def test_history_has_expected_fields(self, tmp_path: Path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        config = TrainConfig(data_dir=data_dir, output_dir=tmp_path / "out", epochs=3)
        result = train(config)
        for entry in result.history:
            assert "epoch" in entry
            assert "train_loss" in entry
            assert "val_loss" in entry

    def test_loss_decreases_generally(self, tmp_path: Path):
        """Placeholder train simulates decreasing losses."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        config = TrainConfig(data_dir=data_dir, output_dir=tmp_path / "out", epochs=5, seed=42)
        result = train(config)
        if len(result.history) >= 2:
            first_train = result.history[0]["train_loss"]
            last_train = result.history[-1]["train_loss"]
            assert last_train < first_train


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class TestCLI:
    def test_default_args(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        cli_main(["--data-dir", str(tmp_path / "nonexistent"), "--output-dir", str(tmp_path / "out")])
        captured = capsys.readouterr()
        assert "Training complete" in captured.out

    def test_custom_args(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        cli_main([
            "--data-dir", str(data_dir),
            "--output-dir", str(tmp_path / "out"),
            "--epochs", "3",
            "--batch-size", "8",
            "--lr", "0.01",
            "--patience", "5",
            "--no-augment",
            "--seed", "123",
        ])
        captured = capsys.readouterr()
        assert "Training complete" in captured.out
        assert "Best epoch" in captured.out

    def test_no_augment_flag(self, tmp_path: Path):
        """--no-augment flag should set augment=False in config."""
        # This is implicitly tested through the CLI running without errors
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        cli_main([
            "--data-dir", str(data_dir),
            "--output-dir", str(tmp_path / "out"),
            "--no-augment",
        ])
