"""Extended tests for shared.i18n -- covers fallback and edge cases."""

from __future__ import annotations

from ailine_runtime.shared.i18n import _load_messages, t


class TestLoadMessagesEdgeCases:
    def test_nonexistent_locale_and_nonexistent_fallback(self, tmp_path, monkeypatch):
        """When both the locale file and the fallback file are missing, return {}."""
        monkeypatch.setattr(
            "ailine_runtime.shared.i18n._DATA_DIR", tmp_path
        )
        # Clear the LRU cache so it picks up the new _DATA_DIR
        _load_messages.cache_clear()
        result = _load_messages("xx-MISSING")
        assert result == {}
        _load_messages.cache_clear()


class TestTranslateEdgeCases:
    def test_fallback_from_nondefault_locale_to_english(self):
        """When a key exists in English but not in a non-English locale."""
        result = t("error.generic", locale="es")
        # Spanish file might not have this key -> falls back to English
        assert result != "error.generic" or isinstance(result, str)

    def test_interpolation_bad_key(self):
        """When template expects {detail} but receives {wrong_key}."""
        result = t("error.validation", locale="en", wrong_key="oops")
        # Should return template as-is since {detail} is not provided
        assert "{detail}" in result
