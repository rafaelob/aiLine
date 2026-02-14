"""Tests for QualityGate hard constraint validators (Task #8)."""

from __future__ import annotations

from typing import Literal

from ailine_runtime.accessibility.hard_constraints import (
    check_accessibility_adaptation,
    check_formative_assessment,
    check_rag_sources,
    check_reading_level,
    compute_rag_confidence,
    extract_rag_quotes,
    run_hard_constraints,
)
from ailine_runtime.accessibility.profiles import (
    AccessibilityNeeds,
    ClassAccessibilityProfile,
    LearningSupportSettings,
    SupportSettings,
)


def _make_profile(
    *,
    learning: bool = False,
    autism: bool = False,
    adhd: bool = False,
    hearing: bool = False,
    visual: bool = False,
    target_reading_level: Literal["simple", "standard"] = "simple",
) -> ClassAccessibilityProfile:
    """Build a test profile with specific needs."""
    return ClassAccessibilityProfile(
        needs=AccessibilityNeeds(
            learning=learning,
            autism=autism,
            adhd=adhd,
            hearing=hearing,
            visual=visual,
        ),
        supports=SupportSettings(
            learning=LearningSupportSettings(target_reading_level=target_reading_level),
        ),
    )


class TestCheckReadingLevel:
    """check_reading_level validates sentence complexity."""

    def test_no_profile_passes(self) -> None:
        result = check_reading_level({"steps": []}, None)
        assert result.passed is True
        assert "not applicable" in result.reason

    def test_no_learning_need_passes(self) -> None:
        profile = _make_profile(adhd=True)
        result = check_reading_level({"steps": []}, profile)
        assert result.passed is True

    def test_standard_target_passes(self) -> None:
        profile = _make_profile(learning=True, target_reading_level="standard")
        result = check_reading_level({"steps": []}, profile)
        assert result.passed is True
        assert "relaxed" in result.reason

    def test_missing_student_plan_fails(self) -> None:
        profile = _make_profile(learning=True)
        result = check_reading_level({"steps": [{"title": "A"}]}, profile)
        assert result.passed is False
        assert "student_plan missing" in result.reason

    def test_simple_text_passes(self) -> None:
        profile = _make_profile(learning=True)
        draft = {
            "student_plan": {
                "summary": ["Hoje vamos ler um texto."],
                "steps": [
                    {"instructions": ["Leia o texto.", "Faca uma lista."]},
                ],
            },
        }
        result = check_reading_level(draft, profile)
        assert result.passed is True

    def test_complex_text_fails(self) -> None:
        profile = _make_profile(learning=True)
        # Generate a draft with long sentences and complex words
        long_sentence = (
            "Os estudantes devem compreender as características fundamentais "
            "dos microrganismos multicelulares e suas interrelações "
            "com os ecossistemas biogeoquímicos contemporâneos "
            "considerando as transformações paleontológicas."
        )
        draft = {
            "student_plan": {
                "summary": [long_sentence],
                "steps": [
                    {"instructions": [long_sentence, long_sentence]},
                ],
            },
        }
        result = check_reading_level(draft, profile)
        assert result.passed is False
        assert "Reading level too high" in result.reason


class TestCheckAccessibilityAdaptation:
    """check_accessibility_adaptation ensures adaptations present."""

    def test_no_profile_passes(self) -> None:
        result = check_accessibility_adaptation({"steps": []}, None)
        assert result.passed is True

    def test_no_needs_passes(self) -> None:
        profile = _make_profile()
        result = check_accessibility_adaptation({"steps": []}, profile)
        assert result.passed is True

    def test_missing_adaptation_fails(self) -> None:
        profile = _make_profile(autism=True)
        draft = {
            "steps": [{"title": "Math", "instructions": ["Solve this."]}],
        }
        result = check_accessibility_adaptation(draft, profile)
        assert result.passed is False
        assert "missing" in result.reason.lower()

    def test_adaptation_present_passes(self) -> None:
        profile = _make_profile(autism=True)
        draft = {
            "accessibility_pack_draft": {
                "applied_adaptations": [
                    {"strategies": ["adaptação TEA: agenda visual"]}
                ],
            },
            "steps": [
                {"title": "Math", "instructions": ["Veja a adaptação UDL."]},
            ],
        }
        result = check_accessibility_adaptation(draft, profile)
        assert result.passed is True

    def test_keywords_without_section_fails(self) -> None:
        profile = _make_profile(adhd=True)
        draft = {
            "steps": [
                {"title": "TDAH lesson", "instructions": ["Use pausa e checkpoint."]},
            ],
        }
        result = check_accessibility_adaptation(draft, profile)
        assert result.passed is False  # Has keywords but no accessibility section


