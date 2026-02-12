from __future__ import annotations

import re
from typing import Any

from .profiles import ClassAccessibilityProfile, human_review_flags

# ----------------------------
# Helpers (cheap heuristics)
# ----------------------------

_BREAK_KEYWORDS = (
    "pausa", "intervalo", "break", "movimento",
    "alongamento", "respiração", "relax", "hidrata",
)
_TRANSITION_KEYWORDS = (
    "agora", "em seguida", "próximo", "depois",
    "transição", "mudança", "vamos", "a seguir",
)
_CHECKPOINT_KEYWORDS = (
    "checkpoint", "verifique", "confira", "checagem", "feito", "ok",
    "\u2713", "autoavalia", "responda 1",
)
_EXAMPLE_KEYWORDS = ("exemplo", "modelo", "mostre", "demonstre", "veja", "como fazer")
_GLOSSARY_KEYWORDS = ("glossário", "vocabulário", "termos", "palavras-chave")
_ALT_TEXT_KEYWORDS = ("texto alternativo", "alt text", "descrição da imagem", "descrever a imagem")
_CAPTION_KEYWORDS = ("legenda", "legendado", "captions")
_TRANSCRIPT_KEYWORDS = ("transcrição", "transcript")
_AUDIO_DESC_KEYWORDS = ("audiodescrição", "audio description", "descrição do vídeo")

_MEDIA_MENTION_KEYWORDS = (
    "vídeo", "video", "áudio", "audio", "podcast",
    "gravação", "imagem", "figura", "slide", "foto", "ilustração",
)


def _collect_text(draft: dict[str, Any]) -> str:
    # Extract a representative corpus to score readability/cognitive load.
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


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    t = text.lower()
    return any(k in t for k in keywords)


def _readability_metrics(text: str) -> dict[str, float]:
    # Lightweight (language-agnostic) heuristics. Not a medical/educational diagnosis tool.
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


def _cognitive_load_bucket(metrics: dict[str, float]) -> str:
    # very rough bucket for demo/reporting.
    awps = metrics["avg_words_per_sentence"]
    long_ratio = metrics["long_word_ratio"]
    if awps <= 12 and long_ratio <= 0.20:
        return "low"
    if awps <= 18 and long_ratio <= 0.30:
        return "medium"
    return "high"


# ----------------------------
# Validator (Quality Gate)
# ----------------------------

