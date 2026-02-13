"""Extended tests for tools/registry.py -- covers handlers and build_tool_registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from ailine_runtime.tools.registry import (
    AccessibilityChecklistArgs,
    CurriculumLookupArgs,
    ExportVariantArgs,
    RagSearchArgs,
    SavePlanArgs,
    accessibility_checklist_handler,
    build_tool_registry,
    curriculum_lookup_handler,
    export_variant_handler,
    rag_search_handler,
    save_plan_handler,
)


class TestRagSearchHandler:
    @pytest.mark.asyncio
    async def test_no_teacher_id(self):
        args = RagSearchArgs(query="fractions")
        result = await rag_search_handler(args)
        assert result["chunks"] == []
        assert "teacher_id_required" in result["note"]

    @pytest.mark.asyncio
    async def test_with_teacher_id(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(tmp_path))
        # Add a material first
        from ailine_runtime.materials.store import add_material

        add_material(
            teacher_id="t1",
            subject="Math",
            title="Fractions",
            content="Teaching fractions with visual aids and manipulatives.",
        )
        args = RagSearchArgs(query="fractions visual", teacher_id="t1")
        result = await rag_search_handler(args)
        assert len(result["chunks"]) >= 1

    @pytest.mark.asyncio
    async def test_with_empty_filters(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(tmp_path))
        args = RagSearchArgs(
            query="test", teacher_id="t1", material_ids=[], tags=[]
        )
        result = await rag_search_handler(args)
        assert "chunks" in result


class TestCurriculumLookupHandler:
    @pytest.mark.asyncio
    async def test_returns_real_objectives(self):
        args = CurriculumLookupArgs(standard="BNCC", grade="4", topic="fractions")
        result = await curriculum_lookup_handler(args)
        assert result["standard"] == "BNCC"
        assert result["grade"] == "4"
        assert result["topic"] == "fractions"
        assert "objectives" in result


class TestAccessibilityChecklistHandler:
    @pytest.mark.asyncio
    async def test_without_profile(self):
        args = AccessibilityChecklistArgs(
            draft_plan={"activities": [{"text": "Read the chapter"}]},
            class_profile=None,
        )
        result = await accessibility_checklist_handler(args)
        assert "score" in result

    @pytest.mark.asyncio
    async def test_with_profile(self):
        args = AccessibilityChecklistArgs(
            draft_plan={"activities": [{"text": "Read the chapter"}]},
            class_profile={"has_low_vision": True},
        )
        result = await accessibility_checklist_handler(args)
        assert "score" in result


class TestExportVariantHandler:
    @pytest.mark.asyncio
    async def test_standard_html(self):
        args = ExportVariantArgs(
            plan_json={"title": "My Plan", "activities": [{"text": "Step 1"}]},
            variant="standard_html",
        )
        result = await export_variant_handler(args)
        assert result["variant"] == "standard_html"
        assert "content" in result


class TestSavePlanHandler:
    @pytest.mark.asyncio
    async def test_save_plan(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(tmp_path))
        args = SavePlanArgs(
            plan_json={"title": "Test Plan"},
            metadata={"run_id": "run-123"},
        )
        result = await save_plan_handler(args)
        assert "plan_id" in result
        assert "stored_at" in result
        # Verify file was created
        stored_path = Path(result["stored_at"])
        assert stored_path.exists()


class TestBuildToolRegistry:
    def test_returns_all_tools(self):
        registry = build_tool_registry()
        assert len(registry) == 5
        names = {t.name for t in registry}
        assert names == {
            "rag_search",
            "curriculum_lookup",
            "accessibility_checklist",
            "export_variant",
            "save_plan",
        }


# ---------------------------------------------------------------------------
# Tenant filtering enforcement tests (FINDING-04)
# ---------------------------------------------------------------------------


class TestTenantFilteringRagSearch:
    """rag_search enforces teacher_id at the code level."""

    @pytest.mark.asyncio
    async def test_rag_rejects_without_teacher_id(self):
        args = RagSearchArgs(query="test")
        result = await rag_search_handler(args)
        assert result["chunks"] == []
        assert "teacher_id_required" in result["note"]

    @pytest.mark.asyncio
    async def test_rag_accepts_teacher_id(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(tmp_path))
        from ailine_runtime.materials.store import add_material

        add_material(teacher_id="t-abc", subject="Math", title="X", content="fractions")
        args = RagSearchArgs(query="fractions", teacher_id="t-abc")
        result = await rag_search_handler(args)
        assert isinstance(result["chunks"], list)


class TestTenantFilteringCurriculumLookup:
    """curriculum_lookup includes teacher_id in response."""

    @pytest.mark.asyncio
    async def test_includes_teacher_id_in_response(self):
        args = CurriculumLookupArgs(standard="BNCC", grade="4", topic="fracs", teacher_id="t-123")
        result = await curriculum_lookup_handler(args)
        assert result["teacher_id"] == "t-123"

    @pytest.mark.asyncio
    async def test_teacher_id_none_when_omitted(self):
        args = CurriculumLookupArgs(standard="BNCC", grade="4", topic="fracs")
        result = await curriculum_lookup_handler(args)
        assert result["teacher_id"] is None


class TestTenantFilteringExportVariant:
    """export_variant includes teacher_id in response."""

    @pytest.mark.asyncio
    async def test_includes_teacher_id_in_response(self):
        args = ExportVariantArgs(
            plan_json={"title": "Test"},
            variant="standard_html",
            teacher_id="t-456",
        )
        result = await export_variant_handler(args)
        assert result["teacher_id"] == "t-456"


class TestTenantFilteringSavePlan:
    """save_plan namespaces by teacher_id."""

    @pytest.mark.asyncio
    async def test_saves_under_teacher_directory(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(tmp_path))
        teacher_uuid = "00000000-0000-0000-0000-000000000789"
        args = SavePlanArgs(
            plan_json={"title": "Plan"},
            metadata={"run_id": "r1"},
            teacher_id=teacher_uuid,
        )
        result = await save_plan_handler(args)
        assert result["teacher_id"] == teacher_uuid
        stored_path = Path(result["stored_at"])
        assert stored_path.exists()
        assert teacher_uuid in str(stored_path)

    @pytest.mark.asyncio
    async def test_anonymous_fallback(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AILINE_LOCAL_STORE", str(tmp_path))
        args = SavePlanArgs(
            plan_json={"title": "Plan"},
            metadata={},
        )
        result = await save_plan_handler(args)
        assert result["teacher_id"] == "anonymous"
        stored_path = Path(result["stored_at"])
        assert stored_path.exists()
        assert "anonymous" in str(stored_path)
