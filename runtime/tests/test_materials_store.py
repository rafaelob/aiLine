"""Tests for materials.store -- local material persistence and search."""

from __future__ import annotations

from pathlib import Path

import pytest

from ailine_runtime.materials.store import (
    Material,
    _chunk_text,
    _slug,
    _tokens,
    add_material,
    iter_materials,
    load_material,
    search_materials,
)


@pytest.fixture
def store_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    store = tmp_path / "store"
    store.mkdir()
    monkeypatch.setenv("AILINE_LOCAL_STORE", str(store))
    return store


class TestSlug:
    def test_basic(self):
        assert _slug("Matematica") == "matematica"

    def test_special_chars(self):
        result = _slug("Ciencias da Natureza!")
        assert result == "ciencias-da-natureza"

    def test_empty(self):
        assert _slug("") == "subject"

    def test_spaces(self):
        assert _slug("  hello  world  ") == "hello-world"


class TestTokens:
    def test_filters_stop_words(self):
        tokens = _tokens("o aluno e a professora")
        assert "aluno" in tokens
        assert "professora" in tokens
        assert "o" not in tokens
        assert "e" not in tokens
        assert "a" not in tokens

    def test_filters_short_tokens(self):
        tokens = _tokens("I am a x b")
        assert "x" not in tokens
        assert "am" in tokens


class TestChunkText:
    def test_single_paragraph(self):
        text = "Short text."
        chunks = _chunk_text(text, max_chars=100)
        assert chunks == ["Short text."]

    def test_multiple_paragraphs(self):
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = _chunk_text(text, max_chars=40)
        assert len(chunks) >= 2

    def test_empty_text(self):
        chunks = _chunk_text("", max_chars=100)
        assert len(chunks) == 1

    def test_long_single_paragraph(self):
        text = "A" * 2000
        chunks = _chunk_text(text, max_chars=900)
        assert len(chunks) >= 1
        assert len(chunks[0]) <= 900

    def test_paragraph_exact_multiple_of_max(self):
        """When paragraph length is exact multiple of max_chars, while loop exhausts it."""
        text = "B" * 1800  # Exactly 2 * 900
        chunks = _chunk_text(text, max_chars=900)
        assert len(chunks) == 2
        assert all(len(c) == 900 for c in chunks)

    def test_whitespace_paragraphs_produce_fallback(self):
        """Text that consists only of whitespace paragraphs."""
        text = "\n\n   \n\n   \n\n"
        chunks = _chunk_text(text, max_chars=100)
        # All paragraphs are whitespace-only, stripped to empty,
        # so chunks list ends up empty -> fallback to [text[:max_chars]]
        assert len(chunks) == 1

    def test_paragraph_exact_multiple_of_max_chars(self):
        """Paragraph whose length is exact multiple of max_chars (line 157).

        After ``while len(p) > max_chars`` exhausts all characters,
        p becomes empty string and ``if not p: continue`` is hit.
        """
        max_c = 10
        # Paragraph of exactly 20 chars = 2 * max_c
        # After two iterations of the while loop, p == "" -> continue
        text = "A" * (max_c * 2)
        chunks = _chunk_text(text, max_chars=max_c)
        # Should produce exactly 2 chunks of max_c chars each
        assert len(chunks) == 2
        assert all(len(c) == max_c for c in chunks)


class TestAddMaterial:
    def test_creates_file(self, store_dir):
        m = add_material(
            teacher_id="t1",
            subject="Math",
            title="Fractions Intro",
            content="This is about fractions.",
            tags=["fracoes"],
        )
        assert isinstance(m, Material)
        assert m.teacher_id == "t1"
        assert m.subject == "Math"
        assert m.title == "Fractions Intro"
        assert "fracoes" in m.tags
        # File should exist
        files = list((store_dir / "materials" / "t1").rglob("*.json"))
        assert len(files) == 1

    def test_auto_timestamp(self, store_dir):
        m = add_material(
            teacher_id="t1",
            subject="Science",
            title="Ecosystems",
            content="About ecosystems.",
        )
        assert m.created_at  # Should be auto-generated
        assert m.tags == []  # Default empty

    def test_custom_timestamp(self, store_dir):
        m = add_material(
            teacher_id="t1",
            subject="Math",
            title="Test",
            content="Content",
            created_at="2026-01-01T00:00:00",
        )
        assert m.created_at == "2026-01-01T00:00:00"


