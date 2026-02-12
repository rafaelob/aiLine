"""Accessibility-related domain entities.

Pure enums and types for the accessibility subsystem.
Detailed profile/settings models remain in accessibility/profiles.py
to avoid breaking existing imports.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

# Canonical definition — accessibility/profiles.py re-exports this
SupportIntensity = Literal["none", "low", "medium", "high"]


class AccessibilityNeed(StrEnum):
    """Functional accessibility needs (non-diagnostic categories)."""

    AUTISM = "autism"
    ADHD = "adhd"
    LEARNING = "learning"
    HEARING = "hearing"
    VISUAL = "visual"
    SPEECH_LANGUAGE = "speech_language"
    MOTOR = "motor"
