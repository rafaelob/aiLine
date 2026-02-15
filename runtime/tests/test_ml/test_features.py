"""Tests for ML feature extraction: normalization, velocity, acceleration."""

from __future__ import annotations

import numpy as np
import pytest

from ailine_runtime.ml.features import (
    compute_acceleration,
    compute_velocity,
    extract_features,
    normalize_landmarks,
)


class TestNormalizeLandmarks:
    """Tests for shoulder-centered, scale-invariant normalization."""

    def test_empty_input(self):
        assert normalize_landmarks([]) == []

    def test_invalid_length_raises(self):
        with pytest.raises(ValueError, match="divisible by 3"):
            normalize_landmarks([1.0, 2.0])

    def test_basic_normalization_centers_on_shoulders(self):
        # 13 landmarks (indices 0-12), shoulders at 11 and 12
        landmarks = [0.0] * (13 * 3)
        # Left shoulder (idx 11) at (1.0, 0.0, 0.0)
        landmarks[11 * 3] = 1.0
        landmarks[11 * 3 + 1] = 0.0
        landmarks[11 * 3 + 2] = 0.0
        # Right shoulder (idx 12) at (3.0, 0.0, 0.0)
        landmarks[12 * 3] = 3.0
        landmarks[12 * 3 + 1] = 0.0
        landmarks[12 * 3 + 2] = 0.0

        result = normalize_landmarks(landmarks)
        arr = np.array(result).reshape(-1, 3)

        # Center should be at (2.0, 0.0, 0.0) -> shoulders at (-1.0, 0, 0) and (1.0, 0, 0)
        # Inter-shoulder distance = 2.0, so after scaling: (-0.5, 0, 0) and (0.5, 0, 0)
        np.testing.assert_allclose(arr[11], [-0.5, 0.0, 0.0], atol=1e-10)
        np.testing.assert_allclose(arr[12], [0.5, 0.0, 0.0], atol=1e-10)

    def test_custom_reference_points(self):
        landmarks = [0.0] * 12  # 4 landmarks
        landmarks[0] = 1.0  # idx 0 x
        landmarks[3] = 3.0  # idx 1 x
        result = normalize_landmarks(
            landmarks,
            reference_points={"left_shoulder": 0, "right_shoulder": 1},
        )
        arr = np.array(result).reshape(-1, 3)
        np.testing.assert_allclose(arr[0], [-0.5, 0.0, 0.0], atol=1e-10)
        np.testing.assert_allclose(arr[1], [0.5, 0.0, 0.0], atol=1e-10)

    def test_scale_invariance(self):
        # Two different scales should produce same normalized output
        base = [0.0] * (13 * 3)
        base[11 * 3] = 1.0
        base[12 * 3] = 3.0
        base[0] = 2.0  # point at center

        scaled = [v * 10.0 for v in base]

        r1 = normalize_landmarks(base)
        r2 = normalize_landmarks(scaled)
        np.testing.assert_allclose(r1, r2, atol=1e-8)

    def test_zero_shoulder_distance(self):
        # Shoulders at same position -> should not divide by zero
        landmarks = [0.0] * (13 * 3)
        landmarks[11 * 3] = 5.0
        landmarks[12 * 3] = 5.0
        result = normalize_landmarks(landmarks)
        # Should not raise; values should be centered but not scaled
        assert len(result) == len(landmarks)


class TestComputeVelocity:
    """Tests for temporal velocity computation."""

    def test_empty_input(self):
        assert compute_velocity([]) == []

    def test_single_frame(self):
        result = compute_velocity([[1.0, 2.0, 3.0]])
        assert result == [[0.0, 0.0, 0.0]]

    def test_two_frames(self):
        frames = [[1.0, 0.0], [3.0, 1.0]]
        result = compute_velocity(frames)
        assert result[0] == [0.0, 0.0]
        np.testing.assert_allclose(result[1], [2.0, 1.0])

    def test_three_frames(self):
        frames = [[0.0], [1.0], [4.0]]
        result = compute_velocity(frames)
        assert result[0] == [0.0]
        np.testing.assert_allclose(result[1], [1.0])
        np.testing.assert_allclose(result[2], [3.0])

    def test_output_length_matches_input(self):
        frames = [[1.0, 2.0]] * 5
        result = compute_velocity(frames)
        assert len(result) == 5


class TestComputeAcceleration:
    """Tests for temporal acceleration computation."""

    def test_empty_input(self):
        assert compute_acceleration([]) == []

    def test_constant_velocity(self):
        # Constant velocity -> zero acceleration
        velocities = [[1.0, 2.0]] * 4
        result = compute_acceleration(velocities)
        for accel in result:
            np.testing.assert_allclose(accel, [0.0, 0.0])

    def test_changing_velocity(self):
        velocities = [[0.0], [1.0], [3.0]]
        result = compute_acceleration(velocities)
        assert result[0] == [0.0]
        np.testing.assert_allclose(result[1], [1.0])
        np.testing.assert_allclose(result[2], [2.0])


class TestExtractFeatures:
    """Tests for full feature extraction pipeline."""

    def test_empty_input(self):
        result = extract_features([])
        assert result.shape[0] == 0

    def test_single_frame_dimensions(self):
        frame = [0.0] * 162  # 54 landmarks * 3
        result = extract_features([frame])
        assert result.shape == (1, 162 * 3)  # pos + vel + acc

    def test_multiple_frames_dimensions(self):
        frames = [[0.0] * 162] * 10
        result = extract_features(frames)
        assert result.shape == (10, 162 * 3)

    def test_features_are_float32(self):
        frames = [[1.0] * 6] * 3
        result = extract_features(frames)
        assert result.dtype == np.float32

    def test_feature_concatenation_order(self):
        # Verify that features are [position | velocity | acceleration]
        dim = 6
        frames = [[float(i)] * dim for i in range(3)]
        result = extract_features(frames)

        # Frame 0: pos=[0,0,0,0,0,0], vel=[0,0,0,0,0,0], acc=[0,0,0,0,0,0]
        np.testing.assert_allclose(result[0, :dim], [0.0] * dim)  # position
        np.testing.assert_allclose(result[0, dim : 2 * dim], [0.0] * dim)  # velocity
        np.testing.assert_allclose(result[0, 2 * dim : 3 * dim], [0.0] * dim)  # acceleration

        # Frame 1: pos=[1,1,...], vel=[1,1,...], acc=[1,1,...]
        np.testing.assert_allclose(result[1, :dim], [1.0] * dim)  # position
        np.testing.assert_allclose(result[1, dim : 2 * dim], [1.0] * dim)  # velocity
