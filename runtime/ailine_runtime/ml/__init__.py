"""ML subsystem for Libras sign language recognition.

Provides landmark feature extraction, vocabulary management,
BiLSTM model definition, CTC decoding, and ONNX export utilities.
"""

from .decoder import GlossBuffer, ctc_beam_search, ctc_greedy_decode
from .features import (
    compute_acceleration,
    compute_velocity,
    extract_features,
    normalize_landmarks,
)
from .model import LibrasRecognitionModel
from .vocabulary import BLANK_TOKEN, LIBRAS_VOCABULARY, TRANSITION_TOKEN

__all__ = [
    "BLANK_TOKEN",
    "LIBRAS_VOCABULARY",
    "TRANSITION_TOKEN",
    "GlossBuffer",
    "LibrasRecognitionModel",
    "compute_acceleration",
    "compute_velocity",
    "ctc_beam_search",
    "ctc_greedy_decode",
    "extract_features",
    "normalize_landmarks",
]
