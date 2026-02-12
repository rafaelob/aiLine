"""Tutor models — re-exports from canonical domain entities.

All model definitions live in domain/entities/tutor.py.
This module exists for backward compatibility with existing imports.
"""

from __future__ import annotations

# Re-export all tutor models from the canonical source
from ..domain.entities.tutor import (
    LearnerProfile,
    TutorAgentSpec,
    TutorMaterialsScope,
    TutorMessage,
    TutorPersona,
    TutorSession,
    TutorTurnOutput,
)

__all__ = [
    "LearnerProfile",
    "TutorAgentSpec",
    "TutorMaterialsScope",
    "TutorMessage",
    "TutorPersona",
    "TutorSession",
    "TutorTurnOutput",
]
