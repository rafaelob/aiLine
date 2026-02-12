"""CLI entry point for Libras model training.

Usage:
  uv run python -m ailine_runtime.ml.training.cli --data-dir data/libras --epochs 50
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .train import TrainConfig, train


def main(argv: list[str] | None = None) -> None:
    """Parse arguments and run training."""
    parser = argparse.ArgumentParser(
        description="Train Libras sign language recognition model"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/libras"),
        help="Directory containing labeled landmark sequences",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("models/libras"),
        help="Directory to save trained model",
    )
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--no-augment", action="store_true")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = TrainConfig(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        patience=args.patience,
        augment=not args.no_augment,
        device=args.device,
        seed=args.seed,
    )

    result = train(config)
    print(f"\nTraining complete. Best epoch: {result.best_epoch}, Best val_loss: {result.best_val_loss:.4f}")


if __name__ == "__main__":
    main()
