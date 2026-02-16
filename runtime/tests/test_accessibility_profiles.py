"""Tests for accessibility profiles and related functions.

Covers ClassAccessibilityProfile construction, human_review_flags logic,
and profile_to_prompt generation.
"""

from __future__ import annotations

import pytest

from ailine_runtime.accessibility.profiles import (
    AccessibilityNeeds,
    ADHDSupportSettings,
    AnonymousLearnerProfile,
    AutismSupportSettings,
    ClassAccessibilityProfile,
    HearingSupportSettings,
    LearningSupportSettings,
    SupportSettings,
    UiPreferences,
    VisualSupportSettings,
    human_review_flags,
    profile_to_prompt,
)

# ---------------------------------------------------------------------------
# AccessibilityNeeds
# ---------------------------------------------------------------------------


class TestAccessibilityNeeds:
    def test_defaults_all_false(self) -> None:
        needs = AccessibilityNeeds()
        assert needs.autism is False
        assert needs.adhd is False
        assert needs.learning is False
        assert needs.hearing is False
        assert needs.visual is False
        assert needs.speech_language is False
        assert needs.motor is False
        assert needs.other == []

    def test_set_specific_needs(self) -> None:
        needs = AccessibilityNeeds(autism=True, adhd=True)
        assert needs.autism is True
        assert needs.adhd is True
        assert needs.learning is False


# ---------------------------------------------------------------------------
# UiPreferences
# ---------------------------------------------------------------------------


class TestUiPreferences:
    def test_defaults(self) -> None:
        prefs = UiPreferences()
        assert prefs.low_distraction is False
        assert prefs.large_print is False
        assert prefs.high_contrast is False
        assert prefs.dyslexia_friendly is False
        assert prefs.reduce_motion is True  # default True


# ---------------------------------------------------------------------------
# Support settings
# ---------------------------------------------------------------------------


