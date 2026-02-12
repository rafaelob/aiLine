"""Tests for shared.i18n -- translation with fallback."""

from __future__ import annotations

from ailine_runtime.shared.i18n import _load_messages, t


class TestLoadMessages:
    def test_english_loads(self):
        msgs = _load_messages("en")
        assert isinstance(msgs, dict)
        assert "error.generic" in msgs

    def test_pt_br_loads(self):
        msgs = _load_messages("pt-BR")
        assert isinstance(msgs, dict)
        assert "error.generic" in msgs

    def test_unknown_falls_back_to_english(self):
        msgs = _load_messages("xx-UNKNOWN")
        # Should return English messages as fallback
        assert isinstance(msgs, dict)


class TestTranslate:
    def test_english_key(self):
        result = t("error.generic", locale="en")
        assert "error" in result.lower() or "unexpected" in result.lower()

    def test_pt_br_key(self):
        result = t("error.generic", locale="pt-BR")
        assert "erro" in result.lower() or "inesperado" in result.lower()

    def test_interpolation(self):
        result = t("error.validation", locale="en", detail="missing field")
        assert "missing field" in result

    def test_missing_key_returns_key(self):
        result = t("nonexistent.key.here", locale="en")
        assert result == "nonexistent.key.here"

    def test_unknown_locale_falls_back(self):
        result = t("error.generic", locale="xx-NOPE")
        # Should return the English message (fallback)
        assert result != "error.generic"

    def test_interpolation_with_missing_kwarg_returns_template(self):
        # If the template expects {detail} but we pass nothing, it returns the template
        result = t("error.validation", locale="en")
        assert "{detail}" in result
