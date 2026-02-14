"""Deterministic accessibility validation for lesson plan drafts.

Runs heuristic checks for structure, cognitive load, sensory needs,
and media requirements. Produces a scored report with pass/fail status.

Helper functions and keyword constants live in validator_helpers.py.
"""

from __future__ import annotations

from typing import Any

from .profiles import ClassAccessibilityProfile, human_review_flags
from .validator_helpers import (
    ALT_TEXT_KEYWORDS,
    AUDIO_DESC_KEYWORDS,
    BREAK_KEYWORDS,
    CAPTION_KEYWORDS,
    CHECKPOINT_KEYWORDS,
    EXAMPLE_KEYWORDS,
    GLOSSARY_KEYWORDS,
    MEDIA_MENTION_KEYWORDS,
    TRANSCRIPT_KEYWORDS,
    TRANSITION_KEYWORDS,
    cognitive_load_bucket,
    collect_text,
    contains_any,
    readability_metrics,
)


def validate_draft_accessibility(
    draft: dict[str, Any],
    class_profile: ClassAccessibilityProfile | None = None,
) -> dict[str, Any]:
    """Deterministic accessibility + structure validation.

    Returns a report with:
    - status: pass|fail
    - score: 0..100 (heuristic)
    - errors / warnings
    - checklist (booleans per minimum requirement)
    - category_scores (structured)
    - human_review_required + reasons
    - recommendations (next actions)
    """
    errors: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    steps = draft.get("steps") or []
    if not isinstance(steps, list) or not steps:
        errors.append("Plano sem steps (sequência didática vazia).")
        steps = []

    # ----- 1) instructions presentes e razoáveis
    checklist_instr = _check_instructions(steps, warnings)

    # ----- 2) transições e agenda (TEA)
    combined_text = collect_text(draft)
    has_transitions = contains_any(combined_text, TRANSITION_KEYWORDS)
    has_breaks = contains_any(combined_text, BREAK_KEYWORDS)
    has_checkpoints = contains_any(combined_text, CHECKPOINT_KEYWORDS)
    has_examples = contains_any(combined_text, EXAMPLE_KEYWORDS)
    has_glossary = contains_any(combined_text, GLOSSARY_KEYWORDS)

    has_accessibility_section = bool(
        draft.get("accessibility_pack_draft")
    ) or bool(draft.get("accessibility_notes"))

    # ----- 3) chunking por tempo (TDAH / aprendizagem)
    step_minutes = [
        step["minutes"]
        for step in steps
        if isinstance(step, dict) and isinstance(step.get("minutes"), int)
    ]
    total_minutes = sum(step_minutes) if step_minutes else 0
    max_step_minutes = max(step_minutes) if step_minutes else 0
    chunked_for_attention = _check_chunking(
        class_profile, max_step_minutes, warnings, recommendations,
    )

    # ----- 4) requisitos de mídia (auditiva/visual)
    media_check = _check_media_requirements(
        draft, combined_text, class_profile, warnings, recommendations,
    )

    # ----- 5) necessidades específicas (TEA/TDAH/learning)
    _check_specific_needs(
        class_profile, combined_text, draft,
        has_transitions, has_breaks, has_checkpoints,
        has_examples, has_glossary,
        warnings, recommendations,
    )

    # ----- 6) speech/language and motor (optional extras)
    _check_speech_motor(class_profile, combined_text, warnings, recommendations)

    # ----- 7) readability / cognitive load summary
    metrics = readability_metrics(combined_text)
    cog_bucket = cognitive_load_bucket(metrics)
    if (
        class_profile
        and (class_profile.needs.adhd or class_profile.needs.learning or class_profile.needs.autism)
        and cog_bucket == "high"
    ):
        warnings.append("Carga cognitiva estimada alta (frases longas / vocabulario denso).")
        recommendations.append("Simplificar linguagem, reduzir texto por etapa e usar listas curtas.")

    # ----- Checklist output
    checklist = {
        "has_steps": bool(steps),
        "has_instructions": checklist_instr["has_instructions"],
        "instructions_short": checklist_instr["instructions_short"],
        "instructions_single_actionish": checklist_instr["instructions_single_actionish"],
        "chunked_for_attention": chunked_for_attention,
        "has_checkpoints": has_checkpoints,
        "has_breaks": has_breaks,
        "has_transitions": has_transitions,
        "has_accessibility_section": has_accessibility_section,
        "has_media_requirements": media_check["has_media_requirements"],
        "captions_or_transcript": media_check["captions_or_transcript"],
        "alt_text": media_check["alt_text"],
    }

    # ----- Hard failures (MVP)
    if not checklist["has_steps"] or not checklist["has_instructions"]:
        errors.append("Falha crítica: plano precisa de steps com instructions.")

    # ----- Human review flags
    needs_human_review, human_reasons = human_review_flags(class_profile)

    # ----- Scoring (heuristic)
    score = _compute_score(
        checklist, cog_bucket, class_profile, media_check["mentions_media"],
    )

    pass_threshold = 70
    if errors:
        status = "fail"
    else:
        status = "pass"
        if score < pass_threshold:
            warnings.append(f"Score de acessibilidade abaixo do ideal ({score}/{pass_threshold}).")
            recommendations.append("Rever linguagem, chunking e requisitos de mídia para subir o score.")

    category_scores = {
        "structure": _score_structure(checklist),
        "cognitive": _score_cognitive(checklist, cog_bucket),
        "predictability": _score_predictability(checklist, has_accessibility_section),
        "media": _score_media(checklist, class_profile, media_check["mentions_media"]),
        "total": score,
        "cognitive_bucket": cog_bucket,
        "readability_metrics": metrics,
        "total_minutes": total_minutes,
        "max_step_minutes": max_step_minutes,
        "total_instruction_items": checklist_instr["total_instr_items"],
    }

    # Deduplicate recommendations in stable order
    seen: set[str] = set()
    recommendations_dedup: list[str] = []
    for r in recommendations:
        r_norm = r.strip()
        if r_norm and r_norm not in seen:
            seen.add(r_norm)
            recommendations_dedup.append(r_norm)

    return {
        "status": status,
        "score": score,
        "errors": errors,
        "warnings": warnings,
        "recommendations": recommendations_dedup,
        "checklist": checklist,
        "category_scores": category_scores,
        "human_review_required": needs_human_review,
        "human_review_reasons": human_reasons,
    }


