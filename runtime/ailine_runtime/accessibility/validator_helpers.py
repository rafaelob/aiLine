"""Helper functions and keyword constants for accessibility validation.

Extracted from validator.py for single-responsibility: keyword tuples,
text collection, readability heuristics, and cognitive load bucketing.
"""

from __future__ import annotations

import re
from typing import Any

# ----------------------------
# Keyword tuples (cheap heuristics)
# ----------------------------

BREAK_KEYWORDS = (
    "pausa", "intervalo", "break", "movimento",
    "alongamento", "respiração", "relax", "hidrata",
)
TRANSITION_KEYWORDS = (
    "agora", "em seguida", "próximo", "depois",
    "transição", "mudança", "vamos", "a seguir",
)
CHECKPOINT_KEYWORDS = (
    "checkpoint", "verifique", "confira", "checagem", "feito", "ok",
    "\u2713", "autoavalia", "responda 1",
)
EXAMPLE_KEYWORDS = ("exemplo", "modelo", "mostre", "demonstre", "veja", "como fazer")
GLOSSARY_KEYWORDS = ("glossário", "vocabulário", "termos", "palavras-chave")
ALT_TEXT_KEYWORDS = ("texto alternativo", "alt text", "descrição da imagem", "descrever a imagem")
CAPTION_KEYWORDS = ("legenda", "legendado", "captions")
TRANSCRIPT_KEYWORDS = ("transcrição", "transcript")
AUDIO_DESC_KEYWORDS = ("audiodescrição", "audio description", "descrição do vídeo")

MEDIA_MENTION_KEYWORDS = (
    "vídeo", "video", "áudio", "audio", "podcast",
    "gravação", "imagem", "figura", "slide", "foto", "ilustração",
)


def collect_text(draft: dict[str, Any]) -> str:
    """Extract a representative corpus to score readability/cognitive load."""
    parts: list[str] = []
    for k in ("title", "grade", "standard"):
        if isinstance(draft.get(k), str):
            parts.append(draft[k])

    objectives = draft.get("objectives") or []
    if isinstance(objectives, list):
        for o in objectives:
            if isinstance(o, dict):
                parts.append(str(o.get("text", "")))
            else:
                parts.append(str(o))

    # Student-facing: prefer student_plan if present
    student_plan = draft.get("student_plan")
    if isinstance(student_plan, dict):
        parts.append(" ".join(student_plan.get("summary") or []))
        for s in student_plan.get("steps") or []:
            if isinstance(s, dict):
                parts.append(" ".join(s.get("instructions") or []))

    # Teacher-facing: steps
    steps = draft.get("steps") or []
    if isinstance(steps, list):
        for step in steps:
            if not isinstance(step, dict):
                continue
            parts.append(str(step.get("title", "")))
            parts.append(" ".join(step.get("instructions") or []))
            parts.append(" ".join(step.get("activities") or []))
            parts.append(" ".join(step.get("assessment") or []))

    # Accessibility pack
    ap = draft.get("accessibility_pack_draft") or {}
    if isinstance(ap, dict):
        parts.append(" ".join(ap.get("media_requirements") or []))
        parts.append(" ".join(ap.get("ui_recommendations") or []))
        for a in ap.get("applied_adaptations") or []:
            if isinstance(a, dict):
                parts.append(" ".join(a.get("strategies") or []))
                parts.append(" ".join(a.get("do_not") or []))
                parts.append(" ".join(a.get("notes") or []))

    return " ".join([p for p in parts if p]).strip()


def contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    """Check if text contains any of the given keywords (case-insensitive)."""
    t = text.lower()
    return any(k in t for k in keywords)


def readability_metrics(text: str) -> dict[str, float]:
    """Lightweight (language-agnostic) readability heuristics."""
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    words = re.findall(r"[\wÀ-ÿ]+", text)
    if not sentences:
        sentences = [text] if text else []
    n_sent = max(len(sentences), 1)
    n_words = max(len(words), 1)

    avg_words_per_sentence = len(words) / n_sent
    avg_chars_per_word = sum(len(w) for w in words) / n_words
    long_words = sum(1 for w in words if len(w) >= 8) / n_words

    return {
        "sentences": float(len(sentences)),
        "words": float(len(words)),
        "avg_words_per_sentence": float(avg_words_per_sentence),
        "avg_chars_per_word": float(avg_chars_per_word),
        "long_word_ratio": float(long_words),
    }


def cognitive_load_bucket(metrics: dict[str, float]) -> str:
    """Very rough cognitive load bucket for demo/reporting."""
    awps = metrics["avg_words_per_sentence"]
    long_ratio = metrics["long_word_ratio"]
    if awps <= 12 and long_ratio <= 0.20:
        return "low"
    if awps <= 18 and long_ratio <= 0.30:
        return "medium"
    return "high"
