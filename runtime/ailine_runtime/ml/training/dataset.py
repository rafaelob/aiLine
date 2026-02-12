"""Dataset for loading landmark sequences for Libras training.

Expects a directory structure:
  data_dir/
    {gloss_label}/
      sequence_001.npy   # shape (T, 162) — T frames of 162-dim landmarks
      sequence_002.npy
      ...
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..features import extract_features
from ..vocabulary import LABEL_TO_ID


class LandmarkDataset:
    """Loads .npy landmark sequences from a directory tree.

    Each subdirectory name is treated as a gloss label.
    Sequences are variable-length (different T per sample).
    """

    def __init__(
        self,
        data_dir: str | Path,
        max_seq_len: int = 120,
        augment: bool = False,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.max_seq_len = max_seq_len
        self.augment = augment

        self.samples: list[tuple[Path, int]] = []  # (file_path, label_id)
        self._scan()

    def _scan(self) -> None:
        """Scan data_dir for .npy files organized by gloss label."""
        if not self.data_dir.exists():
            return

        for label_dir in sorted(self.data_dir.iterdir()):
            if not label_dir.is_dir():
                continue
            label = label_dir.name.upper()
            label_id = LABEL_TO_ID.get(label)
            if label_id is None:
                continue

            for npy_file in sorted(label_dir.glob("*.npy")):
                self.samples.append((npy_file, label_id))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[np.ndarray, int, int]:
        """Load a single sample.

        Returns:
            Tuple of (features, label_id, seq_length).
            features shape: (max_seq_len, feature_dim) — zero-padded.
        """
        file_path, label_id = self.samples[idx]
        landmarks = np.load(file_path)  # (T, 162)

        # Extract features (position + velocity + acceleration)
        landmark_list = landmarks.tolist()
        features = extract_features(landmark_list)

        # Truncate or pad to max_seq_len
        seq_len = min(features.shape[0], self.max_seq_len)
        padded = np.zeros((self.max_seq_len, features.shape[1]), dtype=np.float32)
        padded[:seq_len] = features[:seq_len]

        return padded, label_id, seq_len