# ---------------------------------------------------------------------------
# Internal check functions (extracted for readability)
# ---------------------------------------------------------------------------


def _check_instructions(
    steps: list[Any], warnings: list[str],
) -> dict[str, Any]:
    """Check instruction presence and quality across steps."""
    has_instructions = True
    instructions_short = True
    instructions_single_actionish = True
    max_instr_chars = 180
    max_instr_items = 8
    total_instr_items = 0

    for i, step in enumerate(steps):
        instr = step.get("instructions") if isinstance(step, dict) else None
        if not instr or not isinstance(instr, list):
            has_instructions = False
            warnings.append(f"Step {i+1} sem instructions em lista.")
            continue

        if len(instr) > max_instr_items:
            warnings.append(f"Step {i+1} tem muitas instruções ({len(instr)}). Considere chunking.")
            instructions_short = False

        for line in instr:
            if not isinstance(line, str):
                continue
            total_instr_items += 1
            if len(line) > max_instr_chars:
                instructions_short = False
                warnings.append(f"Instrução muito longa (> {max_instr_chars} chars) no step {i+1}.")
            if line.count(";") >= 1 or line.lower().count(" e ") >= 3:
                instructions_single_actionish = False

    return {
        "has_instructions": has_instructions,
        "instructions_short": instructions_short,
        "instructions_single_actionish": instructions_single_actionish,
        "total_instr_items": total_instr_items,
    }


def _check_chunking(
    class_profile: ClassAccessibilityProfile | None,
    max_step_minutes: int,
    warnings: list[str],
    recommendations: list[str],
) -> bool:
    """Check if steps are chunked for attention (TDAH / learning needs)."""
    focus_window = 10
    if class_profile:
        try:
            focus_window = int(class_profile.supports.adhd.focus_window_minutes)
        except (ValueError, TypeError, AttributeError):
            focus_window = 10

    if (
        class_profile
        and (class_profile.needs.adhd or class_profile.needs.learning)
        and max_step_minutes > (focus_window + 4)
    ):
        warnings.append(
            f"Chunking: step com {max_step_minutes} min "
            f"(acima da janela de foco ~{focus_window} min). "
            "Considere quebrar etapas longas."
        )
        recommendations.append(
            "Quebrar etapas longas em blocos de 5-10 min com checkpoints."
        )
        return False
    return True


