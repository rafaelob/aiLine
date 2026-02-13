"""Data augmentation for landmark sequences.

Augmentations preserve the semantic meaning of signs while
increasing training data diversity. All operate on numpy arrays
of shape (T, D) where T is frames and D is landmark dimensions.
"""

from __future__ import annotations

import numpy as np


def speed_variation(
    sequence: np.ndarray,
    factor_range: tuple[float, float] = (0.8, 1.2),
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Randomly speed up or slow down the sequence via interpolation.

    Args:
        sequence: Array of shape (T, D).
        factor_range: Min and max speed factors.
        rng: Random generator for reproducibility.

    Returns:
        Resampled sequence with adjusted length.
    """
    if rng is None:
        rng = np.random.default_rng()

    n_frames, n_dims = sequence.shape
    factor = rng.uniform(*factor_range)
    new_len = max(2, int(n_frames * factor))

    old_indices = np.linspace(0, n_frames - 1, new_len)
    new_sequence = np.zeros((new_len, n_dims), dtype=sequence.dtype)

    for d in range(n_dims):
        new_sequence[:, d] = np.interp(old_indices, np.arange(n_frames), sequence[:, d])

    return new_sequence


def spatial_noise(
    sequence: np.ndarray,
    std: float = 0.01,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Add Gaussian noise to landmark coordinates.

    Args:
        sequence: Array of shape (T, D).
        std: Standard deviation of the noise.
        rng: Random generator for reproducibility.

    Returns:
        Noisy copy of the sequence.
    """
    if rng is None:
        rng = np.random.default_rng()

    noise = rng.normal(0.0, std, size=sequence.shape).astype(sequence.dtype)
    result: np.ndarray = sequence + noise
    return result


def mirror_horizontal(sequence: np.ndarray) -> np.ndarray:
    """Mirror landmarks horizontally (negate x coordinates).

    Assumes landmarks are stored as (x, y, z) triples,
    so x is at indices 0, 3, 6, ...

    Args:
        sequence: Array of shape (T, D) where D is divisible by 3.

    Returns:
        Horizontally mirrored copy.
    """
    mirrored = sequence.copy()
    # Negate x coordinates (every 3rd starting from 0)
    mirrored[:, 0::3] = -mirrored[:, 0::3]
    return mirrored


def random_rotation(
    sequence: np.ndarray,
    max_angle_deg: float = 15.0,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Apply a small random rotation in the x-y plane.

    Args:
        sequence: Array of shape (T, D) where D is divisible by 3.
        max_angle_deg: Maximum rotation angle in degrees.
        rng: Random generator for reproducibility.

    Returns:
        Rotated copy of the sequence.
    """
    if rng is None:
        rng = np.random.default_rng()

    angle = rng.uniform(-max_angle_deg, max_angle_deg)
    rad = np.radians(angle)
    cos_a, sin_a = np.cos(rad), np.sin(rad)

    rotated = sequence.copy()
    _n_frames, n_dims = sequence.shape
    n_landmarks = n_dims // 3

    for i in range(n_landmarks):
        x_idx = i * 3
        y_idx = i * 3 + 1
        x = sequence[:, x_idx]
        y = sequence[:, y_idx]
        rotated[:, x_idx] = cos_a * x - sin_a * y
        rotated[:, y_idx] = sin_a * x + cos_a * y

    return rotated
