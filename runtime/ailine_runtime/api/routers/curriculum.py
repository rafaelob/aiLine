"""Curriculum standards API router.

Endpoints for searching curriculum objectives across BNCC, CCSS,
and NGSS systems, looking up individual standards by code, listing
available standard codes, and retrieving grade mappings.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, Response

from ...adapters.curriculum.unified_provider import UnifiedCurriculumProvider

router = APIRouter()


def _get_provider(request: Request) -> UnifiedCurriculumProvider:
    """Retrieve the UnifiedCurriculumProvider from app state.

    Falls back to creating a fresh instance when the container does not
    provide one — this keeps the router self-contained for testing.
    """
    provider = getattr(request.app.state, "curriculum_provider", None)
    if isinstance(provider, UnifiedCurriculumProvider):
        return provider
    # Lazy default — acceptable for pre-MVP; production should wire via DI
    new_provider = UnifiedCurriculumProvider()
    request.app.state.curriculum_provider = new_provider
    return new_provider


@router.get("/search")
async def curriculum_search(
    request: Request,
    response: Response,
    q: str = Query(..., min_length=1, description="Search query (code, keyword, or text)."),
    grade: str | None = Query(None, description="Grade filter (e.g. '6o ano', 'Grade 6')."),
    subject: str | None = Query(None, description="Subject filter (e.g. 'Matematica', 'Science')."),
    system: str | None = Query(None, description="System filter: bncc, ccss, ccss_ela, or ngss."),
    bloom_level: str | None = Query(
        None,
        description="Bloom's Taxonomy filter: remember, understand, apply, analyze, evaluate, or create.",
    ),
) -> list[dict[str, Any]]:
    """Search curriculum objectives across all supported systems.

    Returns a list of matching objectives as JSON objects.
    """
    response.headers["Cache-Control"] = "public, max-age=3600"
    provider = _get_provider(request)
    results = await provider.search(
        q, grade=grade, subject=subject, system=system, bloom_level=bloom_level,
    )
    return [obj.model_dump() for obj in results]


@router.get("/standards")
async def curriculum_list_standards(
    request: Request,
    response: Response,
    system: str | None = Query(None, description="System filter: bncc, ccss, or ngss."),
) -> list[str]:
    """List all available standard codes, optionally filtered by system."""
    response.headers["Cache-Control"] = "public, max-age=3600"
    provider = _get_provider(request)
    return await provider.list_standards(system=system)


@router.get("/standards/{code}")
async def curriculum_get_by_code(
    code: str,
    request: Request,
) -> dict[str, Any]:
    """Look up a single curriculum objective by its exact code."""
    provider = _get_provider(request)
    result = await provider.get_by_code(code)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Standard '{code}' not found.")
    return result.model_dump()


@router.get("/grade-mapping")
async def grade_mapping(request: Request) -> dict[str, Any]:
    """Return the Brazil <-> US grade equivalency mapping."""
    provider = _get_provider(request)
    return provider.get_grade_mapping()


@router.get("/grade-mapping/translate")
async def grade_translate(
    request: Request,
    grade: str = Query(..., description="Grade to translate (e.g. '6o ano' or 'Grade 6')."),
) -> dict[str, str | None]:
    """Translate a grade label between Brazilian and US systems."""
    provider = _get_provider(request)
    translated = provider.translate_grade(grade)
    return {"input": grade, "translated": translated}