def _check_media_requirements(
    draft: dict[str, Any],
    combined_text: str,
    class_profile: ClassAccessibilityProfile | None,
    warnings: list[str],
    recommendations: list[str],
) -> dict[str, Any]:
    """Check media accessibility requirements (captions, alt text, etc.)."""
    needs_media_req = bool(
        class_profile and (class_profile.needs.hearing or class_profile.needs.visual)
    )
    media_req = None
    ap = draft.get("accessibility_pack_draft")
    if isinstance(ap, dict):
        media_req = ap.get("media_requirements")
    if not media_req:
        media_req = draft.get("media_requirements")

    media_req_text = (
        " ".join(media_req) if isinstance(media_req, list) else str(media_req or "")
    )
    media_lower = media_req_text.lower()

    mentions_media = contains_any(combined_text, MEDIA_MENTION_KEYWORDS)
    captions_present = (
        contains_any(media_lower, CAPTION_KEYWORDS)
        or contains_any(combined_text, CAPTION_KEYWORDS)
    )
    transcript_present = (
        contains_any(media_lower, TRANSCRIPT_KEYWORDS)
        or contains_any(combined_text, TRANSCRIPT_KEYWORDS)
    )
    alt_text_present = (
        contains_any(media_lower, ALT_TEXT_KEYWORDS)
        or contains_any(combined_text, ALT_TEXT_KEYWORDS)
    )
    audio_desc_present = (
        contains_any(media_lower, AUDIO_DESC_KEYWORDS)
        or contains_any(combined_text, AUDIO_DESC_KEYWORDS)
    )

    has_media_requirements = bool(media_req_text.strip())
    if needs_media_req and not has_media_requirements:
        warnings.append(
            "Perfil inclui deficiência auditiva/visual mas plano não explicita requisitos de mídia "
            "(legenda/transcrição/descrição/alt text)."
        )
        recommendations.append("Adicionar seção 'requisitos de mídia' (legenda/transcrição/alt text).")

    if class_profile and class_profile.needs.hearing and not (captions_present or transcript_present):
        warnings.append("Auditiva: faltou explicitar legenda/transcrição para conteúdos com áudio.")
        recommendations.append("Garantir: vídeo → legendas; áudio → transcrição; instruções críticas em texto.")

    if class_profile and class_profile.needs.visual:
        if not alt_text_present:
            warnings.append("Visual: faltou exigir texto alternativo (alt text) para imagens/figuras.")
            recommendations.append(
                "Garantir: imagens/figuras -> texto alternativo; "
                "exports compativeis com leitor de tela."
            )
        require_ad = getattr(
            class_profile.supports.visual, "require_audio_description", False
        )
        if require_ad and not audio_desc_present:
            warnings.append("Visual: perfil exige audiodescrição mas não foi mencionada.")
            recommendations.append(
                "Adicionar audiodescricao (ou sinalizar revisao humana) "
                "para midia visual relevante."
            )

    return {
        "has_media_requirements": has_media_requirements,
        "captions_or_transcript": bool(captions_present or transcript_present),
        "alt_text": bool(alt_text_present),
        "mentions_media": mentions_media,
    }


