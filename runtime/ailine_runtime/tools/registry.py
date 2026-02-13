from __future__ import annotations

import json
import os
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NewType

from pydantic import BaseModel, Field

from ..accessibility.exports import render_export
from ..accessibility.profiles import ClassAccessibilityProfile
from ..accessibility.validator import validate_draft_accessibility
from ..materials.store import search_materials

# ----------------------------
# Tenant-scoped identity
# ----------------------------

TeacherId = NewType("TeacherId", str)

# ----------------------------
# Canonical Tool Definitions
# ----------------------------

ArgsModelT = type[BaseModel]
ToolHandler = Callable[..., Awaitable[Any]]


@dataclass(frozen=True)
class ToolDef:
    name: str
    description: str
    args_model: ArgsModelT
    handler: ToolHandler


# ----------------------------
# Domain tools (MVP stubs / local)
# ----------------------------

class RagSearchArgs(BaseModel):
    query: str = Field(..., description="Texto de busca (pergunta ou trecho).")
    k: int = Field(5, ge=1, le=20, description="Quantidade de trechos a retornar.")
    grade: str | None = Field(None, description="Filtro opcional (série/ano).")
    subject: str | None = Field(None, description="Filtro opcional (disciplina).")

    # Para tutoria e materiais do professor
    teacher_id: str | None = Field(None, description="Opcional: filtra materiais de um professor específico.")
    material_ids: list[str] = Field(default_factory=list, description="Opcional: filtra por material_id.")
    tags: list[str] = Field(default_factory=list, description="Opcional: filtra por tags.")


class CurriculumLookupArgs(BaseModel):
    standard: str = Field(..., description="BNCC|US")
    grade: str = Field(..., description="Série/ano")
    topic: str = Field(..., description="Tema/tópico")
    teacher_id: str | None = Field(None, description="Opcional: teacher_id para escopo de tenant.")


class AccessibilityChecklistArgs(BaseModel):
    draft_plan: dict[str, Any] = Field(..., description="Plano draft (JSON).")
    class_profile: dict[str, Any] | None = Field(None, description="ClassAccessibilityProfile (dict).")


class ExportVariantArgs(BaseModel):
    plan_json: dict[str, Any] = Field(..., description="Plano final (JSON).")

    variant: str = Field(
        ...,
        description=(
            "standard_html|low_distraction_html|large_print_html|high_contrast_html|"
            "dyslexia_friendly_html|screen_reader_html|visual_schedule_html|"
            "visual_schedule_json|student_plain_text|audio_script"
        ),
    )
    teacher_id: str | None = Field(None, description="Opcional: teacher_id para escopo de tenant.")


class SavePlanArgs(BaseModel):
    plan_json: dict[str, Any] = Field(
        ...,
        description="Plano final (JSON), incluindo accessibility_pack, relatorio e exports.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadados (run_id, versão, etc).")
    teacher_id: str | None = Field(None, description="Opcional: teacher_id para escopo de tenant.")


# ----------------------------
# Handlers
# ----------------------------

async def rag_search_handler(args: RagSearchArgs) -> dict[str, Any]:
    # Segurança (MVP):
    # - Em um produto real, rag_search precisa ser autorizado por tenant (teacher_id/escola).
    # - Aqui exigimos teacher_id para evitar "vazar" materiais de outro professor.
    if not args.teacher_id:
        return {"chunks": [], "note": "teacher_id_required_for_rag_search"}

    chunks = search_materials(
        query=args.query,
        k=args.k,
        teacher_id=args.teacher_id,
        subject=args.subject,
        material_ids=args.material_ids or None,
        tags=args.tags or None,
    )
    return {"chunks": chunks, "note": "local_material_search (troque por pgvector em produção)"}


