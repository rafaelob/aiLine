"""Tests for curriculum adapters, unified provider, and API endpoints.

Covers BNCC, US (CCSS + NGSS), unified provider, grade mapping,
and the FastAPI curriculum router.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.adapters.curriculum.bncc_provider import BNCCProvider
from ailine_runtime.adapters.curriculum.loader import (
    keyword_matches,
    load_grade_mapping,
    load_objectives_from_json,
    text_matches,
)
from ailine_runtime.adapters.curriculum.unified_provider import (
    UnifiedCurriculumProvider,
)
from ailine_runtime.adapters.curriculum.us_provider import USProvider
from ailine_runtime.api.app import create_app
from ailine_runtime.domain.entities.curriculum import (
    CurriculumObjective,
    CurriculumSystem,
)
from ailine_runtime.shared.config import Settings

# =====================================================================
# Loader utilities
# =====================================================================


class TestLoader:
    def test_load_bncc_json(self):
        objs = load_objectives_from_json("bncc.json")
        assert len(objs) > 0
        assert all(isinstance(o, CurriculumObjective) for o in objs)
        assert all(o.system == CurriculumSystem.BNCC for o in objs)

    def test_load_ccss_json(self):
        objs = load_objectives_from_json("ccss_math.json")
        assert len(objs) > 0
        assert all(o.system == CurriculumSystem.CCSS for o in objs)

    def test_load_ngss_json(self):
        objs = load_objectives_from_json("ngss.json")
        assert len(objs) > 0
        assert all(o.system == CurriculumSystem.NGSS for o in objs)

    def test_load_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            load_objectives_from_json("nonexistent.json")

    def test_load_grade_mapping(self):
        mapping = load_grade_mapping()
        assert "mappings" in mapping
        assert len(mapping["mappings"]) == 9
        first = mapping["mappings"][0]
        assert first["br"] == "1º ano"
        assert first["us"] == "Grade 1"
        assert first["age_range"] == "6-7"

    def test_load_grade_mapping_missing_raises(self, tmp_path, monkeypatch):
        """Missing grade_mapping.json raises FileNotFoundError (line 56)."""
        import ailine_runtime.adapters.curriculum.loader as loader_mod

        monkeypatch.setattr(loader_mod, "_DATA_DIR", tmp_path / "nonexistent")
        with pytest.raises(FileNotFoundError, match="Grade mapping"):
            load_grade_mapping()

    def test_text_matches_case_insensitive(self):
        assert text_matches("math", "Mathematics")
        assert text_matches("MATH", "mathematics")
        assert not text_matches("physics", "Mathematics")

    def test_keyword_matches(self):
        obj = CurriculumObjective(
            code="TEST01",
            system=CurriculumSystem.BNCC,
            subject="Test",
            grade="1",
            description="Resolver problemas de adição",
            keywords=["adição", "subtração"],
            bloom_level=None,
        )
        assert keyword_matches("adição", obj)
        assert keyword_matches("problemas", obj)
        assert not keyword_matches("multiplicação", obj)


# =====================================================================
# BNCC Provider
# =====================================================================


class TestBNCCProvider:
    @pytest.fixture()
    def provider(self) -> BNCCProvider:
        return BNCCProvider()

    async def test_search_by_code_fragment(self, provider: BNCCProvider):
        results = await provider.search("EF06MA01")
        assert len(results) >= 1
        assert results[0].code == "EF06MA01"

    async def test_search_by_keyword(self, provider: BNCCProvider):
        results = await provider.search("frações")
        assert len(results) >= 1
        assert all(
            "fração" in r.description.lower()
            or "frações" in r.description.lower()
            or any(
                "fração" in kw.lower() or "frações" in kw.lower() for kw in r.keywords
            )
            for r in results
        )

    async def test_search_with_grade_filter(self, provider: BNCCProvider):
        results = await provider.search("números", grade="6º ano")
        assert len(results) >= 1
        assert all("6" in r.grade for r in results)

    async def test_search_with_subject_filter(self, provider: BNCCProvider):
        results = await provider.search("comparar", subject="Ciências")
        assert len(results) >= 1
        assert all("ciências" in r.subject.lower() for r in results)

    async def test_search_wrong_system_returns_empty(self, provider: BNCCProvider):
        results = await provider.search("math", system="ccss")
        assert results == []

    async def test_get_by_code_found(self, provider: BNCCProvider):
        obj = await provider.get_by_code("EF01MA01")
        assert obj is not None
        assert obj.code == "EF01MA01"
        assert obj.system == CurriculumSystem.BNCC

    async def test_get_by_code_not_found(self, provider: BNCCProvider):
        obj = await provider.get_by_code("NONEXISTENT")
        assert obj is None

    async def test_list_standards(self, provider: BNCCProvider):
        codes = await provider.list_standards()
        assert len(codes) > 0
        assert "EF01MA01" in codes
        assert all(isinstance(c, str) for c in codes)

    async def test_list_standards_wrong_system(self, provider: BNCCProvider):
        codes = await provider.list_standards(system="ccss")
        assert codes == []

    async def test_search_description_match(self, provider: BNCCProvider):
        results = await provider.search("Pitágoras")
        assert len(results) >= 1
        assert any("Pitágoras" in r.description for r in results)

    async def test_all_objectives_have_required_fields(self, provider: BNCCProvider):
        codes = await provider.list_standards()
        for code in codes:
            obj = await provider.get_by_code(code)
            assert obj is not None
            assert obj.code
            assert obj.system == CurriculumSystem.BNCC
            assert obj.subject
            assert obj.grade
            assert obj.description

    async def test_search_domain_match(self, provider: BNCCProvider):
        results = await provider.search("Geometria")
        assert len(results) >= 1
        # At least some should have Geometria as the domain
        assert any(r.domain == "Geometria" for r in results)

    async def test_search_keyword_only_match(self, provider: BNCCProvider):
        """Query matching only through keywords path in _matches_query (line 97)."""
        from ailine_runtime.adapters.curriculum.bncc_provider import _matches_query

        # Create a synthetic objective where only keyword matches
        obj = CurriculumObjective(
            code="TEST99",
            system=CurriculumSystem.BNCC,
            subject="Subj",
            grade="1",
            domain="Dom",
            description="Something unrelated",
            keywords=["xyz_unique_keyword"],
            bloom_level=None,
        )
        # This query does not appear in code/description/domain/subject
        assert _matches_query("xyz_unique_keyword", obj) is True

    async def test_matches_query_subject_match(self, provider: BNCCProvider):
        """Query matching via subject field in _matches_query (line 96)."""
        from ailine_runtime.adapters.curriculum.bncc_provider import _matches_query

        obj = CurriculumObjective(
            code="ZZZ00",
            system=CurriculumSystem.BNCC,
            subject="Zoologia Especial",
            grade="1",
            domain="Nada",
            description="Texto completamente diferente",
            keywords=[],
            bloom_level=None,
        )
        # Query matches subject but NOT code, description, or domain
        assert _matches_query("zoologia especial", obj) is True


# =====================================================================
# US Provider (CCSS + NGSS)
# =====================================================================


class TestUSProvider:
    @pytest.fixture()
    def provider(self) -> USProvider:
        return USProvider()

    async def test_search_ccss_code(self, provider: USProvider):
        results = await provider.search("CCSS.MATH.CONTENT.6.NS.A.1")
        assert len(results) >= 1
        assert results[0].code == "CCSS.MATH.CONTENT.6.NS.A.1"

    async def test_search_ngss_code(self, provider: USProvider):
        results = await provider.search("MS-PS1-1")
        assert len(results) >= 1
        assert results[0].system == CurriculumSystem.NGSS

    async def test_search_with_system_ccss(self, provider: USProvider):
        results = await provider.search("fractions", system="ccss")
        assert len(results) >= 1
        assert all(r.system == CurriculumSystem.CCSS for r in results)

    async def test_search_with_system_ngss(self, provider: USProvider):
        results = await provider.search("forces", system="ngss")
        assert len(results) >= 1
        assert all(r.system == CurriculumSystem.NGSS for r in results)

    async def test_search_wrong_system_returns_empty(self, provider: USProvider):
        results = await provider.search("math", system="bncc")
        assert results == []

    async def test_search_with_grade_filter(self, provider: USProvider):
        results = await provider.search("fractions", grade="Grade 5")
        assert len(results) >= 1
        assert all("5" in r.grade for r in results)

    async def test_get_by_code_ccss(self, provider: USProvider):
        obj = await provider.get_by_code("CCSS.MATH.CONTENT.8.G.B.6")
        assert obj is not None
        assert obj.system == CurriculumSystem.CCSS
        assert "Pythagorean" in obj.description

    async def test_get_by_code_ngss(self, provider: USProvider):
        obj = await provider.get_by_code("5-PS1-1")
        assert obj is not None
        assert obj.system == CurriculumSystem.NGSS

    async def test_get_by_code_not_found(self, provider: USProvider):
        obj = await provider.get_by_code("NONEXISTENT")
        assert obj is None

    async def test_list_standards_all(self, provider: USProvider):
        codes = await provider.list_standards()
        assert len(codes) > 0
        # Should have both CCSS and NGSS codes
        ccss_codes = [c for c in codes if c.startswith("CCSS")]
        ngss_codes = [c for c in codes if not c.startswith("CCSS")]
        assert len(ccss_codes) > 0
        assert len(ngss_codes) > 0

    async def test_list_standards_system_filter(self, provider: USProvider):
        codes = await provider.list_standards(system="ngss")
        assert len(codes) > 0
        assert all(not c.startswith("CCSS") for c in codes)

    async def test_list_standards_wrong_system(self, provider: USProvider):
        codes = await provider.list_standards(system="bncc")
        assert codes == []

    async def test_search_subject_filter(self, provider: USProvider):
        results = await provider.search("model", subject="Science")
        assert len(results) >= 1
        assert all("science" in r.subject.lower() for r in results)

    async def test_search_keyword_only_match(self, provider: USProvider):
        """Query matching only through keywords in US _matches_query (line 123)."""
        from ailine_runtime.adapters.curriculum.us_provider import _matches_query

        obj = CurriculumObjective(
            code="ZZZ00",
            system=CurriculumSystem.CCSS,
            subject="Nada Aqui",
            grade="1",
            domain="Outro",
            description="Texto diferente",
            keywords=["xyz_special_kw_us"],
            bloom_level=None,
        )
        assert _matches_query("xyz_special_kw_us", obj) is True

    async def test_matches_query_subject_match(self, provider: USProvider):
        """Query matching via subject field in US _matches_query (line 122)."""
        from ailine_runtime.adapters.curriculum.us_provider import _matches_query

        obj = CurriculumObjective(
            code="ZZZ00",
            system=CurriculumSystem.CCSS,
            subject="Zoologia Especial US",
            grade="1",
            domain="Nada",
            description="Texto completamente diferente",
            keywords=[],
            bloom_level=None,
        )
        assert _matches_query("zoologia especial us", obj) is True

    async def test_ensure_loaded_cached_on_second_call(self, provider: USProvider):
        """Second call to _ensure_loaded returns early (line 31)."""
        # First call triggers full load
        codes1 = await provider.list_standards()
        assert len(codes1) > 0
        assert provider._loaded is True
        # Second call hits the early-return guard at line 31
        codes2 = await provider.list_standards()
        assert codes1 == codes2


# =====================================================================
# Unified Provider
# =====================================================================


class TestUnifiedProvider:
    @pytest.fixture()
    def provider(self) -> UnifiedCurriculumProvider:
        return UnifiedCurriculumProvider()

    async def test_search_returns_mixed_systems(
        self, provider: UnifiedCurriculumProvider
    ):
        # "números" appears in BNCC; "number" appears in CCSS — search for "numer"
        # which is a common fragment. Use "frações" which is BNCC-only.
        bncc_results = await provider.search("frações", system="bncc")
        assert len(bncc_results) >= 1
        us_results = await provider.search("fractions", system="ccss")
        assert len(us_results) >= 1

    async def test_search_no_system_filter(self, provider: UnifiedCurriculumProvider):
        # "Geometry" appears as domain in both BNCC (Geometria) and CCSS
        results = await provider.search("Geometry")
        # CCSS has Geometry domain entries
        systems = {r.system for r in results}
        assert CurriculumSystem.CCSS in systems

    async def test_search_bncc_system_filter(self, provider: UnifiedCurriculumProvider):
        results = await provider.search("números", system="bncc")
        assert all(r.system == CurriculumSystem.BNCC for r in results)

    async def test_search_ccss_system_filter(self, provider: UnifiedCurriculumProvider):
        results = await provider.search("fractions", system="ccss")
        assert all(r.system == CurriculumSystem.CCSS for r in results)

    async def test_get_by_code_bncc(self, provider: UnifiedCurriculumProvider):
        obj = await provider.get_by_code("EF06MA01")
        assert obj is not None
        assert obj.system == CurriculumSystem.BNCC

    async def test_get_by_code_ccss(self, provider: UnifiedCurriculumProvider):
        obj = await provider.get_by_code("CCSS.MATH.CONTENT.8.G.B.6")
        assert obj is not None
        assert obj.system == CurriculumSystem.CCSS

    async def test_get_by_code_ngss(self, provider: UnifiedCurriculumProvider):
        obj = await provider.get_by_code("5-PS1-1")
        assert obj is not None
        assert obj.system == CurriculumSystem.NGSS

    async def test_get_by_code_not_found(self, provider: UnifiedCurriculumProvider):
        obj = await provider.get_by_code("NONEXISTENT")
        assert obj is None

    async def test_list_standards_all(self, provider: UnifiedCurriculumProvider):
        codes = await provider.list_standards()
        assert len(codes) > 0
        # Should contain codes from all three systems
        assert any(c.startswith("EF") for c in codes)  # BNCC
        assert any(c.startswith("CCSS") for c in codes)  # CCSS
        assert any(c.endswith("-1") for c in codes)  # NGSS-style codes

    async def test_list_standards_bncc_only(self, provider: UnifiedCurriculumProvider):
        codes = await provider.list_standards(system="bncc")
        assert len(codes) > 0
        # BNCC codes: EF (Ensino Fundamental), EI (Educacao Infantil), EM (Ensino Medio)
        assert all(c.startswith(("EF", "EI", "EM")) for c in codes)

    async def test_list_standards_ngss_only(self, provider: UnifiedCurriculumProvider):
        codes = await provider.list_standards(system="ngss")
        assert len(codes) > 0
        assert all(not c.startswith("CCSS") and not c.startswith("EF") for c in codes)

    async def test_grade_mapping(self, provider: UnifiedCurriculumProvider):
        mapping = provider.get_grade_mapping()
        assert "mappings" in mapping
        assert len(mapping["mappings"]) == 9

    async def test_translate_grade_br_to_us(self, provider: UnifiedCurriculumProvider):
        assert provider.translate_grade("6º ano") == "Grade 6"
        assert provider.translate_grade("1º ano") == "Grade 1"
        assert provider.translate_grade("9º ano") == "Grade 9"

    async def test_translate_grade_us_to_br(self, provider: UnifiedCurriculumProvider):
        assert provider.translate_grade("Grade 6") == "6º ano"
        assert provider.translate_grade("Grade 1") == "1º ano"

    async def test_translate_grade_kindergarten(
        self, provider: UnifiedCurriculumProvider
    ):
        result = provider.translate_grade("Grade K")
        assert result == "Educação Infantil"

    async def test_translate_grade_kindergarten_br_to_us(
        self, provider: UnifiedCurriculumProvider
    ):
        """Translate kindergarten from BR to US (line 75)."""
        result = provider.translate_grade("Educação Infantil")
        assert result == "Grade K"

    async def test_translate_grade_not_found(self, provider: UnifiedCurriculumProvider):
        assert provider.translate_grade("Grade 99") is None

    async def test_with_custom_subproviders(self):
        bncc = BNCCProvider()
        us = USProvider()
        provider = UnifiedCurriculumProvider(bncc=bncc, us=us)
        codes = await provider.list_standards()
        assert len(codes) > 0


# =====================================================================
# API Endpoints
# =====================================================================


class TestCurriculumAPIFallbackProvider:
    """Cover _get_provider both paths: fallback creation and cached return."""

    async def test_fallback_provider_created_when_not_on_state(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        """When curriculum_provider is not on app.state, a new one is created."""
        monkeypatch.setenv("AILINE_DEV_MODE", "true")
        settings = Settings(
            anthropic_api_key="",
            openai_api_key="",
            google_api_key="",
            openrouter_api_key="",
        )
        app = create_app(settings)
        # Remove the curriculum_provider from state if it exists
        if hasattr(app.state, "curriculum_provider"):
            delattr(app.state, "curriculum_provider")

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-Teacher-ID": "teacher-001"},
        ) as ac:
            resp = await ac.get("/curriculum/search", params={"q": "EF06MA01"})
            assert resp.status_code == 200
            # After the call, the provider should be cached on app.state
            assert hasattr(app.state, "curriculum_provider")

    async def test_cached_provider_returned_when_on_state(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        """When curriculum_provider IS on app.state, return it (line 27)."""
        monkeypatch.setenv("AILINE_DEV_MODE", "true")
        settings = Settings(
            anthropic_api_key="",
            openai_api_key="",
            google_api_key="",
            openrouter_api_key="",
        )
        app = create_app(settings)
        # Pre-set the provider on state so line 27 is hit
        pre_set_provider = UnifiedCurriculumProvider()
        app.state.curriculum_provider = pre_set_provider

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-Teacher-ID": "teacher-001"},
        ) as ac:
            resp = await ac.get("/curriculum/search", params={"q": "EF06MA01"})
            assert resp.status_code == 200
            # The provider on state should still be the same object
            assert app.state.curriculum_provider is pre_set_provider


class TestCurriculumAPI:
    @pytest.fixture()
    def app(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("AILINE_DEV_MODE", "true")
        settings = Settings(
            anthropic_api_key="",
            openai_api_key="",
            google_api_key="",
            openrouter_api_key="",
        )
        return create_app(settings)

    @pytest.fixture()
    async def client(self, app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-Teacher-ID": "teacher-001"},
        ) as ac:
            yield ac

    async def test_search_endpoint(self, client: AsyncClient):
        resp = await client.get("/curriculum/search", params={"q": "EF06MA01"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["code"] == "EF06MA01"

    async def test_search_with_filters(self, client: AsyncClient):
        resp = await client.get(
            "/curriculum/search",
            params={"q": "números", "grade": "6º ano", "system": "bncc"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all(d["system"] == "bncc" for d in data)

    async def test_search_missing_query_returns_422(self, client: AsyncClient):
        resp = await client.get("/curriculum/search")
        assert resp.status_code == 422

    async def test_search_empty_query_returns_422(self, client: AsyncClient):
        resp = await client.get("/curriculum/search", params={"q": ""})
        assert resp.status_code == 422

    async def test_standards_list(self, client: AsyncClient):
        resp = await client.get("/curriculum/standards")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        assert isinstance(data, list)
        assert all(isinstance(c, str) for c in data)

    async def test_standards_list_with_system(self, client: AsyncClient):
        resp = await client.get("/curriculum/standards", params={"system": "ngss"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        assert all(not c.startswith("CCSS") and not c.startswith("EF") for c in data)

    async def test_get_by_code_found(self, client: AsyncClient):
        resp = await client.get("/curriculum/standards/EF01MA01")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "EF01MA01"
        assert data["system"] == "bncc"
        assert "description" in data

    async def test_get_by_code_not_found(self, client: AsyncClient):
        resp = await client.get("/curriculum/standards/NONEXISTENT")
        assert resp.status_code == 404

    async def test_grade_mapping_endpoint(self, client: AsyncClient):
        resp = await client.get("/curriculum/grade-mapping")
        assert resp.status_code == 200
        data = resp.json()
        assert "mappings" in data
        assert len(data["mappings"]) == 9

    async def test_grade_translate_br_to_us(self, client: AsyncClient):
        resp = await client.get(
            "/curriculum/grade-mapping/translate",
            params={"grade": "6º ano"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["translated"] == "Grade 6"

    async def test_grade_translate_us_to_br(self, client: AsyncClient):
        resp = await client.get(
            "/curriculum/grade-mapping/translate",
            params={"grade": "Grade 3"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["translated"] == "3º ano"

    async def test_grade_translate_not_found(self, client: AsyncClient):
        resp = await client.get(
            "/curriculum/grade-mapping/translate",
            params={"grade": "Grade 99"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["translated"] is None

    async def test_search_ccss_fractions(self, client: AsyncClient):
        resp = await client.get(
            "/curriculum/search",
            params={"q": "fractions", "system": "ccss"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all(d["system"] == "ccss" for d in data)

    async def test_search_ngss_forces(self, client: AsyncClient):
        resp = await client.get(
            "/curriculum/search",
            params={"q": "forces", "system": "ngss"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all(d["system"] == "ngss" for d in data)

    async def test_get_by_code_ccss(self, client: AsyncClient):
        resp = await client.get("/curriculum/standards/CCSS.MATH.CONTENT.8.G.B.6")
        assert resp.status_code == 200
        data = resp.json()
        assert data["system"] == "ccss"
        assert "Pythagorean" in data["description"]

    async def test_get_by_code_ngss(self, client: AsyncClient):
        resp = await client.get("/curriculum/standards/5-PS1-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["system"] == "ngss"


# =====================================================================
# Bloom's Taxonomy (Task #5)
# =====================================================================


class TestBloomTaxonomy:
    """Test bloom_level field on CurriculumObjective and filtering."""

    def test_bloom_level_on_bncc_objectives(self):
        objs = load_objectives_from_json("bncc.json")
        # Every BNCC objective should have a bloom_level
        for obj in objs:
            assert obj.bloom_level is not None, f"{obj.code} missing bloom_level"
            assert obj.bloom_level in (
                "remember",
                "understand",
                "apply",
                "analyze",
                "evaluate",
                "create",
            )

    def test_bloom_level_on_ccss_objectives(self):
        objs = load_objectives_from_json("ccss_math.json")
        for obj in objs:
            assert obj.bloom_level is not None, f"{obj.code} missing bloom_level"

    def test_bloom_level_on_ngss_objectives(self):
        objs = load_objectives_from_json("ngss.json")
        for obj in objs:
            assert obj.bloom_level is not None, f"{obj.code} missing bloom_level"

    def test_bloom_level_optional_default_none(self):
        obj = CurriculumObjective(
            code="TEST01",
            system=CurriculumSystem.BNCC,
            subject="Test",
            grade="1",
            description="Test description",
        )
        assert obj.bloom_level is None

    def test_bloom_level_set_explicitly(self):
        obj = CurriculumObjective(
            code="TEST01",
            system=CurriculumSystem.BNCC,
            subject="Test",
            grade="1",
            description="Test description",
            bloom_level="analyze",
        )
        assert obj.bloom_level == "analyze"

    async def test_search_with_bloom_filter_bncc(self):
        provider = BNCCProvider()
        # Search for "apply" level objectives about calculation
        results = await provider.search("cálculo", bloom_level="apply")
        assert len(results) >= 1
        assert all(r.bloom_level == "apply" for r in results)

    async def test_search_with_bloom_filter_excludes_other_levels(self):
        provider = BNCCProvider()
        # Search broadly but filter to "create" only
        results = await provider.search("produzir", bloom_level="create")
        assert len(results) >= 1
        assert all(r.bloom_level == "create" for r in results)

    async def test_search_with_bloom_filter_us(self):
        provider = USProvider()
        results = await provider.search("fractions", bloom_level="understand")
        assert len(results) >= 1
        assert all(r.bloom_level == "understand" for r in results)

    async def test_search_with_bloom_filter_unified(self):
        provider = UnifiedCurriculumProvider()
        results = await provider.search("model", bloom_level="create")
        assert len(results) >= 1
        assert all(r.bloom_level == "create" for r in results)

    async def test_bloom_level_in_model_dump(self):
        obj = CurriculumObjective(
            code="TEST01",
            system=CurriculumSystem.BNCC,
            subject="Test",
            grade="1",
            description="Resolver problemas",
            bloom_level="apply",
        )
        data = obj.model_dump()
        assert data["bloom_level"] == "apply"

    async def test_bloom_distribution_bncc(self):
        """Verify BNCC has reasonable Bloom distribution (all 6 levels present)."""
        objs = load_objectives_from_json("bncc.json")
        levels = {obj.bloom_level for obj in objs}
        assert levels == {
            "remember",
            "understand",
            "apply",
            "analyze",
            "evaluate",
            "create",
        }


class TestBloomTaxonomyAPI:
    @pytest.fixture()
    def app(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("AILINE_DEV_MODE", "true")
        settings = Settings(
            anthropic_api_key="",
            openai_api_key="",
            google_api_key="",
            openrouter_api_key="",
        )
        return create_app(settings)

    @pytest.fixture()
    async def client(self, app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-Teacher-ID": "teacher-001"},
        ) as ac:
            yield ac

    async def test_search_with_bloom_filter(self, client: AsyncClient):
        resp = await client.get(
            "/curriculum/search",
            params={"q": "fractions", "bloom_level": "understand"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all(d["bloom_level"] == "understand" for d in data)

    async def test_search_bloom_filter_apply(self, client: AsyncClient):
        resp = await client.get(
            "/curriculum/search",
            params={"q": "resolver", "bloom_level": "apply", "system": "bncc"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all(d["bloom_level"] == "apply" for d in data)

    async def test_search_bloom_filter_no_results(self, client: AsyncClient):
        """Filtering by a bloom level that doesn't match returns empty."""
        resp = await client.get(
            "/curriculum/search",
            params={"q": "EF01MA01", "bloom_level": "create"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # EF01MA01 is "apply" level, filtering for "create" should exclude it
        assert all(d["code"] != "EF01MA01" for d in data)

    async def test_get_by_code_includes_bloom_level(self, client: AsyncClient):
        resp = await client.get("/curriculum/standards/EF01MA01")
        assert resp.status_code == 200
        data = resp.json()
        assert "bloom_level" in data
        assert data["bloom_level"] in (
            "remember",
            "understand",
            "apply",
            "analyze",
            "evaluate",
            "create",
        )


# =====================================================================
# CCSS ELA (Task #6)
# =====================================================================


class TestCCSSELA:
    """Test CCSS ELA curriculum data and integration."""

    def test_load_ccss_ela_json(self):
        objs = load_objectives_from_json("ccss_ela.json")
        assert len(objs) > 0
        assert all(o.system == CurriculumSystem.CCSS_ELA for o in objs)
        assert all(o.subject == "English Language Arts" for o in objs)

    def test_ccss_ela_all_have_bloom_level(self):
        objs = load_objectives_from_json("ccss_ela.json")
        for obj in objs:
            assert obj.bloom_level is not None, f"{obj.code} missing bloom_level"

    def test_ccss_ela_covers_grades_k_through_8(self):
        objs = load_objectives_from_json("ccss_ela.json")
        grades = {obj.grade for obj in objs}
        # Must have at least K, some elementary, and some middle school grades
        assert any("K" in g for g in grades)
        assert any("8" in g for g in grades)
        assert len(grades) >= 5  # At least 5 different grade levels

    def test_ccss_ela_domains(self):
        objs = load_objectives_from_json("ccss_ela.json")
        domains = {obj.domain for obj in objs}
        # Should cover core ELA domains
        assert "Reading: Literature" in domains
        assert "Writing" in domains
        assert "Language" in domains

    def test_ccss_ela_system_enum(self):
        assert CurriculumSystem.CCSS_ELA == "ccss_ela"
        assert CurriculumSystem.CCSS_ELA.value == "ccss_ela"

    async def test_us_provider_loads_ccss_ela(self):
        provider = USProvider()
        codes = await provider.list_standards()
        ela_codes = [c for c in codes if c.startswith("CCSS.ELA")]
        assert len(ela_codes) > 0

    async def test_us_provider_search_ccss_ela_system_filter(self):
        provider = USProvider()
        results = await provider.search("reading", system="ccss_ela")
        assert len(results) >= 1
        assert all(r.system == CurriculumSystem.CCSS_ELA for r in results)

    async def test_us_provider_search_ccss_ela_excluded_by_ccss_filter(self):
        provider = USProvider()
        results = await provider.search("reading", system="ccss")
        # ccss filter should only return CCSS Math, not ELA
        assert all(r.system == CurriculumSystem.CCSS for r in results)

    async def test_unified_provider_includes_ccss_ela(self):
        provider = UnifiedCurriculumProvider()
        codes = await provider.list_standards()
        ela_codes = [c for c in codes if c.startswith("CCSS.ELA")]
        assert len(ela_codes) > 0

    async def test_unified_provider_search_ccss_ela(self):
        provider = UnifiedCurriculumProvider()
        results = await provider.search("arguments", system="ccss_ela")
        assert len(results) >= 1
        assert all(r.system == CurriculumSystem.CCSS_ELA for r in results)

    async def test_unified_get_by_code_ccss_ela(self):
        provider = UnifiedCurriculumProvider()
        obj = await provider.get_by_code("CCSS.ELA-LITERACY.RL.8.1")
        assert obj is not None
        assert obj.system == CurriculumSystem.CCSS_ELA
        assert "textual evidence" in obj.description.lower()

    async def test_unified_list_standards_ccss_ela_only(self):
        provider = UnifiedCurriculumProvider()
        codes = await provider.list_standards(system="ccss_ela")
        assert len(codes) > 0
        assert all(c.startswith("CCSS.ELA") for c in codes)


class TestCCSSELAAPI:
    @pytest.fixture()
    def app(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("AILINE_DEV_MODE", "true")
        settings = Settings(
            anthropic_api_key="",
            openai_api_key="",
            google_api_key="",
            openrouter_api_key="",
        )
        return create_app(settings)

    @pytest.fixture()
    async def client(self, app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-Teacher-ID": "teacher-001"},
        ) as ac:
            yield ac

    async def test_search_ccss_ela(self, client: AsyncClient):
        resp = await client.get(
            "/curriculum/search",
            params={"q": "arguments", "system": "ccss_ela"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all(d["system"] == "ccss_ela" for d in data)

    async def test_get_by_code_ccss_ela(self, client: AsyncClient):
        resp = await client.get("/curriculum/standards/CCSS.ELA-LITERACY.W.8.1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["system"] == "ccss_ela"
        assert data["subject"] == "English Language Arts"
        assert data["bloom_level"] is not None

    async def test_standards_list_ccss_ela(self, client: AsyncClient):
        resp = await client.get("/curriculum/standards", params={"system": "ccss_ela"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        assert all(c.startswith("CCSS.ELA") for c in data)

    async def test_search_ela_with_bloom_filter(self, client: AsyncClient):
        resp = await client.get(
            "/curriculum/search",
            params={"q": "write", "system": "ccss_ela", "bloom_level": "create"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all(d["bloom_level"] == "create" for d in data)
        assert all(d["system"] == "ccss_ela" for d in data)