def _check_specific_needs(
    class_profile: ClassAccessibilityProfile | None,
    combined_text: str,
    draft: dict[str, Any],
    has_transitions: bool,
    has_breaks: bool,
    has_checkpoints: bool,
    has_examples: bool,
    has_glossary: bool,
    warnings: list[str],
    recommendations: list[str],
) -> None:
    """Check TEA/TDAH/learning-specific needs."""
    if class_profile and class_profile.needs.autism:
        if not has_transitions:
            warnings.append("TEA: plano não explicita transições (ex.: 'agora / em seguida / depois').")
            recommendations.append("Adicionar scripts de transição curtos a cada mudança de atividade.")
        if not has_breaks:
            warnings.append("TEA: plano não tem pausas/regulação explícitas.")
            recommendations.append("Inserir pausas curtas de regulação (respiração, água, canto calmo).")
        if not contains_any(combined_text, ("agenda", "cronograma", "rotina", "hoje vamos")):
            warnings.append("TEA: faltou uma agenda/roteiro explícito no início da aula.")
            recommendations.append("Adicionar uma agenda (o que vai acontecer e quando) e um cronograma visual.")

    if class_profile and class_profile.needs.adhd:
        if not has_checkpoints:
            warnings.append("TDAH: faltou checkpoints curtos de 'feito' / checagem de progresso.")
            recommendations.append("Adicionar checkpoints (ex.: 'marque ✓ quando terminar') e micro-met as por etapa.")
        if not has_breaks:
            warnings.append("TDAH: faltou pausa/movimento explícito.")
            recommendations.append(
                "Inserir pausas de movimento e reset de atencao a cada ~10-15 min."
            )

    if class_profile and class_profile.needs.learning:
        if not has_examples:
            warnings.append("Aprendizagem: faltou exemplo/modelo antes de pedir execução.")
            recommendations.append("Adicionar exemplo curto (modelo) antes da atividade principal.")
        if not has_glossary:
            warnings.append("Aprendizagem: faltou glossário/vocabulário de termos difíceis.")
            recommendations.append(
                "Gerar um mini-glossario (3-8 termos) com definicao simples."
            )
        has_student_plan = isinstance(draft.get("student_plan"), dict) or bool(
            draft.get("student_friendly_summary")
        )
        if not has_student_plan:
            warnings.append("Aprendizagem: faltou versão aluno (linguagem simples + passos curtos).")
            recommendations.append("Gerar versão aluno com frases curtas e instruções 1-ação-por-item.")


def _check_speech_motor(
    class_profile: ClassAccessibilityProfile | None,
    combined_text: str,
    warnings: list[str],
    recommendations: list[str],
) -> None:
    """Check speech/language and motor accessibility needs."""
    aac_kw = ("pictograma", "aac", "comunicacao alternativa", "cartao", "prancha")
    if (
        class_profile
        and class_profile.needs.speech_language
        and not contains_any(combined_text, aac_kw)
    ):
        warnings.append(
            "Fala/linguagem: considerar suporte AAC/pictogramas "
            "e opcoes de resposta alternativa."
        )
        recommendations.append(
            "Oferecer opcoes de resposta: "
            "apontar/selecionar/imagem/oral (conforme contexto)."
        )

    motor_kw = ("ditado", "oral", "alternativa", "teclado", "assistivo")
    if (
        class_profile
        and class_profile.needs.motor
        and not contains_any(combined_text, motor_kw)
    ):
        warnings.append(
            "Motora: considerar alternativas a escrita manual "
            "(oral/teclado/selecao)."
        )
        recommendations.append(
            "Oferecer alternativas de entrega "
            "(oral/teclado/multipla escolha) para reduzir barreira motora."
        )


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------


def _score_structure(checklist: dict[str, Any]) -> int:
    score = 0
    score += 12 if checklist["has_steps"] else 0
    score += 12 if checklist["has_instructions"] else 0
    score += 6 if checklist["instructions_short"] else 0
    return score


def _score_cognitive(checklist: dict[str, Any], cog_bucket: str) -> int:
    score = 0
    score += 10 if checklist["chunked_for_attention"] else 0
    score += 8 if checklist["has_checkpoints"] else 0
    score += 7 if cog_bucket in ("low", "medium") else 2
    return score


def _score_predictability(checklist: dict[str, Any], has_accessibility_section: bool) -> int:
    score = 0
    score += 10 if checklist["has_transitions"] else 0
    score += 8 if checklist["has_breaks"] else 0
    score += 7 if has_accessibility_section else 0
    return score


def _score_media(
    checklist: dict[str, Any],
    class_profile: ClassAccessibilityProfile | None,
    mentions_media: bool,
) -> int:
    if class_profile and (class_profile.needs.hearing or class_profile.needs.visual):
        score = 0
        score += 8 if checklist["has_media_requirements"] else 0
        score += 6 if checklist["captions_or_transcript"] else 0
        score += 6 if checklist["alt_text"] else 0
        return score
    return 16 if mentions_media else 18


def _compute_score(
    checklist: dict[str, Any],
    cog_bucket: str,
    class_profile: ClassAccessibilityProfile | None,
    mentions_media: bool,
) -> int:
    has_accessibility_section = checklist.get("has_accessibility_section", False)
    structure = _score_structure(checklist)
    cognitive = _score_cognitive(checklist, cog_bucket)
    predict = _score_predictability(checklist, has_accessibility_section)
    media = _score_media(checklist, class_profile, mentions_media)
    return max(0, min(100, structure + cognitive + predict + media))