async def curriculum_lookup_handler(args: CurriculumLookupArgs) -> dict[str, Any]:
    """Look up real curriculum objectives via UnifiedCurriculumProvider."""
    from ..adapters.curriculum.unified_provider import UnifiedCurriculumProvider

    provider = UnifiedCurriculumProvider()
    system_filter = args.standard.lower() if args.standard else None

    objectives = await provider.search(
        args.topic,
        grade=args.grade,
        system=system_filter,
    )

    return {
        "standard": args.standard,
        "grade": args.grade,
        "topic": args.topic,
        "teacher_id": args.teacher_id,
        "objectives": [
            {
                "code": obj.code,
                "system": obj.system.value if hasattr(obj.system, "value") else str(obj.system),
                "subject": obj.subject,
                "grade": obj.grade,
                "domain": obj.domain,
                "description": obj.description,
                "keywords": obj.keywords,
                "bloom_level": obj.bloom_level,
            }
            for obj in objectives[:10]
        ],
    }


async def accessibility_checklist_handler(args: AccessibilityChecklistArgs) -> dict[str, Any]:
    class_profile = ClassAccessibilityProfile(**args.class_profile) if args.class_profile else None
    report = validate_draft_accessibility(args.draft_plan, class_profile)
    return report


async def export_variant_handler(args: ExportVariantArgs) -> dict[str, Any]:
    # Tenant filtering: teacher_id scopes which plan data is accessible.
    # The plan_json itself should come from a tenant-scoped source;
    # teacher_id is tracked here for audit and future DB-backed storage.
    variant = args.variant
    content = render_export(args.plan_json, variant=variant)
    return {"variant": variant, "content": content, "teacher_id": args.teacher_id}


async def save_plan_handler(args: SavePlanArgs) -> dict[str, Any]:
    # MVP: persistência local (arquivo) para demo; troque por Postgres.
    # Tenant filtering: teacher_id is included in the stored metadata
    # and in the file path namespace to prevent cross-tenant access.
    from uuid_utils import uuid7

    teacher_id = args.teacher_id or "anonymous"
    # Validate teacher_id format to prevent path traversal (S-5)
    if teacher_id != "anonymous" and not re.match(r"^[0-9a-f\-]{36}$", teacher_id):
        return {"error": "Invalid teacher_id format (expected UUID)"}
    plan_id = str(uuid7())
    out_dir = Path(os.getenv("AILINE_LOCAL_STORE", ".local_store")) / teacher_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{plan_id}.json"
    stored_metadata = {**args.metadata, "teacher_id": teacher_id}
    out_path.write_text(
        json.dumps({"plan": args.plan_json, "metadata": stored_metadata}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"plan_id": plan_id, "stored_at": str(out_path), "teacher_id": teacher_id}


def build_tool_registry() -> list[ToolDef]:
    return [
        ToolDef(
            name="rag_search",
            description="Busca trechos relevantes nos materiais do professor (RAG).",
            args_model=RagSearchArgs,
            handler=rag_search_handler,
        ),
        ToolDef(
            name="curriculum_lookup",
            description="Consulta objetivos curriculares (BNCC/US) por série e tópico.",
            args_model=CurriculumLookupArgs,
            handler=curriculum_lookup_handler,
        ),
        ToolDef(
            name="accessibility_checklist",
            description=(
                "Gera um relatório determinístico de acessibilidade (score, checklist, warnings, recomendações) "
                "e marca quando revisão humana é necessária."
            ),
            args_model=AccessibilityChecklistArgs,
            handler=accessibility_checklist_handler,
        ),
        ToolDef(
            name="export_variant",
            description=(
                "Gera uma variante exportavel do plano "
                "(HTML: baixa distracao, large print, alto contraste, "
                "dislexia-friendly, screen reader; visual schedule; "
                "student plain text; audio script)."
            ),
            args_model=ExportVariantArgs,
            handler=export_variant_handler,
        ),
        ToolDef(
            name="save_plan",
            description="Persiste o plano final e retorna identificadores.",
            args_model=SavePlanArgs,
            handler=save_plan_handler,
        ),
    ]