class TestAutismSupportSettings:
    def test_defaults(self) -> None:
        s = AutismSupportSettings()
        assert s.intensity == "medium"
        assert s.require_visual_schedule is True
        assert s.require_transition_scripts is True
        assert s.avoid_figurative_language is True

    def test_break_minutes_bounds(self) -> None:
        s = AutismSupportSettings(break_every_minutes=3)
        assert s.break_every_minutes == 3
        s = AutismSupportSettings(break_every_minutes=30)
        assert s.break_every_minutes == 30

    def test_break_minutes_below_minimum(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AutismSupportSettings(break_every_minutes=2)


class TestADHDSupportSettings:
    def test_defaults(self) -> None:
        s = ADHDSupportSettings()
        assert s.focus_window_minutes == 8
        assert s.require_checkpoints is True
        assert s.require_timer_prompts is True


class TestLearningSupportSettings:
    def test_defaults(self) -> None:
        s = LearningSupportSettings()
        assert s.target_reading_level == "simple"
        assert s.require_examples_first is True
        assert s.require_glossary is True


class TestHearingSupportSettings:
    def test_defaults(self) -> None:
        s = HearingSupportSettings()
        assert s.require_captions is True
        assert s.require_transcript is True
        assert s.sign_language == "none"

    def test_sign_language_options(self) -> None:
        s = HearingSupportSettings(sign_language="libras")
        assert s.sign_language == "libras"


class TestVisualSupportSettings:
    def test_defaults(self) -> None:
        s = VisualSupportSettings()
        assert s.require_alt_text is True
        assert s.require_screen_reader_structure is True
        assert s.braille_ready is False


# ---------------------------------------------------------------------------
# ClassAccessibilityProfile
# ---------------------------------------------------------------------------


class TestClassAccessibilityProfile:
    def test_empty_profile(self) -> None:
        profile = ClassAccessibilityProfile()
        assert profile.needs.autism is False
        assert profile.ui_prefs.reduce_motion is True
        assert profile.notes is None

    def test_profile_with_needs(self) -> None:
        profile = ClassAccessibilityProfile(
            needs=AccessibilityNeeds(autism=True, visual=True),
            ui_prefs=UiPreferences(large_print=True, high_contrast=True),
            notes="Low vision and autism in class.",
        )
        assert profile.needs.autism is True
        assert profile.needs.visual is True
        assert profile.ui_prefs.large_print is True
        assert profile.notes == "Low vision and autism in class."


# ---------------------------------------------------------------------------
# human_review_flags
# ---------------------------------------------------------------------------


class TestHumanReviewFlags:
    def test_none_profile(self) -> None:
        required, reasons = human_review_flags(None)
        assert required is False
        assert reasons == []

    def test_empty_profile_no_flags(self) -> None:
        profile = ClassAccessibilityProfile()
        required, reasons = human_review_flags(profile)
        assert required is False
        assert reasons == []

    def test_hearing_with_libras_triggers_review(self) -> None:
        profile = ClassAccessibilityProfile(
            needs=AccessibilityNeeds(hearing=True),
            supports=SupportSettings(
                hearing=HearingSupportSettings(sign_language="libras")
            ),
        )
        required, reasons = human_review_flags(profile)
        assert required is True
        assert len(reasons) >= 1
        assert any("sinais" in r.lower() or "intérprete" in r.lower() for r in reasons)

    def test_visual_with_braille_triggers_review(self) -> None:
        profile = ClassAccessibilityProfile(
            needs=AccessibilityNeeds(visual=True),
            supports=SupportSettings(visual=VisualSupportSettings(braille_ready=True)),
        )
        required, reasons = human_review_flags(profile)
        assert required is True
        assert any("braille" in r.lower() for r in reasons)

    def test_other_needs_triggers_review(self) -> None:
        profile = ClassAccessibilityProfile(
            needs=AccessibilityNeeds(other=["needs_aac_communication"]),
        )
        required, reasons = human_review_flags(profile)
        assert required is True
        assert any("adicionais" in r.lower() for r in reasons)

    def test_multiple_triggers_accumulate(self) -> None:
        profile = ClassAccessibilityProfile(
            needs=AccessibilityNeeds(
                hearing=True,
                visual=True,
                other=["other_need"],
            ),
            supports=SupportSettings(
                hearing=HearingSupportSettings(sign_language="asl"),
                visual=VisualSupportSettings(braille_ready=True),
            ),
        )
        required, reasons = human_review_flags(profile)
        assert required is True
        assert len(reasons) >= 3


# ---------------------------------------------------------------------------
# profile_to_prompt
# ---------------------------------------------------------------------------


class TestProfileToPrompt:
    def test_none_profile_returns_empty(self) -> None:
        result = profile_to_prompt(None, None)
        assert result == ""

    def test_empty_profile_and_no_learners(self) -> None:
        result = profile_to_prompt(None, [])
        assert result == ""

    def test_basic_profile_generates_text(self) -> None:
        profile = ClassAccessibilityProfile(
            needs=AccessibilityNeeds(autism=True, adhd=True),
        )
        result = profile_to_prompt(profile)
        assert "PERFIL DE ACESSIBILIDADE" in result
        assert "TEA=True" in result
        assert "TDAH=True" in result

    def test_profile_with_autism_details(self) -> None:
        profile = ClassAccessibilityProfile(
            needs=AccessibilityNeeds(autism=True),
        )
        result = profile_to_prompt(profile)
        assert "TEA:" in result
        assert "agenda_visual" in result

    def test_profile_with_adhd_details(self) -> None:
        profile = ClassAccessibilityProfile(
            needs=AccessibilityNeeds(adhd=True),
        )
        result = profile_to_prompt(profile)
        assert "TDAH:" in result
        assert "foco~" in result

    def test_profile_with_learning_details(self) -> None:
        """Cover line 233: learning support section in profile_to_prompt."""
        profile = ClassAccessibilityProfile(
            needs=AccessibilityNeeds(learning=True),
        )
        result = profile_to_prompt(profile)
        assert "Aprendizagem:" in result
        assert "leitura=" in result
        assert "glossario=" in result
        assert "exemplos_antes=" in result

    def test_profile_with_visual_details(self) -> None:
        """Cover line 243: visual support section in profile_to_prompt."""
        profile = ClassAccessibilityProfile(
            needs=AccessibilityNeeds(visual=True),
        )
        result = profile_to_prompt(profile)
        assert "Visual:" in result
        assert "alt_text=" in result
        assert "screen_reader=" in result
        assert "large_print=" in result
        assert "braille_ready=" in result

    def test_profile_with_hearing_details(self) -> None:
        """Cover hearing support section in profile_to_prompt."""
        profile = ClassAccessibilityProfile(
            needs=AccessibilityNeeds(hearing=True),
        )
        result = profile_to_prompt(profile)
        assert "Auditiva:" in result
        assert "captions=" in result
        assert "transcript=" in result
        assert "lingua_sinais=" in result

    def test_profile_with_learners(self) -> None:
        learners = [
            AnonymousLearnerProfile(
                label="Aluno A - baixa visao",
                needs_json={"visual": True, "large_print": True},
            ),
        ]
        result = profile_to_prompt(None, learners)
        assert "perfis anônimos" in result
        assert "Aluno A" in result

    def test_profile_with_notes(self) -> None:
        profile = ClassAccessibilityProfile(
            notes="Classe com 3 alunos com TEA.",
        )
        result = profile_to_prompt(profile)
        assert "notas:" in result
        assert "3 alunos com TEA" in result

    def test_profile_with_human_review_reasons(self) -> None:
        profile = ClassAccessibilityProfile(
            needs=AccessibilityNeeds(hearing=True),
            supports=SupportSettings(
                hearing=HearingSupportSettings(sign_language="libras")
            ),
        )
        result = profile_to_prompt(profile)
        assert "revisão humana" in result

    def test_learners_capped_at_8(self) -> None:
        learners = [
            AnonymousLearnerProfile(label=f"Aluno {i}", needs_json={"need": True})
            for i in range(12)
        ]
        result = profile_to_prompt(None, learners)
        # Should only include first 8
        assert "Aluno 7" in result
        assert "Aluno 8" not in result

    def test_rules_appended(self) -> None:
        profile = ClassAccessibilityProfile()
        result = profile_to_prompt(profile)
        assert "não diagnosticar" in result.lower()