class TestLoadMaterial:
    def test_found(self, store_dir):
        m = add_material(
            teacher_id="t1",
            subject="Math",
            title="Test",
            content="Content",
        )
        loaded = load_material(m.material_id, teacher_id="t1", subject="Math")
        assert loaded is not None
        assert loaded.material_id == m.material_id

    def test_not_found(self, store_dir):
        result = load_material("nonexistent-id")
        assert result is None

    def test_found_without_filters(self, store_dir):
        m = add_material(
            teacher_id="t1",
            subject="Math",
            title="Test",
            content="Content",
        )
        loaded = load_material(m.material_id)
        assert loaded is not None


class TestIterMaterials:
    def test_iter_all(self, store_dir):
        add_material(teacher_id="t1", subject="Math", title="M1", content="C1")
        add_material(teacher_id="t2", subject="Science", title="M2", content="C2")
        all_mats = list(iter_materials())
        assert len(all_mats) == 2

    def test_iter_by_teacher(self, store_dir):
        add_material(teacher_id="t1", subject="Math", title="M1", content="C1")
        add_material(teacher_id="t2", subject="Math", title="M2", content="C2")
        t1_mats = list(iter_materials(teacher_id="t1"))
        assert len(t1_mats) == 1
        assert t1_mats[0].teacher_id == "t1"

    def test_iter_by_subject(self, store_dir):
        add_material(teacher_id="t1", subject="Math", title="M1", content="C1")
        add_material(teacher_id="t1", subject="Science", title="M2", content="C2")
        math_mats = list(iter_materials(teacher_id="t1", subject="Math"))
        assert len(math_mats) == 1

    def test_iter_nonexistent_teacher(self, store_dir):
        mats = list(iter_materials(teacher_id="nonexistent"))
        assert mats == []

    def test_iter_nonexistent_subject(self, store_dir):
        add_material(teacher_id="t1", subject="Math", title="M1", content="C1")
        mats = list(iter_materials(teacher_id="t1", subject="Nonexistent"))
        assert mats == []

    def test_iter_skips_invalid_json(self, store_dir):
        add_material(teacher_id="t1", subject="Math", title="Valid", content="C")
        # Create an invalid JSON file
        subdir = store_dir / "materials" / "t1" / "math"
        subdir.mkdir(parents=True, exist_ok=True)
        (subdir / "bad.json").write_text("not json", encoding="utf-8")
        mats = list(iter_materials(teacher_id="t1"))
        assert len(mats) == 1  # Only the valid one


class TestSearchMaterials:
    def test_search_basic(self, store_dir):
        add_material(
            teacher_id="t1",
            subject="Math",
            title="Fractions",
            content="Teaching fractions to students using visual methods.",
        )
        results = search_materials(query="fractions visual", teacher_id="t1")
        assert len(results) >= 1
        assert results[0]["title"] == "Fractions"

    def test_search_empty_query(self, store_dir):
        add_material(teacher_id="t1", subject="Math", title="T", content="Content")
        results = search_materials(query="", teacher_id="t1")
        assert results == []

    def test_search_no_match(self, store_dir):
        add_material(
            teacher_id="t1",
            subject="Math",
            title="T",
            content="Something about algebra.",
        )
        results = search_materials(query="quantum physics", teacher_id="t1")
        assert results == []

    def test_search_with_tags(self, store_dir):
        add_material(
            teacher_id="t1",
            subject="Math",
            title="Tagged",
            content="Fractions lesson plan.",
            tags=["fracoes", "bncc:EF04MA07"],
        )
        add_material(
            teacher_id="t1",
            subject="Math",
            title="Untagged",
            content="Fractions exercise.",
            tags=["exercicios"],
        )
        results = search_materials(query="fractions", teacher_id="t1", tags=["fracoes"])
        assert len(results) == 1
        assert results[0]["title"] == "Tagged"

    def test_search_with_material_ids(self, store_dir):
        m1 = add_material(
            teacher_id="t1",
            subject="Math",
            title="M1",
            content="Fractions content.",
        )
        add_material(
            teacher_id="t1",
            subject="Math",
            title="M2",
            content="Fractions other content.",
        )
        results = search_materials(query="fractions", teacher_id="t1", material_ids=[m1.material_id])
        assert len(results) == 1
        assert results[0]["material_id"] == m1.material_id

    def test_search_k_limit(self, store_dir):
        for i in range(5):
            add_material(
                teacher_id="t1",
                subject="Math",
                title=f"Material {i}",
                content=f"Fractions content block {i}.",
            )
        results = search_materials(query="fractions content", teacher_id="t1", k=2)
        assert len(results) <= 2

    def test_search_stop_words_only(self, store_dir):
        add_material(teacher_id="t1", subject="Math", title="T", content="content")
        results = search_materials(query="o a e de", teacher_id="t1")
        assert results == []
