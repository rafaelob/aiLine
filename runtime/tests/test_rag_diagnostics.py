"""Tests for RAG diagnostics entities, store, and API endpoint."""

from __future__ import annotations

import pytest

from ailine_runtime.domain.entities.rag_diagnostics import (
    AnswerabilityCheck,
    RAGChunkProvenance,
    RAGDiagnostics,
    build_diagnostics,
    check_answerability,
)
from ailine_runtime.shared.rag_diagnostics_store import RAGDiagnosticsStore

# ---------------------------------------------------------------------------
# Answerability check
# ---------------------------------------------------------------------------


class TestCheckAnswerability:
    def test_no_results_not_answerable(self) -> None:
        result = check_answerability([])
        assert not result.answerable
        assert result.confidence == "low"
        assert result.top_score == 0.0

    def test_below_threshold_not_answerable(self) -> None:
        result = check_answerability([0.5, 0.3, 0.2], threshold=0.7)
        assert not result.answerable
        assert result.confidence == "low"

    def test_at_threshold_answerable_medium(self) -> None:
        result = check_answerability([0.72, 0.5], threshold=0.7)
        assert result.answerable
        assert result.confidence == "medium"

    def test_high_score_answerable_high(self) -> None:
        result = check_answerability([0.9, 0.85, 0.6], threshold=0.7)
        assert result.answerable
        assert result.confidence == "high"

    def test_custom_threshold(self) -> None:
        result = check_answerability([0.55], threshold=0.5)
        assert result.answerable
        assert result.score_threshold == 0.5


# ---------------------------------------------------------------------------
# build_diagnostics
# ---------------------------------------------------------------------------


class TestBuildDiagnostics:
    def test_empty_results(self) -> None:
        diag = build_diagnostics(
            run_id="r1",
            query="test query",
            results=[],
        )
        assert diag.run_id == "r1"
        assert diag.query == "test query"
        assert len(diag.chunks) == 0
        assert not diag.answerability.answerable

    def test_with_results(self) -> None:
        results = [
            {
                "id": "chunk-1",
                "score": 0.92,
                "text": "Fracoes sao numeros da forma a/b.",
                "title": "Matematica 5o ano",
                "section": "Cap 3 - Fracoes",
                "metadata": {"doc_id": "doc-abc", "page": 42},
            },
            {
                "id": "chunk-2",
                "score": 0.75,
                "text": "Para comparar fracoes com denominadores diferentes...",
                "title": "Matematica 5o ano",
                "section": "Cap 3 - Fracoes",
                "metadata": {"doc_id": "doc-abc", "page": 45},
            },
        ]
        diag = build_diagnostics(
            run_id="r2",
            query="o que sao fracoes?",
            results=results,
            k_requested=5,
            filters={"teacher_id": "t1", "subject": "Matematica"},
        )
        assert diag.run_id == "r2"
        assert len(diag.chunks) == 2
        assert diag.chunks[0].chunk_id == "chunk-1"
        assert diag.chunks[0].retrieval_score == 0.92
        assert diag.chunks[0].doc_title == "Matematica 5o ano"
        assert diag.chunks[0].page == 42
        assert diag.answerability.answerable
        assert diag.answerability.confidence == "high"
        assert diag.top_k_requested == 5
        assert diag.top_k_returned == 2
        assert diag.filters_applied == {"teacher_id": "t1", "subject": "Matematica"}
        assert "2/2 chunks above threshold" in diag.selection_rationale

    def test_text_preview_truncation(self) -> None:
        long_text = "x" * 500
        results = [{"id": "c1", "score": 0.8, "text": long_text}]
        diag = build_diagnostics(run_id="r3", query="q", results=results)
        assert len(diag.chunks[0].text_preview) == 200

    def test_alternative_field_names(self) -> None:
        """Results can use various field name conventions."""
        results = [
            {
                "chunk_id": "alt-1",
                "similarity": 0.88,
                "content": "Some content",
                "doc_title": "Doc A",
                "heading": "Section X",
            }
        ]
        diag = build_diagnostics(run_id="r4", query="q", results=results)
        assert diag.chunks[0].chunk_id == "alt-1"
        assert diag.chunks[0].retrieval_score == 0.88
        assert diag.chunks[0].section == "Section X"


# ---------------------------------------------------------------------------
# RAGDiagnosticsStore
# ---------------------------------------------------------------------------


class TestRAGDiagnosticsStore:
    @pytest.fixture()
    def store(self) -> RAGDiagnosticsStore:
        return RAGDiagnosticsStore(ttl_seconds=60, max_entries=10)

    async def test_save_and_get(self, store: RAGDiagnosticsStore) -> None:
        diag = RAGDiagnostics(run_id="r1", query="test")
        await store.save(diag)
        result = await store.get("r1")
        assert result is not None
        assert result.run_id == "r1"

    async def test_get_nonexistent(self, store: RAGDiagnosticsStore) -> None:
        result = await store.get("nonexistent")
        assert result is None

    async def test_list_recent(self, store: RAGDiagnosticsStore) -> None:
        for i in range(5):
            await store.save(RAGDiagnostics(run_id=f"r{i}", query=f"q{i}"))
        results = await store.list_recent(limit=3)
        assert len(results) == 3

    async def test_capacity_enforcement(self, store: RAGDiagnosticsStore) -> None:
        for i in range(15):  # exceeds max_entries=10
            await store.save(RAGDiagnostics(run_id=f"r{i}", query=f"q{i}"))
        results = await store.list_recent(limit=20)
        assert len(results) <= 10


# ---------------------------------------------------------------------------
# Model serialization
# ---------------------------------------------------------------------------


class TestDiagnosticsModel:
    def test_chunk_provenance_serialization(self) -> None:
        chunk = RAGChunkProvenance(
            chunk_id="c1",
            doc_title="Doc",
            doc_id="d1",
            page=10,
            section="Intro",
            retrieval_score=0.85,
            text_preview="Sample text",
        )
        data = chunk.model_dump()
        assert data["chunk_id"] == "c1"
        assert data["page"] == 10

    def test_answerability_serialization(self) -> None:
        check = AnswerabilityCheck(
            answerable=True,
            confidence="high",
            top_score=0.92,
        )
        data = check.model_dump()
        assert data["answerable"] is True
        assert data["confidence"] == "high"

    def test_full_diagnostics_serialization(self) -> None:
        diag = build_diagnostics(
            run_id="test",
            query="query",
            results=[{"id": "c1", "score": 0.8, "text": "text"}],
        )
        data = diag.model_dump()
        assert "chunks" in data
        assert "answerability" in data
        assert "selection_rationale" in data
