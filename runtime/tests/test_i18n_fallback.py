"""Tests for i18n.py -- covers the fallback path on lines 29-30.

Lines 29-30: When a key exists in English but not in the requested locale,
the function falls back to the English translation.
"""

from __future__ import annotations

from ailine_runtime.shared.i18n import _load_messages, t


class TestFallbackToEnglish:
    """Test the fallback path (lines 29-30) where a key is missing
    in the requested locale but present in English."""

    def test_nonexistent_key_in_locale_falls_back_to_english(self):
        """When a key does not exist in pt-BR but exists in en,
        t() should fall back to the English translation (lines 29-30)."""
        # Use a key that definitely exists in English
        # First, verify it exists in English
        en_msgs = _load_messages("en")
        assert "error.generic" in en_msgs

        # Now test with a locale that either has this key or falls back.
        # The Spanish file has 'error.generic', so use a constructed scenario.
        # Instead, test with a truly non-standard locale that falls back to English.
        result = t("error.generic", locale="xx-NONEXISTENT")
        # xx-NONEXISTENT won't have a file, _load_messages returns en fallback,
        # so the first lookup succeeds. To actually hit lines 29-30, we need
        # a locale that has a file but is missing a specific key.

        # The test below patches a specific locale to have a file without the key.
        assert isinstance(result, str)
        assert result != "error.generic"

    def test_locale_file_exists_but_key_missing(self, tmp_path, monkeypatch):
        """When the locale file exists but lacks the key, fall back to English (lines 29-30)."""
        import json

        # Create a minimal locale file without error.generic
        locale_dir = tmp_path / "i18n"
        locale_dir.mkdir()
        # Create the custom locale file with only one key
        custom_data = {"custom.key": "Custom value"}
        (locale_dir / "zz-TEST.json").write_text(json.dumps(custom_data), encoding="utf-8")
        # Create the English fallback file
        en_data = {"error.generic": "An unexpected error occurred.", "custom.key": "EN custom"}
        (locale_dir / "en.json").write_text(json.dumps(en_data), encoding="utf-8")

        # Point i18n to our temp directory
        monkeypatch.setattr("ailine_runtime.shared.i18n._DATA_DIR", locale_dir)
        _load_messages.cache_clear()

        try:
            # This should hit lines 29-30: key not in zz-TEST, falls back to en
            result = t("error.generic", locale="zz-TEST")
            assert result == "An unexpected error occurred."

            # Verify the custom key from the locale file still works
            result2 = t("custom.key", locale="zz-TEST")
            assert result2 == "Custom value"
        finally:
            _load_messages.cache_clear()

    def test_key_missing_in_both_locale_and_english(self, tmp_path, monkeypatch):
        """When a key is missing in both locale and fallback, return the key itself."""
        import json

        locale_dir = tmp_path / "i18n2"
        locale_dir.mkdir()
        (locale_dir / "en.json").write_text(json.dumps({"only.key": "val"}), encoding="utf-8")
        (locale_dir / "aa-BB.json").write_text(json.dumps({"other.key": "v"}), encoding="utf-8")

        monkeypatch.setattr("ailine_runtime.shared.i18n._DATA_DIR", locale_dir)
        _load_messages.cache_clear()

        try:
            result = t("nonexistent.key", locale="aa-BB")
            assert result == "nonexistent.key"
        finally:
            _load_messages.cache_clear()
