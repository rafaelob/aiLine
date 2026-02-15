"""Tests for ML data augmentation functions.

Covers:
- speed_variation: interpolation, length change, reproducibility
- spatial_noise: noise addition, std control
- mirror_horizontal: x-coordinate negation
- random_rotation: rotation in x-y plane, angle bounds
"""

from __future__ import annotations

import numpy as np

from ailine_runtime.ml.training.augment import (
    mirror_horizontal,
    random_rotation,
    spatial_noise,
    speed_variation,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sequence(n_frames: int = 30, n_dims: int = 162) -> np.ndarray:
    """Create a deterministic landmark sequence for tests."""
    rng = np.random.default_rng(42)
    return rng.standard_normal((n_frames, n_dims)).astype(np.float32)


# ---------------------------------------------------------------------------
# speed_variation
# ---------------------------------------------------------------------------


class TestSpeedVariation:
    def test_output_shape_dims_preserved(self):
        seq = _make_sequence(30, 162)
        result = speed_variation(seq, factor_range=(0.8, 1.2), rng=np.random.default_rng(0))
        assert result.ndim == 2
        assert result.shape[1] == 162

    def test_speed_up_reduces_length(self):
        seq = _make_sequence(30, 6)
        result = speed_variation(seq, factor_range=(0.5, 0.5), rng=np.random.default_rng(0))
        assert result.shape[0] < 30

    def test_slow_down_increases_length(self):
        seq = _make_sequence(30, 6)
        result = speed_variation(seq, factor_range=(1.5, 1.5), rng=np.random.default_rng(0))
        assert result.shape[0] > 30

    def test_minimum_length_2(self):
        seq = _make_sequence(3, 6)
        result = speed_variation(seq, factor_range=(0.01, 0.01), rng=np.random.default_rng(0))
        assert result.shape[0] >= 2

    def test_reproducible_with_same_seed(self):
        seq = _make_sequence(20, 6)
        r1 = speed_variation(seq, rng=np.random.default_rng(99))
        r2 = speed_variation(seq, rng=np.random.default_rng(99))
        np.testing.assert_array_equal(r1, r2)

    def test_default_rng_when_none(self):
        seq = _make_sequence(10, 6)
        # Should not raise when rng is None
        result = speed_variation(seq, rng=None)
        assert result.shape[1] == 6


# ---------------------------------------------------------------------------
# spatial_noise
# ---------------------------------------------------------------------------


class TestSpatialNoise:
    def test_output_shape_matches_input(self):
        seq = _make_sequence(20, 6)
        result = spatial_noise(seq, std=0.01, rng=np.random.default_rng(0))
        assert result.shape == seq.shape

    def test_noise_changes_values(self):
        seq = np.ones((10, 6), dtype=np.float32)
        result = spatial_noise(seq, std=0.1, rng=np.random.default_rng(0))
        assert not np.allclose(result, seq)

    def test_zero_std_preserves_values(self):
        seq = _make_sequence(10, 6)
        result = spatial_noise(seq, std=0.0, rng=np.random.default_rng(0))
        np.testing.assert_array_equal(result, seq)

    def test_dtype_preserved(self):
        seq = _make_sequence(10, 6)
        result = spatial_noise(seq, rng=np.random.default_rng(0))
        assert result.dtype == seq.dtype

    def test_default_rng_when_none(self):
        seq = _make_sequence(10, 6)
        result = spatial_noise(seq, rng=None)
        assert result.shape == seq.shape


# ---------------------------------------------------------------------------
# mirror_horizontal
# ---------------------------------------------------------------------------


class TestMirrorHorizontal:
    def test_x_coords_negated(self):
        seq = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]], dtype=np.float32)
        result = mirror_horizontal(seq)
        # x coords at idx 0 and 3 should be negated
        np.testing.assert_allclose(result[0, 0], -1.0)
        np.testing.assert_allclose(result[0, 3], -4.0)

    def test_y_z_coords_unchanged(self):
        seq = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]], dtype=np.float32)
        result = mirror_horizontal(seq)
        np.testing.assert_allclose(result[0, 1], 2.0)
        np.testing.assert_allclose(result[0, 2], 3.0)
        np.testing.assert_allclose(result[0, 4], 5.0)
        np.testing.assert_allclose(result[0, 5], 6.0)

    def test_double_mirror_is_identity(self):
        seq = _make_sequence(10, 12)
        result = mirror_horizontal(mirror_horizontal(seq))
        np.testing.assert_allclose(result, seq, atol=1e-7)

    def test_does_not_modify_original(self):
        seq = _make_sequence(5, 6)
        original = seq.copy()
        mirror_horizontal(seq)
        np.testing.assert_array_equal(seq, original)


# ---------------------------------------------------------------------------
# random_rotation
# ---------------------------------------------------------------------------


class TestRandomRotation:
    def test_output_shape_preserved(self):
        seq = _make_sequence(20, 12)
        result = random_rotation(seq, max_angle_deg=15.0, rng=np.random.default_rng(0))
        assert result.shape == seq.shape

    def test_z_coords_unchanged(self):
        seq = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]], dtype=np.float32)
        result = random_rotation(seq, max_angle_deg=45.0, rng=np.random.default_rng(0))
        # z coords at idx 2 and 5 should be preserved
        np.testing.assert_allclose(result[0, 2], 3.0, atol=1e-6)
        np.testing.assert_allclose(result[0, 5], 6.0, atol=1e-6)

    def test_zero_angle_preserves_values(self):
        seq = _make_sequence(10, 6)
        result = random_rotation(seq, max_angle_deg=0.0, rng=np.random.default_rng(0))
        np.testing.assert_allclose(result, seq, atol=1e-6)

    def test_reproducible_with_same_seed(self):
        seq = _make_sequence(10, 12)
        r1 = random_rotation(seq, rng=np.random.default_rng(42))
        r2 = random_rotation(seq, rng=np.random.default_rng(42))
        np.testing.assert_array_equal(r1, r2)

    def test_does_not_modify_original(self):
        seq = _make_sequence(5, 6)
        original = seq.copy()
        random_rotation(seq, rng=np.random.default_rng(0))
        np.testing.assert_array_equal(seq, original)

    def test_default_rng_when_none(self):
        seq = _make_sequence(5, 6)
        result = random_rotation(seq, rng=None)
        assert result.shape == seq.shape

    def test_rotation_preserves_norms_approximately(self):
        """2D rotation preserves vector magnitudes."""
        seq = np.array([[3.0, 4.0, 0.0]], dtype=np.float32)
        result = random_rotation(seq, max_angle_deg=90.0, rng=np.random.default_rng(1))
        orig_norm = np.sqrt(seq[0, 0] ** 2 + seq[0, 1] ** 2)
        rot_norm = np.sqrt(result[0, 0] ** 2 + result[0, 1] ** 2)
        np.testing.assert_allclose(orig_norm, rot_norm, atol=1e-5)
