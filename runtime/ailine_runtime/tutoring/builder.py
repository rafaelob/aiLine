"""Tutor agent builder — creates and persists tutor specifications.

Uses the ChatLLM port for optional auto-persona generation
instead of DeepAgents directly (ADR-048).
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import structlog

from ..accessibility.profiles import ClassAccessibilityProfile, human_review_flags
from ..domain.entities.tutor import LearnerProfile, TutorAgentSpec, TutorMaterialsScope, TutorPersona
from .playbooks import build_tutor_system_prompt

logger = structlog.get_logger("ailine.tutoring.builder")

TutorStyle = Literal["socratic", "coach", "direct", "explainer"]

# -----------------------------
# Local persistence (MVP)
# -----------------------------


def _root_dir() -> Path:
    return Path(os.getenv("AILINE_LOCAL_STORE", ".local_store"))


def _tutors_dir() -> Path:
    d = _root_dir() / "tutors"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_tutor_spec(spec: TutorAgentSpec) -> dict[str, Any]:
    path = _tutors_dir() / f"{spec.tutor_id}.json"
    path.write_text(spec.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
    return {"tutor_id": spec.tutor_id, "stored_at": str(path)}


def load_tutor_spec(tutor_id: str) -> TutorAgentSpec | None:
    path = _tutors_dir() / f"{tutor_id}.json"
    if not path.exists():
        return None
    try:
        return TutorAgentSpec(**json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, ValueError, TypeError, OSError):
        logger.warning("load_tutor_spec_failed", tutor_id=tutor_id)
        return None


async def _generate_persona_with_llm(llm: Any, draft_prompt: str) -> TutorPersona:
    """Generate a tutor persona using the ChatLLM port."""
    messages = [
        {
            "role": "user",
            "content": (
                "Você cria prompts de tutor inclusivo para educação. "
                "Produza um system prompt curto, operacional e seguro. "
                "Não inclua dados sensíveis. Não diagnosticar. "
                "Incorpore UDL/COGA e adaptações (TEA/TDAH/aprendizagem/auditiva/visual).\n\n"
                'Responda com JSON: {"system_prompt": "...", "notes": ["..."]}\n\n'
                f"{draft_prompt}"
            ),
        }
    ]

    result = await llm.generate(messages, temperature=0.7, max_tokens=2048)

    # Parse JSON from response
    try:
        data = json.loads(result)
    except (json.JSONDecodeError, ValueError):
        logger.warning("persona_json_parse_failed", result_preview=result[:100])
        # Try to extract JSON from response
        if "{" in result and "}" in result:
            start = result.find("{")
            end = result.rfind("}")
            try:
                data = json.loads(result[start : end + 1])
            except (json.JSONDecodeError, ValueError):
                logger.warning("persona_json_extract_failed")
                data = {"system_prompt": result, "notes": []}
        else:
            data = {"system_prompt": result, "notes": []}

    return TutorPersona(
        system_prompt=data.get("system_prompt", result),
        response_contract="json",
        notes=data.get("notes", []),
    )


async def create_tutor_agent(
    *,
    cfg: Any,
    teacher_id: str,
    subject: str,
    grade: str,
    student_profile: dict[str, Any],
    class_accessibility_profile: dict[str, Any] | None = None,
    standard: str = "BNCC",
    style: TutorStyle = "socratic",
    tone: str = "calmo, paciente, encorajador",
    material_ids: list[str] | None = None,
    tags: list[str] | None = None,
    auto_persona: bool = False,
    llm: Any | None = None,
) -> TutorAgentSpec:
    """Create and persist a Tutor Agent configured by the teacher.

    Args:
        cfg: Settings or legacy AiLineConfig.
        teacher_id: Teacher who owns this tutor.
        subject: Subject area.
        grade: Grade level.
        student_profile: Functional learner profile dict (avoid PII).
        class_accessibility_profile: Optional class-level accessibility needs.
        standard: Curriculum standard (BNCC or US).
        style: Tutoring style.
        tone: Tutor tone description.
        material_ids: Optional material ID filter.
        tags: Optional tag filter.
        auto_persona: If True and LLM available, generate persona with AI.
        llm: Optional ChatLLM instance for persona generation.
    """
    from uuid_utils import uuid7

    tutor_id = str(uuid7())
    created_at = datetime.now(UTC).isoformat()

    learner = LearnerProfile(**student_profile)
    scope = TutorMaterialsScope(
        teacher_id=teacher_id,
        subject=subject,
        material_ids=material_ids or [],
        tags=tags or [],
    )

    # Human review flags (e.g., Libras/Braille)
    class_profile = ClassAccessibilityProfile(**class_accessibility_profile) if class_accessibility_profile else None
    human_req, reasons = human_review_flags(class_profile)

    # Persona generation
    if auto_persona and llm is not None:
        prompt = (
            f"Crie um system prompt para um Tutor de {subject}, série {grade}.\n"
            f"Estilo: {style}. Tom: {tone}.\n"
            f"Perfil do aluno: {learner.model_dump()}\n"
            f"Escopo de materiais: teacher_id={teacher_id}, subject={subject}\n"
        )
        persona = await _generate_persona_with_llm(llm, prompt)
    else:
        # Deterministic template (always works, no API key needed)
        dummy = TutorAgentSpec(
            tutor_id=tutor_id,
            created_at=created_at,
            teacher_id=teacher_id,
            subject=subject,
            grade=grade,
            standard=standard,
            style=style,
            tone=tone,
            student_profile=learner,
            materials_scope=scope,
            persona=TutorPersona(system_prompt="", response_contract="json", notes=[]),
            human_review_required=human_req,
            human_review_reasons=reasons,
        )
        persona = TutorPersona(
            system_prompt=build_tutor_system_prompt(dummy),
            response_contract="json",
            notes=[],
        )

    spec = TutorAgentSpec(
        tutor_id=tutor_id,
        created_at=created_at,
        teacher_id=teacher_id,
        subject=subject,
        grade=grade,
        standard=standard,
        style=style,  # type: ignore[arg-type]
        tone=tone,
        student_profile=learner,
        materials_scope=scope,
        persona=persona,
        human_review_required=human_req,
        human_review_reasons=reasons,
    )

    save_tutor_spec(spec)
    return spec