class TestCheckRagSources:
    """check_rag_sources validates RAG citation."""

    def test_no_rag_results_passes(self) -> None:
        result = check_rag_sources({"steps": []}, None)
        assert result.passed is True

    def test_empty_rag_results_passes(self) -> None:
        result = check_rag_sources({"steps": []}, [])
        assert result.passed is True

    def test_rag_with_citation_passes(self) -> None:
        draft = {
            "steps": [
                {"title": "Lesson", "instructions": ["Baseado em fonte oficial."]}
            ],
        }
        rag = [{"content": "...", "score": 0.8}]
        result = check_rag_sources(draft, rag)
        assert result.passed is True
        assert "cited" in result.reason.lower()

    def test_rag_with_no_sources_declaration_passes(self) -> None:
        draft = {
            "steps": [
                {"title": "Lesson", "instructions": ["Sem fontes encontradas."]}
            ],
        }
        rag = [{"content": "...", "score": 0.3}]
        result = check_rag_sources(draft, rag)
        assert result.passed is True

    def test_rag_without_citation_fails(self) -> None:
        draft = {
            "steps": [
                {"title": "Lesson", "instructions": ["Just do the math."]}
            ],
        }
        rag = [{"content": "...", "score": 0.9}]
        result = check_rag_sources(draft, rag)
        assert result.passed is False
        assert "neither cites" in result.reason.lower()


class TestCheckFormativeAssessment:
    """check_formative_assessment requires assessment items."""

    def test_with_assessment_field_passes(self) -> None:
        draft = {
            "steps": [
                {
                    "title": "Lesson",
                    "instructions": ["Read."],
                    "assessment": ["Responda: qual a ideia principal?"],
                },
            ],
        }
        result = check_formative_assessment(draft)
        assert result.passed is True

    def test_with_keywords_passes(self) -> None:
        draft = {
            "steps": [
                {"title": "Lesson", "instructions": ["Faca o quiz de autoavaliação."]},
            ],
        }
        result = check_formative_assessment(draft)
        assert result.passed is True

    def test_without_assessment_fails(self) -> None:
        draft = {
            "steps": [
                {"title": "Lesson", "instructions": ["Read the text."]},
            ],
        }
        result = check_formative_assessment(draft)
        assert result.passed is False
        assert "No formative assessment" in result.reason


class TestComputeRagConfidence:
    """compute_rag_confidence returns high/medium/low."""

    def test_no_results_low(self) -> None:
        assert compute_rag_confidence(None) == "low"
        assert compute_rag_confidence([]) == "low"

    def test_high_score_high(self) -> None:
        assert compute_rag_confidence([{"score": 0.90}]) == "high"

    def test_medium_score_medium(self) -> None:
        assert compute_rag_confidence([{"score": 0.70}, {"score": 0.65}]) == "medium"

    def test_medium_score_with_margin_high(self) -> None:
        # Top=0.75, second=0.50 -> margin=0.25 -> high
        assert compute_rag_confidence([{"score": 0.75}, {"score": 0.50}]) == "high"

    def test_low_score_low(self) -> None:
        assert compute_rag_confidence([{"score": 0.40}]) == "low"

    def test_uses_similarity_key(self) -> None:
        assert compute_rag_confidence([{"similarity": 0.90}]) == "high"


class TestExtractRagQuotes:
    """extract_rag_quotes builds provenance list."""

    def test_no_results_empty(self) -> None:
        assert extract_rag_quotes(None) == []
        assert extract_rag_quotes([]) == []

    def test_extracts_quotes(self) -> None:
        rag = [
            {"content": "Paragraph about fractions.", "title": "Math Guide", "section": "Ch 3", "score": 0.9},
            {"content": "Another paragraph.", "title": "Algebra", "heading": "Intro", "score": 0.8},
        ]
        quotes = extract_rag_quotes(rag)
        assert len(quotes) == 2
        assert quotes[0]["doc_title"] == "Math Guide"
        assert quotes[0]["section"] == "Ch 3"
        assert quotes[0]["relevance_score"] == 0.9
        assert quotes[1]["section"] == "Intro"

    def test_truncates_long_text(self) -> None:
        rag = [{"content": "x" * 500, "score": 0.7}]
        quotes = extract_rag_quotes(rag)
        assert len(quotes[0]["text"]) == 300

    def test_max_quotes(self) -> None:
        rag = [{"content": f"Para {i}", "score": 0.5} for i in range(10)]
        quotes = extract_rag_quotes(rag, max_quotes=2)
        assert len(quotes) == 2


class TestRunAllHardConstraints:
    """run_hard_constraints runs all 4 checks."""

    def test_returns_four_results(self) -> None:
        results = run_hard_constraints({"steps": []})
        assert len(results) == 4
        names = {r.name for r in results}
        assert names == {"reading_level", "accessibility_adaptation", "rag_sources_cited", "formative_assessment"}

    def test_all_pass_without_profile(self) -> None:
        draft = {
            "steps": [
                {
                    "title": "Lesson",
                    "instructions": ["Faca o quiz."],
                    "assessment": ["Responda."],
                },
            ],
        }
        results = run_hard_constraints(draft)
        # Without profile and RAG, reading_level and accessibility pass by default
        assert all(r.passed for r in results)
