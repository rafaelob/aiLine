"""Tests for LandmarkDataset loading from directory tree.

Covers:
- Scanning of data_dir structure
- Missing/empty data_dir handling
- __len__ and __getitem__
- Zero-padding and truncation
- Feature extraction integration
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from ailine_runtime.ml.training.dataset import LandmarkDataset
from ailine_runtime.ml.vocabulary import LABEL_TO_ID

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_data_dir(tmp_path: Path, labels: list[str], n_samples: int = 2, seq_len: int = 20) -> Path:
    """Create a mock data directory with .npy landmark files."""
    data_dir = tmp_path / "libras_data"
    data_dir.mkdir()
    for label in labels:
        label_dir = data_dir / label
        label_dir.mkdir()
        for i in range(n_samples):
            seq = np.random.default_rng(i).standard_normal((seq_len, 162)).astype(np.float32)
            np.save(label_dir / f"sequence_{i:03d}.npy", seq)
    return data_dir


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLandmarkDataset:
    def test_nonexistent_dir_yields_empty_dataset(self, tmp_path: Path):
        ds = LandmarkDataset(tmp_path / "nonexistent")
        assert len(ds) == 0

    def test_empty_dir_yields_empty_dataset(self, tmp_path: Path):
        data_dir = tmp_path / "empty"
        data_dir.mkdir()
        ds = LandmarkDataset(data_dir)
        assert len(ds) == 0

    def test_unknown_labels_are_skipped(self, tmp_path: Path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        bad_label_dir = data_dir / "UNKNOWN_GLOSS_XYZ"
        bad_label_dir.mkdir()
        np.save(bad_label_dir / "seq.npy", np.zeros((10, 162), dtype=np.float32))
        ds = LandmarkDataset(data_dir)
        assert len(ds) == 0

    def test_valid_labels_scanned(self, tmp_path: Path):
        # Use actual vocab labels
        valid_labels = list(LABEL_TO_ID.keys())[:2]
        if len(valid_labels) < 1:
            pytest.skip("No labels in vocabulary")
        data_dir = _create_data_dir(tmp_path, valid_labels, n_samples=3)
        ds = LandmarkDataset(data_dir)
        assert len(ds) == len(valid_labels) * 3

    def test_getitem_returns_tuple(self, tmp_path: Path):
        valid_labels = list(LABEL_TO_ID.keys())[:1]
        if not valid_labels:
            pytest.skip("No labels in vocabulary")
        data_dir = _create_data_dir(tmp_path, valid_labels, n_samples=1, seq_len=15)
        ds = LandmarkDataset(data_dir, max_seq_len=60)
        features, label_id, seq_len = ds[0]
        assert isinstance(features, np.ndarray)
        assert isinstance(label_id, int)
        assert isinstance(seq_len, int)

    def test_getitem_pads_to_max_seq_len(self, tmp_path: Path):
        valid_labels = list(LABEL_TO_ID.keys())[:1]
        if not valid_labels:
            pytest.skip("No labels in vocabulary")
        data_dir = _create_data_dir(tmp_path, valid_labels, n_samples=1, seq_len=10)
        ds = LandmarkDataset(data_dir, max_seq_len=60)
        features, _, seq_len = ds[0]
        assert features.shape[0] == 60
        assert seq_len == 10
        # Padded region should be zeros
        np.testing.assert_allclose(features[seq_len:], 0.0)

    def test_getitem_truncates_long_sequences(self, tmp_path: Path):
        valid_labels = list(LABEL_TO_ID.keys())[:1]
        if not valid_labels:
            pytest.skip("No labels in vocabulary")
        data_dir = _create_data_dir(tmp_path, valid_labels, n_samples=1, seq_len=200)
        ds = LandmarkDataset(data_dir, max_seq_len=60)
        features, _, seq_len = ds[0]
        assert features.shape[0] == 60
        assert seq_len == 60

    def test_feature_dim_is_3x_landmark_dim(self, tmp_path: Path):
        """Features = position + velocity + acceleration = 3 * 162 = 486."""
        valid_labels = list(LABEL_TO_ID.keys())[:1]
        if not valid_labels:
            pytest.skip("No labels in vocabulary")
        data_dir = _create_data_dir(tmp_path, valid_labels, n_samples=1, seq_len=10)
        ds = LandmarkDataset(data_dir, max_seq_len=60)
        features, _, _ = ds[0]
        assert features.shape[1] == 486  # 162 * 3

    def test_label_id_matches_vocabulary(self, tmp_path: Path):
        valid_labels = list(LABEL_TO_ID.keys())[:1]
        if not valid_labels:
            pytest.skip("No labels in vocabulary")
        data_dir = _create_data_dir(tmp_path, valid_labels, n_samples=1)
        ds = LandmarkDataset(data_dir)
        _, label_id, _ = ds[0]
        expected_id = LABEL_TO_ID[valid_labels[0]]
        assert label_id == expected_id

    def test_files_not_dirs_are_skipped(self, tmp_path: Path):
        """Files at the top level of data_dir should be skipped (not dirs)."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "README.txt").write_text("notes")
        ds = LandmarkDataset(data_dir)
        assert len(ds) == 0
