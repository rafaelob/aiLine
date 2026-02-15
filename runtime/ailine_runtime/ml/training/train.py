"""Training loop for the Libras recognition BiLSTM model.

Scaffold for future training runs. Uses CTC loss, supports validation
and early stopping. Requires PyTorch (optional dependency, not needed for inference).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TrainConfig:
    """Training hyperparameters."""

    data_dir: Path = Path("data/libras")
    output_dir: Path = Path("models/libras")
    epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 1e-3
    weight_decay: float = 1e-5
    max_seq_len: int = 120
    patience: int = 10  # early stopping patience
    augment: bool = True
    device: str = "cpu"
    seed: int = 42


@dataclass
class TrainResult:
    """Result of a training run."""

    best_epoch: int = 0
    best_val_loss: float = float("inf")
    final_train_loss: float = float("inf")
    history: list[dict[str, float]] = field(default_factory=list)


def train(config: TrainConfig) -> TrainResult:
    """Run the training loop.

    This is a scaffold that validates the config and returns a placeholder
    result. Full PyTorch training requires:
      pip install torch torchaudio

    Args:
        config: Training configuration.

    Returns:
        Training result with loss history.
    """
    logger.info("Training config: %s", config)
    config.output_dir.mkdir(parents=True, exist_ok=True)

    # Validate data directory
    if not config.data_dir.exists():
        logger.warning("Data directory %s does not exist — returning placeholder result", config.data_dir)
        return TrainResult()

    try:
        import torch  # noqa: F401
    except ImportError:
        logger.warning("PyTorch not installed — training scaffold only. Install with: pip install torch")
        return _placeholder_train(config)

    return _placeholder_train(config)


def _placeholder_train(config: TrainConfig) -> TrainResult:
    """Placeholder training that simulates a training run.

    In production, this would be replaced with the actual PyTorch
    training loop using CTC loss and BiLSTM model.
    """
    rng = np.random.default_rng(config.seed)
    history: list[dict[str, float]] = []

    best_val_loss = float("inf")
    best_epoch = 0

    for epoch in range(min(config.epochs, 5)):  # cap at 5 for placeholder
        train_loss = 2.0 * np.exp(-0.3 * epoch) + rng.uniform(0, 0.1)
        val_loss = 2.2 * np.exp(-0.25 * epoch) + rng.uniform(0, 0.15)

        history.append(
            {
                "epoch": epoch,
                "train_loss": float(train_loss),
                "val_loss": float(val_loss),
            }
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch

        logger.info("Epoch %d: train_loss=%.4f, val_loss=%.4f", epoch, train_loss, val_loss)

    return TrainResult(
        best_epoch=best_epoch,
        best_val_loss=best_val_loss,
        final_train_loss=history[-1]["train_loss"] if history else float("inf"),
        history=history,
    )
