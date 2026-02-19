"""Tests for RAG provenance entities (dataclass variant).

Covers:
- RetrievalResult confidence classification
- RAGDiagnostics answerable threshold
- Provenance model serialization (to_dict)
- Diagnostics API endpoint (mock store)
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.api.app import create_app
from ailine_runtime.domain.entities.rag_provenance import (
    RAGDiagnostics,
    RetrievalResult,
)
from ailine_runtime.shared.config import Settings
from ailine_runtime.shared.rag_diagnostics_store import (
    get_rag_diagnostics_store,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AILINE_DEV_MODE", "true")
    settings = Settings(
        anthropic_api_key="",
        openai_api_key="",
        google_api_key="",
        openrouter_api_key="",
        env="development",
    )
    return create_app(settings)


_AUTH = {"X-Teacher-ID": "teacher-test"}


def _make_result(score: float, chunk_id: str = "chunk-1") -> RetrievalResult:
    """Helper to create a RetrievalResult with a given score."""
    return RetrievalResult(
        chunk_id=chunk_id,
        doc_title="Test Document",
        section="Section 1",
        score=score,
        confidence=RetrievalResult.classify_confidence(score),
        text_preview="Lorem ipsum dolor sit amet...",
    )


# ---------------------------------------------------------------------------
# RetrievalResult confidence classification
# ---------------------------------------------------------------------------


class TestRetrievalResultConfidence:
    """Confidence tier classification based on similarity score."""

    def test_high_confidence(self) -> None:
        assert RetrievalResult.classify_confidence(0.95) == "high"
        assert RetrievalResult.classify_confidence(0.80) == "high"

    def test_medium_confidence(self) -> None:
        assert RetrievalResult.classify_confidence(0.75) == "medium"
        assert RetrievalResult.classify_confidence(0.60) == "medium"

    def test_low_confidence(self) -> None:
        assert RetrievalResult.classify_confidence(0.59) == "low"
        assert RetrievalResult.classify_confidence(0.0) == "low"

    def test_boundary_values(self) -> None:
        assert RetrievalResult.classify_confidence(0.8) == "high"
        assert RetrievalResult.classify_confidence(0.6) == "medium"
        assert RetrievalResult.classify_confidence(0.5999) == "low"

    def test_result_creation_with_classification(self) -> None:
        result = _make_result(0.85)
        assert result.confidence == "high"
        assert result.score == 0.85
        assert result.chunk_id == "chunk-1"

    def test_frozen_immutability(self) -> None:
        result = _make_result(0.9)
        with pytest.raises(AttributeError):
            result.score = 0.5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# RAGDiagnostics answerable threshold
# ---------------------------------------------------------------------------


class TestRAGDiagnosticsAnswerable:
    """Answerable determination based on max retrieval score."""

    def test_answerable_when_high_score(self) -> None:
        diag = RAGDiagnostics(
            run_id="run-1",
            query="What are fractions?",
            top_k=5,
            results=[_make_result(0.9), _make_result(0.3)],
        )
        assert diag.compute_answerable() is True
        assert diag.answerable is True

    def test_not_answerable_when_low_scores(self) -> None:
        diag = RAGDiagnostics(
            run_id="run-2",
            query="Quantum physics?",
            top_k=5,
            results=[_make_result(0.3), _make_result(0.2)],
        )
        assert diag.compute_answerable() is False
        assert diag.answerable is False

    def test_not_answerable_when_empty(self) -> None:
        diag = RAGDiagnostics(
            run_id="run-3",
            query="Empty query",
            top_k=5,
            results=[],
        )
        assert diag.compute_answerable() is False

    def test_custom_threshold(self) -> None:
        diag = RAGDiagnostics(
            run_id="run-4",
            query="Test",
            top_k=3,
            results=[_make_result(0.7)],
            answerable_threshold=0.8,
        )
        assert diag.compute_answerable() is False

    def test_boundary_threshold(self) -> None:
        diag = RAGDiagnostics(
            run_id="run-5",
            query="Test",
            top_k=3,
            results=[_make_result(0.6)],
            answerable_threshold=0.6,
        )
        assert diag.compute_answerable() is True


# ---------------------------------------------------------------------------
# Provenance model serialization
# ---------------------------------------------------------------------------


class TestRAGDiagnosticsSerialization:
    """Test to_dict serialization of RAGDiagnostics."""

    def test_to_dict_structure(self) -> None:
        results = [_make_result(0.85, "c1"), _make_result(0.55, "c2")]
        diag = RAGDiagnostics(
            run_id="run-ser",
            query="Test query",
            top_k=5,
            filter_applied={"subject": "math"},
            results=results,
            answerable=True,
            retrieval_time_ms=35.2,
        )
        d = diag.to_dict()

        assert d["run_id"] == "run-ser"
        assert d["query"] == "Test query"
        assert d["top_k"] == 5
        assert d["filter_applied"] == {"subject": "math"}
        assert d["answerable"] is True
        assert d["retrieval_time_ms"] == 35.2
        assert len(d["results"]) == 2
        assert d["results"][0]["chunk_id"] == "c1"
        assert d["results"][0]["confidence"] == "high"
        assert d["results"][1]["confidence"] == "low"

    def test_to_dict_empty_results(self) -> None:
        diag = RAGDiagnostics(run_id="run-empty", query="Q", top_k=3)
        d = diag.to_dict()
        assert d["results"] == []
        assert d["answerable"] is False

    def test_roundtrip_preserves_data(self) -> None:
        results = [_make_result(0.72, "c-rt")]
        diag = RAGDiagnostics(
            run_id="rt-1",
            query="roundtrip",
            top_k=10,
            filter_applied={"teacher_id": "t1"},
            results=results,
            retrieval_time_ms=12.5,
        )
        d = diag.to_dict()
        assert d["results"][0]["score"] == 0.72
        assert d["results"][0]["doc_title"] == "Test Document"


# ---------------------------------------------------------------------------
# Diagnostics API endpoint (using existing Pydantic-based store)
# ---------------------------------------------------------------------------


class TestDiagnosticsAPIEndpoint:
    """Verify the /rag/diagnostics/{run_id} endpoint works end-to-end."""

    @pytest.mark.asyncio
    async def test_get_not_found(self, app) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers=_AUTH,
        ) as client:
            resp = await client.get("/rag/diagnostics/nonexistent")
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, app) -> None:
        """Save via the Pydantic store, retrieve via API."""
        from ailine_runtime.domain.entities.rag_diagnostics import (
            RAGDiagnostics as PydanticRAGDiag,
        )

        store = get_rag_diagnostics_store()
        diag = PydanticRAGDiag(run_id="prov-test-1", query="fracoes")
        await store.save(diag)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers=_AUTH,
        ) as client:
            resp = await client.get("/rag/diagnostics/prov-test-1")
            assert resp.status_code == 200
            data = resp.json()
            assert data["run_id"] == "prov-test-1"
            assert data["query"] == "fracoes"
            assert "answerability" in data
