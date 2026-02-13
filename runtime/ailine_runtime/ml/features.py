"""Landmark feature extraction for Libras sign language recognition.

MediaPipe produces 33 pose + 21*2 hand landmarks = 75 landmarks, each with
(x, y, z) = 225 values. We use a subset: 33 pose + 2*21 hand = 75 points
times 3 coords = 225 dimensions per frame. However, the standard compact
representation uses 54 key landmarks (subset of pose + both hands) = 162 dims.

Feature pipeline:
  1. normalize_landmarks: shoulder-centered, scale-invariant
  2. compute_velocity: first-order temporal differences
  3. compute_acceleration: second-order temporal differences
  4. extract_features: concatenate position + velocity + acceleration
"""

from __future__ import annotations

import numpy as np

# MediaPipe landmark indices for the compact representation:
# - 11,12: shoulders (used as reference)
# - 13-22: arms and hands (pose landmarks)
# - 0-20 for each hand (42 hand landmarks)
# Total: 54 landmarks * 3 = 162 dimensions

_LEFT_SHOULDER_IDX = 11
_RIGHT_SHOULDER_IDX = 12


def normalize_landmarks(
    landmarks: list[float],
    reference_points: dict[str, int] | None = None,
) -> list[float]:
    """Normalize landmarks to be shoulder-centered and scale-invariant.

    Args:
        landmarks: Flat list of (x, y, z) landmark coordinates.
            Length must be divisible by 3.
        reference_points: Optional dict mapping "left_shoulder" and
            "right_shoulder" to landmark indices. Defaults to MediaPipe
            pose landmark indices 11 and 12.

    Returns:
        Normalized landmark list of the same length.
    """
    if len(landmarks) == 0:
        return []

    if len(landmarks) % 3 != 0:
        msg = f"Landmark count must be divisible by 3, got {len(landmarks)}"
        raise ValueError(msg)

    arr = np.array(landmarks, dtype=np.float64).reshape(-1, 3)
    n_landmarks = arr.shape[0]

    # Determine reference landmark indices
    left_idx = _LEFT_SHOULDER_IDX
    right_idx = _RIGHT_SHOULDER_IDX
    if reference_points is not None:
        left_idx = reference_points.get("left_shoulder", _LEFT_SHOULDER_IDX)
        right_idx = reference_points.get("right_shoulder", _RIGHT_SHOULDER_IDX)

    # Clamp indices to valid range
    left_idx = min(left_idx, n_landmarks - 1)
    right_idx = min(right_idx, n_landmarks - 1)

    # Center on midpoint between shoulders
    center = (arr[left_idx] + arr[right_idx]) / 2.0
    arr = arr - center

    # Scale by inter-shoulder distance (prevents division by zero)
    shoulder_dist = np.linalg.norm(arr[left_idx] - arr[right_idx])
    if shoulder_dist > 1e-8:
        arr = arr / shoulder_dist

    result: list[float] = arr.flatten().tolist()
    return result


def compute_velocity(frames: list[list[float]]) -> list[list[float]]:
    """Compute first-order temporal differences (velocity) between frames.

    Args:
        frames: List of per-frame landmark vectors.

    Returns:
        Velocity vectors. First frame velocity is zero. Length matches input.
    """
    if len(frames) == 0:
        return []

    dim = len(frames[0])
    velocities: list[list[float]] = [[0.0] * dim]  # first frame = zero velocity

    for i in range(1, len(frames)):
        prev = np.array(frames[i - 1], dtype=np.float64)
        curr = np.array(frames[i], dtype=np.float64)
        vel = (curr - prev).tolist()
        velocities.append(vel)

    return velocities


def compute_acceleration(velocities: list[list[float]]) -> list[list[float]]:
    """Compute second-order temporal differences (acceleration) from velocities.

    Args:
        velocities: List of per-frame velocity vectors.

    Returns:
        Acceleration vectors. First frame acceleration is zero. Length matches input.
    """
    # Acceleration is just velocity of velocity
    return compute_velocity(velocities)


def extract_features(landmark_sequence: list[list[float]]) -> np.ndarray:
    """Extract concatenated features from a sequence of landmark frames.

    For each frame, concatenates:
      [position (162d)] + [velocity (162d)] + [acceleration (162d)] = 486d

    Args:
        landmark_sequence: List of T frames, each a flat list of landmark coords.

    Returns:
        numpy array of shape (T, 3 * D) where D is the landmark dimension.
    """
    if len(landmark_sequence) == 0:
        return np.empty((0, 0), dtype=np.float32)

    velocities = compute_velocity(landmark_sequence)
    accelerations = compute_acceleration(velocities)

    positions = np.array(landmark_sequence, dtype=np.float32)
    vels = np.array(velocities, dtype=np.float32)
    accs = np.array(accelerations, dtype=np.float32)

    # Concatenate along feature dimension: (T, D) -> (T, 3*D)
    features = np.concatenate([positions, vels, accs], axis=1)
    return features