def validate_draft_accessibility(
    draft: dict[str, Any],
    class_profile: ClassAccessibilityProfile | None = None,
) -> dict[str, Any]:
    """Validação determinística focada em acessibilidade e estrutura.

    Retorna um relatório com:
    - status: pass|fail
    - score: 0..100 (heurística)
    - errors / warnings
    - checklist (booleans por requisito mínimo)
    - category_scores (estruturado)
    - human_review_required + razões
    - recommendations (próximas ações)
    """
    errors: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    steps = draft.get("steps") or []
    if not isinstance(steps, list) or not steps:
        errors.append("Plano sem steps (sequência didática vazia).")
        steps = []

    # ----- 1) instructions presentes e razoáveis
    has_instructions = True
    instructions_short = True
    instructions_single_actionish = True  # heuristic: penalize very long lines or multiple clauses
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
            # crude heuristic: multiple clauses
            if line.count(";") >= 1 or line.lower().count(" e ") >= 3:
                instructions_single_actionish = False

    # ----- 2) transições e agenda (TEA)
    combined_text = _collect_text(draft)
    has_transitions = _contains_any(combined_text, _TRANSITION_KEYWORDS)
    has_breaks = _contains_any(combined_text, _BREAK_KEYWORDS)
    has_checkpoints = _contains_any(combined_text, _CHECKPOINT_KEYWORDS)
    has_examples = _contains_any(combined_text, _EXAMPLE_KEYWORDS)
    has_glossary = _contains_any(combined_text, _GLOSSARY_KEYWORDS)

    has_accessibility_section = bool(draft.get("accessibility_pack_draft")) or bool(draft.get("accessibility_notes"))

    # ----- 3) chunking por tempo (TDAH / aprendizagem)
    step_minutes = []
    for step in steps:
        if isinstance(step, dict) and isinstance(step.get("minutes"), int):
            step_minutes.append(step["minutes"])
    total_minutes = sum(step_minutes) if step_minutes else 0
    max_step_minutes = max(step_minutes) if step_minutes else 0

    focus_window = 10
    if class_profile:
        # prefer support settings when present
        try:
            focus_window = int(class_profile.supports.adhd.focus_window_minutes)
        except Exception:
            focus_window = 10

    chunked_for_attention = True
    if (  # Heuristic: major steps should be <= focus window (or close)
        class_profile
        and (class_profile.needs.adhd or class_profile.needs.learning)
        and max_step_minutes > (focus_window + 4)
    ):
        chunked_for_attention = False
        warnings.append(
            f"Chunking: step com {max_step_minutes} min "
            f"(acima da janela de foco ~{focus_window} min). "
            "Considere quebrar etapas longas."
        )
        recommendations.append(
            "Quebrar etapas longas em blocos de 5-10 min com checkpoints."
        )

    # ----- 4) requisitos de mídia (auditiva/visual)
    needs_media_req = bool(class_profile and (class_profile.needs.hearing or class_profile.needs.visual))
    media_req = None
    ap = draft.get("accessibility_pack_draft")
    if isinstance(ap, dict):
        media_req = ap.get("media_requirements")
    if not media_req:
        media_req = draft.get("media_requirements")

    media_req_text = (
        " ".join(media_req) if isinstance(media_req, list) else str(media_req or "")
    )
    _media_lower = media_req_text.lower()

    mentions_media = _contains_any(combined_text, _MEDIA_MENTION_KEYWORDS)
    captions_present = (
        _contains_any(_media_lower, _CAPTION_KEYWORDS)
        or _contains_any(combined_text, _CAPTION_KEYWORDS)
    )
    transcript_present = (
        _contains_any(_media_lower, _TRANSCRIPT_KEYWORDS)
        or _contains_any(combined_text, _TRANSCRIPT_KEYWORDS)
    )
    alt_text_present = (
        _contains_any(_media_lower, _ALT_TEXT_KEYWORDS)
        or _contains_any(combined_text, _ALT_TEXT_KEYWORDS)
    )
    audio_desc_present = (
        _contains_any(_media_lower, _AUDIO_DESC_KEYWORDS)
        or _contains_any(combined_text, _AUDIO_DESC_KEYWORDS)
    )

    has_media_requirements = bool(media_req_text.strip())
    if needs_media_req and not has_media_requirements:
        warnings.append(
            "Perfil inclui deficiência auditiva/visual mas plano não explicita requisitos de mídia "
            "(legenda/transcrição/descrição/alt text)."
        )
        recommendations.append("Adicionar seção 'requisitos de mídia' (legenda/transcrição/alt text).")

    # hearing specifics
    if class_profile and class_profile.needs.hearing and not (captions_present or transcript_present):
        warnings.append("Auditiva: faltou explicitar legenda/transcrição para conteúdos com áudio.")
        recommendations.append("Garantir: vídeo → legendas; áudio → transcrição; instruções críticas em texto.")
    # visual specifics
    if class_profile and class_profile.needs.visual:
        if not alt_text_present:
            warnings.append("Visual: faltou exigir texto alternativo (alt text) para imagens/figuras.")
            recommendations.append(
                "Garantir: imagens/figuras -> texto alternativo; "
                "exports compativeis com leitor de tela."
            )
        # audio description is optional; only warn if explicitly required
        require_ad = getattr(
            class_profile.supports.visual, "require_audio_description", False
        )
        if require_ad and not audio_desc_present:
            warnings.append("Visual: perfil exige audiodescrição mas não foi mencionada.")
            recommendations.append(
                "Adicionar audiodescricao (ou sinalizar revisao humana) "
                "para midia visual relevante."
            )

    # ----- 5) necessidades específicas (TEA/TDAH/learning)
    if class_profile and class_profile.needs.autism:
        if not has_transitions:
            warnings.append("TEA: plano não explicita transições (ex.: 'agora / em seguida / depois').")
            recommendations.append("Adicionar scripts de transição curtos a cada mudança de atividade.")
        if not has_breaks:
            warnings.append("TEA: plano não tem pausas/regulação explícitas.")
            recommendations.append("Inserir pausas curtas de regulação (respiração, água, canto calmo).")
        # visual schedule expectation
        if not _contains_any(combined_text, ("agenda", "cronograma", "rotina", "hoje vamos")):
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
        # student plan presence
        has_student_plan = isinstance(draft.get("student_plan"), dict) or bool(draft.get("student_friendly_summary"))
        if not has_student_plan:
            warnings.append("Aprendizagem: faltou versão aluno (linguagem simples + passos curtos).")
            recommendations.append("Gerar versão aluno com frases curtas e instruções 1-ação-por-item.")

    # ----- 6) speech/language and motor (optional extras)
    _aac_kw = ("pictograma", "aac", "comunicacao alternativa", "cartao", "prancha")
    if (
        class_profile
        and class_profile.needs.speech_language
        and not _contains_any(combined_text, _aac_kw)
    ):
        warnings.append(
            "Fala/linguagem: considerar suporte AAC/pictogramas "
            "e opcoes de resposta alternativa."
        )
        recommendations.append(
            "Oferecer opcoes de resposta: "
            "apontar/selecionar/imagem/oral (conforme contexto)."
        )

    _motor_kw = ("ditado", "oral", "alternativa", "teclado", "assistivo")
    if (
        class_profile
        and class_profile.needs.motor
        and not _contains_any(combined_text, _motor_kw)
    ):
        warnings.append(
            "Motora: considerar alternativas a escrita manual "
            "(oral/teclado/selecao)."
        )
        recommendations.append(
            "Oferecer alternativas de entrega "
            "(oral/teclado/multipla escolha) para reduzir barreira motora."
        )

    # ----- 7) readability / cognitive load summary
    metrics = _readability_metrics(combined_text)
    cognitive_bucket = _cognitive_load_bucket(metrics)
    if (
        class_profile
        and (class_profile.needs.adhd or class_profile.needs.learning or class_profile.needs.autism)
        and cognitive_bucket == "high"
    ):
        warnings.append("Carga cognitiva estimada alta (frases longas / vocabulario denso).")
        recommendations.append("Simplificar linguagem, reduzir texto por etapa e usar listas curtas.")

    # ----- Checklist output
    checklist = {
        "has_steps": bool(steps),
        "has_instructions": has_instructions,
        "instructions_short": instructions_short,
        "instructions_single_actionish": instructions_single_actionish,
        "chunked_for_attention": chunked_for_attention,
        "has_checkpoints": has_checkpoints,
        "has_breaks": has_breaks,
        "has_transitions": has_transitions,
        "has_accessibility_section": has_accessibility_section,
        "has_media_requirements": has_media_requirements,
        "captions_or_transcript": bool(captions_present or transcript_present),
        "alt_text": bool(alt_text_present),
    }

    # ----- Hard failures (MVP)
    if not checklist["has_steps"] or not checklist["has_instructions"]:
        errors.append("Falha crítica: plano precisa de steps com instructions.")

    # ----- Human review flags
    needs_human_review, human_reasons = human_review_flags(class_profile)

    # ----- Scoring (heuristic)
    # Structure (0-30)
    structure = 0
    structure += 12 if checklist["has_steps"] else 0
    structure += 12 if checklist["has_instructions"] else 0
    structure += 6 if checklist["instructions_short"] else 0

    # Cognitive (0-25)
    cognitive = 0
    cognitive += 10 if checklist["chunked_for_attention"] else 0
    cognitive += 8 if checklist["has_checkpoints"] else 0
    cognitive += 7 if cognitive_bucket in ("low", "medium") else 2

    # Predictability/sensory (0-25)
    predict = 0
    predict += 10 if checklist["has_transitions"] else 0
    predict += 8 if checklist["has_breaks"] else 0
    predict += 7 if has_accessibility_section else 0

    # Media (0-20)
    media = 0
    if class_profile and (class_profile.needs.hearing or class_profile.needs.visual):
        media += 8 if checklist["has_media_requirements"] else 0
        media += 6 if checklist["captions_or_transcript"] else 0
        media += 6 if checklist["alt_text"] else 0
    else:
        # If not needed, neutral score
        media = 16 if mentions_media else 18

    score = max(0, min(100, structure + cognitive + predict + media))

    # Recommend threshold for pass in demo (soft)
    pass_threshold = 70
    if errors:
        status = "fail"
    else:
        status = "pass"  # keep pass but expose warnings/score
        if score < pass_threshold:
            warnings.append(f"Score de acessibilidade abaixo do ideal ({score}/{pass_threshold}).")
            recommendations.append("Rever linguagem, chunking e requisitos de mídia para subir o score.")

    category_scores = {
        "structure": structure,
        "cognitive": cognitive,
        "predictability": predict,
        "media": media,
        "total": score,
        "cognitive_bucket": cognitive_bucket,
        "readability_metrics": metrics,
        "total_minutes": total_minutes,
        "max_step_minutes": max_step_minutes,
        "total_instruction_items": total_instr_items,
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
