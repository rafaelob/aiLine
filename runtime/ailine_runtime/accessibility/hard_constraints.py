"""Deterministic hard constraint validators for QualityGate (Task #8).

These run BEFORE the LLM QualityGate and produce boolean pass/fail
results for non-negotiable requirements:

1. Reading level target met (sentence length + word complexity)
2. Accessibility adaptation present if learner profile requires it
3. RAG sources cited or explicit "no sources found"
4. Formative assessment item included

Each validator returns a HardConstraintResult with pass/fail, reason,
and optional details.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from .profiles import ClassAccessibilityProfile

# Re-export RAG provenance utilities for backward compatibility
from .rag_provenance import compute_rag_confidence, extract_rag_quotes


class HardConstraintResult(BaseModel):
    """Result of a single hard constraint check."""

    name: str = Field(..., description="Constraint identifier")
    passed: bool = Field(..., description="Whether the constraint was met")
    reason: str = Field("", description="Human-readable explanation")
    details: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# 1. Reading level target
# ---------------------------------------------------------------------------

_SIMPLE_MAX_AVG_WORDS = 14  # avg words per sentence for "simple" target
_SIMPLE_MAX_LONG_WORD_RATIO = 0.25  # max fraction of 8+ char words


def check_reading_level(
    draft: dict[str, Any],
    class_profile: ClassAccessibilityProfile | None,
) -> HardConstraintResult:
    """Check if the plan meets the reading level target.

    Uses sentence length + word complexity heuristics.
    Only enforced when the learner profile has learning needs
    with target_reading_level="simple".
    """
    # Determine if constraint applies
    if not class_profile or not class_profile.needs.learning:
        return HardConstraintResult(
            name="reading_level",
            passed=True,
            reason="No learning needs profile; reading level constraint not applicable",
        )

    target = class_profile.supports.learning.target_reading_level
    if target != "simple":
        return HardConstraintResult(
            name="reading_level",
            passed=True,
            reason=f"Target reading level is '{target}' (not simple); relaxed constraint",
        )

    # Extract student-facing text
    text = _extract_student_text(draft)
    if not text:
        return HardConstraintResult(
            name="reading_level",
            passed=False,
            reason="No student-facing text found in plan (student_plan missing)",
            details={"text_length": 0},
        )

    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    words = re.findall(r"[\wÀ-ÿ]+", text)
    n_sent = max(len(sentences), 1)
    n_words = max(len(words), 1)

    avg_wps = len(words) / n_sent
    long_ratio = sum(1 for w in words if len(w) >= 8) / n_words

    passed = avg_wps <= _SIMPLE_MAX_AVG_WORDS and long_ratio <= _SIMPLE_MAX_LONG_WORD_RATIO
    details = {
        "avg_words_per_sentence": round(avg_wps, 1),
        "long_word_ratio": round(long_ratio, 3),
        "thresholds": {
            "max_avg_words": _SIMPLE_MAX_AVG_WORDS,
            "max_long_word_ratio": _SIMPLE_MAX_LONG_WORD_RATIO,
        },
    }

    if passed:
        reason = f"Reading level OK: avg {avg_wps:.1f} words/sentence, {long_ratio:.1%} long words"
    else:
        parts = []
        if avg_wps > _SIMPLE_MAX_AVG_WORDS:
            parts.append(f"avg {avg_wps:.1f} words/sentence > {_SIMPLE_MAX_AVG_WORDS}")
        if long_ratio > _SIMPLE_MAX_LONG_WORD_RATIO:
            parts.append(f"long word ratio {long_ratio:.1%} > {_SIMPLE_MAX_LONG_WORD_RATIO:.0%}")
        reason = "Reading level too high: " + "; ".join(parts)

    return HardConstraintResult(name="reading_level", passed=passed, reason=reason, details=details)


def _extract_student_text(draft: dict[str, Any]) -> str:
    """Extract student-facing text from the draft plan."""
    parts: list[str] = []

    sp = draft.get("student_plan")
    if isinstance(sp, dict):
        parts.append(" ".join(sp.get("summary") or []))
        for step in sp.get("steps") or []:
            if isinstance(step, dict):
                parts.append(" ".join(step.get("instructions") or []))

    # Fallback: student_friendly_summary
    sfs = draft.get("student_friendly_summary")
    if isinstance(sfs, str):
        parts.append(sfs)

    return " ".join(p for p in parts if p).strip()


# ---------------------------------------------------------------------------
# 2. Accessibility adaptation present
# ---------------------------------------------------------------------------

_ADAPTATION_KEYWORDS = (
    "adaptação", "adaptacao", "adaptation", "acessibilidade",
    "accessibility", "UDL", "COGA", "TEA", "TDAH", "ADHD",
    "baixa visão", "low vision", "legenda", "transcrição",
    "alt text", "texto alternativo", "pausa", "checkpoint",
)


def check_accessibility_adaptation(
    draft: dict[str, Any],
    class_profile: ClassAccessibilityProfile | None,
) -> HardConstraintResult:
    """Check that accessibility adaptations are present when the profile requires them.

    Verifies:
    - accessibility_pack_draft or accessibility_notes exist
    - Relevant keywords appear in the plan text
    """
    if not class_profile:
        return HardConstraintResult(
            name="accessibility_adaptation",
            passed=True,
            reason="No class profile provided; adaptation constraint not applicable",
        )

    needs = class_profile.needs
    has_any_need = (
        needs.autism or needs.adhd or needs.learning
        or needs.hearing or needs.visual
        or needs.speech_language or needs.motor
    )
    if not has_any_need:
        return HardConstraintResult(
            name="accessibility_adaptation",
            passed=True,
            reason="No accessibility needs flagged in profile",
        )

    # Check for adaptation section
    has_pack = bool(draft.get("accessibility_pack_draft"))
    has_notes = bool(draft.get("accessibility_notes"))

    # Check for keywords in text
    combined = _collect_all_text(draft).lower()
    keyword_found = any(kw.lower() in combined for kw in _ADAPTATION_KEYWORDS)

    passed = (has_pack or has_notes) and keyword_found
    details = {
        "has_accessibility_pack": has_pack,
        "has_accessibility_notes": has_notes,
        "adaptation_keywords_found": keyword_found,
        "needs_flagged": {
            k: v for k, v in needs.model_dump().items()
            if isinstance(v, bool) and v
        },
    }

    if passed:
        reason = "Accessibility adaptations present for flagged needs"
    else:
        missing = []
        if not (has_pack or has_notes):
            missing.append("no accessibility_pack_draft or accessibility_notes section")
        if not keyword_found:
            missing.append("no adaptation keywords found in plan text")
        reason = "Accessibility adaptation missing: " + "; ".join(missing)

    return HardConstraintResult(
        name="accessibility_adaptation", passed=passed, reason=reason, details=details,
    )


def _collect_all_text(draft: dict[str, Any]) -> str:
    """Collect all text from the draft for keyword scanning."""
    parts: list[str] = []
    for key in ("title", "grade", "standard", "student_friendly_summary"):
        val = draft.get(key)
        if isinstance(val, str):
            parts.append(val)

    for step in draft.get("steps") or []:
        if isinstance(step, dict):
            parts.append(str(step.get("title", "")))
            parts.append(" ".join(step.get("instructions") or []))
            parts.append(" ".join(step.get("activities") or []))

    sp = draft.get("student_plan")
    if isinstance(sp, dict):
        parts.append(" ".join(sp.get("summary") or []))
        for s in sp.get("steps") or []:
            if isinstance(s, dict):
                parts.append(" ".join(s.get("instructions") or []))

    ap = draft.get("accessibility_pack_draft")
    if isinstance(ap, dict):
        parts.append(" ".join(ap.get("media_requirements") or []))
        parts.append(" ".join(ap.get("ui_recommendations") or []))
        for a in ap.get("applied_adaptations") or []:
            if isinstance(a, dict):
                parts.append(" ".join(a.get("strategies") or []))

    return " ".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# 3. RAG sources cited
# ---------------------------------------------------------------------------

_RAG_CITATION_KEYWORDS = (
    "fonte", "source", "referência", "reference", "baseado em",
    "based on", "de acordo com", "according to", "citação",
    "material", "documento", "documento de apoio",
)
_NO_SOURCES_KEYWORDS = (
    "sem fontes", "no sources", "nenhuma fonte", "não encontrado",
    "not found", "sem materiais", "no materials",
)


def check_rag_sources(
    draft: dict[str, Any],
    rag_results: list[dict[str, Any]] | None = None,
) -> HardConstraintResult:
    """Check that RAG sources are cited or explicitly marked as absent.

    When RAG retrieval happened (rag_results non-empty), the plan
    should either cite sources or explicitly state "no sources found".
    """
    if not rag_results:
        return HardConstraintResult(
            name="rag_sources_cited",
            passed=True,
            reason="No RAG retrieval performed; citation constraint not applicable",
        )

    combined = _collect_all_text(draft).lower()

    has_citation = any(kw.lower() in combined for kw in _RAG_CITATION_KEYWORDS)
    has_no_sources = any(kw.lower() in combined for kw in _NO_SOURCES_KEYWORDS)

    passed = has_citation or has_no_sources
    details = {
        "rag_results_count": len(rag_results),
        "citation_found": has_citation,
        "no_sources_declaration": has_no_sources,
    }

    if passed:
        if has_citation:
            reason = f"RAG sources cited ({len(rag_results)} results retrieved)"
        else:
            reason = "Explicit 'no sources found' declaration present"
    else:
        reason = (
            f"RAG retrieved {len(rag_results)} results but plan neither cites sources "
            "nor declares 'no sources found'"
        )

    return HardConstraintResult(
        name="rag_sources_cited", passed=passed, reason=reason, details=details,
    )


# ---------------------------------------------------------------------------
# 4. Formative assessment item included
# ---------------------------------------------------------------------------

_ASSESSMENT_KEYWORDS = (
    "avaliação", "avaliacao", "assessment", "autoavaliação",
    "self-assessment", "quiz", "questão", "questao", "pergunta",
    "verifique", "checkpoint", "reflexão", "reflita",
    "responda", "marque", "classifique", "ordene",
    "multiple choice", "multipla escolha", "verdadeiro ou falso",
    "true or false", "checklist", "rubrica", "rubric",
)


def check_formative_assessment(
    draft: dict[str, Any],
) -> HardConstraintResult:
    """Check that at least one formative assessment item is included.

    Scans steps for assessment-related keywords, or checks for
    explicit assessment fields in the draft.
    """
    # Check explicit assessment fields
    has_assessment_field = False
    for step in draft.get("steps") or []:
        if isinstance(step, dict):
            assessment = step.get("assessment")
            if assessment and isinstance(assessment, list) and len(assessment) > 0:
                has_assessment_field = True
                break

    # Check keywords
    combined = _collect_all_text(draft).lower()
    keyword_found = any(kw.lower() in combined for kw in _ASSESSMENT_KEYWORDS)

    passed = has_assessment_field or keyword_found
    details = {
        "has_assessment_field": has_assessment_field,
        "assessment_keywords_found": keyword_found,
    }

    if passed:
        reason = "Formative assessment item present"
    else:
        reason = (
            "No formative assessment found: add at least one assessment item "
            "(quiz, checkpoint, reflection question, etc.) in step.assessment"
        )

    return HardConstraintResult(
        name="formative_assessment", passed=passed, reason=reason, details=details,
    )


# ---------------------------------------------------------------------------
# Combined runner
# ---------------------------------------------------------------------------


def run_hard_constraints(
    draft: dict[str, Any],
    class_profile: ClassAccessibilityProfile | None = None,
    rag_results: list[dict[str, Any]] | None = None,
) -> list[HardConstraintResult]:
    """Run all hard constraints and return results."""
    return [
        check_reading_level(draft, class_profile),
        check_accessibility_adaptation(draft, class_profile),
        check_rag_sources(draft, rag_results),
        check_formative_assessment(draft),
    ]


__all__ = [
    "HardConstraintResult",
    "check_accessibility_adaptation",
    "check_formative_assessment",
    "check_rag_sources",
    "check_reading_level",
    "compute_rag_confidence",
    "extract_rag_quotes",
    "run_hard_constraints",
]
