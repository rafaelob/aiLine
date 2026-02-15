"""Tests for Libras vocabulary constants."""

from __future__ import annotations

from ailine_runtime.ml.vocabulary import (
    BLANK_TOKEN,
    LABEL_TO_ID,
    LIBRAS_VOCABULARY,
    TRANSITION_TOKEN,
    VOCAB_SIZE,
)


class TestVocabulary:
    """Verify vocabulary structure and constants."""

    def test_blank_token_is_zero(self):
        assert BLANK_TOKEN == 0

    def test_transition_token_is_one(self):
        assert TRANSITION_TOKEN == 1

    def test_vocab_ids_start_at_2(self):
        """Real glosses start at id=2, after blank and transition."""
        assert min(LIBRAS_VOCABULARY.keys()) == 2

    def test_vocab_has_30_signs(self):
        assert len(LIBRAS_VOCABULARY) == 30

    def test_vocab_size_includes_special_tokens(self):
        assert len(LIBRAS_VOCABULARY) + 2 == VOCAB_SIZE

    def test_common_signs_present(self):
        labels = set(LIBRAS_VOCABULARY.values())
        expected = {
            "OI",
            "TUDO-BEM",
            "OBRIGADO",
            "POR-FAVOR",
            "SIM",
            "NAO",
            "EU",
            "VOCE",
            "CASA",
            "ESCOLA",
            "PROFESSOR",
            "ALUNO",
            "ESTUDAR",
            "APRENDER",
            "AJUDA",
            "ENTENDER",
            "GOSTAR",
            "QUERER",
            "PRECISAR",
            "DESCULPA",
            "BOM",
            "MAU",
            "GRANDE",
            "PEQUENO",
            "HOJE",
            "AMANHA",
            "ONTEM",
            "NUMERO",
            "NOME",
            "AGUA",
        }
        assert labels == expected

    def test_all_labels_uppercase(self):
        for label in LIBRAS_VOCABULARY.values():
            assert label == label.upper(), f"Label {label!r} is not uppercase"

    def test_no_duplicate_ids(self):
        ids = list(LIBRAS_VOCABULARY.keys())
        assert len(ids) == len(set(ids))

    def test_no_duplicate_labels(self):
        labels = list(LIBRAS_VOCABULARY.values())
        assert len(labels) == len(set(labels))

    def test_reverse_mapping_consistent(self):
        for gloss_id, label in LIBRAS_VOCABULARY.items():
            assert LABEL_TO_ID[label] == gloss_id

    def test_reverse_mapping_same_size(self):
        assert len(LABEL_TO_ID) == len(LIBRAS_VOCABULARY)

    def test_ids_are_contiguous(self):
        ids = sorted(LIBRAS_VOCABULARY.keys())
        expected = list(range(2, 2 + len(LIBRAS_VOCABULARY)))
        assert ids == expected
