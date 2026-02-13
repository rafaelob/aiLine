"""Tests for the input sanitization utilities."""

from __future__ import annotations

import pytest

from ailine_runtime.shared.sanitize import (
    sanitize_metadata,
    sanitize_prompt,
    validate_teacher_id,
)


# ---------------------------------------------------------------------------
# sanitize_prompt
# ---------------------------------------------------------------------------


class TestSanitizePrompt:
    def test_basic_text_passes_through(self) -> None:
        assert sanitize_prompt("Hello, world!") == "Hello, world!"

    def test_strips_null_bytes(self) -> None:
        assert sanitize_prompt("Hello\x00World") == "HelloWorld"

    def test_strips_leading_trailing_whitespace(self) -> None:
        assert sanitize_prompt("  hello  ") == "hello"

    def test_truncates_to_max_length(self) -> None:
        long_text = "a" * 100_000
        result = sanitize_prompt(long_text)
        assert len(result) == 50_000

    def test_custom_max_length(self) -> None:
        result = sanitize_prompt("abcdefghij", max_length=5)
        assert result == "abcde"

    def test_nfc_normalization(self) -> None:
        # e + combining acute accent -> e-acute (NFC)
        decomposed = "e\u0301"  # NFD form
        result = sanitize_prompt(decomposed)
        assert result == "\u00e9"  # NFC form

    def test_empty_string(self) -> None:
        assert sanitize_prompt("") == ""

    def test_only_null_bytes(self) -> None:
        assert sanitize_prompt("\x00\x00\x00") == ""

    def test_only_whitespace(self) -> None:
        assert sanitize_prompt("   \t\n  ") == ""

    def test_mixed_null_bytes_and_content(self) -> None:
        assert sanitize_prompt("\x00Hello\x00 \x00World\x00") == "Hello World"


# ---------------------------------------------------------------------------
# validate_teacher_id
# ---------------------------------------------------------------------------


class TestValidateTeacherId:
    def test_valid_uuid(self) -> None:
        tid = "550e8400-e29b-41d4-a716-446655440000"
        assert validate_teacher_id(tid) == tid

    def test_valid_simple_id(self) -> None:
        assert validate_teacher_id("teacher-001") == "teacher-001"

    def test_valid_with_underscores(self) -> None:
        assert validate_teacher_id("teacher_abc_123") == "teacher_abc_123"

    def test_strips_whitespace(self) -> None:
        assert validate_teacher_id("  teacher-001  ") == "teacher-001"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            validate_teacher_id("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            validate_teacher_id("   ")

    def test_too_long_raises(self) -> None:
        with pytest.raises(ValueError, match="exceeds maximum length"):
            validate_teacher_id("a" * 129)

    def test_special_chars_raise(self) -> None:
        with pytest.raises(ValueError, match="alphanumeric"):
            validate_teacher_id("teacher/001")

    def test_path_traversal_rejected(self) -> None:
        with pytest.raises(ValueError, match="alphanumeric"):
            validate_teacher_id("../../etc/passwd")

    def test_unicode_rejected(self) -> None:
        with pytest.raises(ValueError, match="alphanumeric"):
            validate_teacher_id("teacher\u00e9")


# ---------------------------------------------------------------------------
# sanitize_metadata
# ---------------------------------------------------------------------------


class TestSanitizeMetadata:
    def test_basic_dict(self) -> None:
        result = sanitize_metadata({"key": "value"})
        assert result == {"key": "value"}

    def test_strips_null_bytes_in_values(self) -> None:
        result = sanitize_metadata({"key": "val\x00ue"})
        assert result == {"key": "value"}

    def test_numeric_values_pass_through(self) -> None:
        result = sanitize_metadata({"count": 42, "ratio": 3.14, "flag": True})
        assert result == {"count": 42, "ratio": 3.14, "flag": True}

    def test_none_values_pass_through(self) -> None:
        result = sanitize_metadata({"key": None})
        assert result == {"key": None}

    def test_nested_dict_cleaned(self) -> None:
        result = sanitize_metadata({"a": {"b": "val\x00ue"}})
        assert result == {"a": {"b": "value"}}

    def test_max_depth_enforced(self) -> None:
        deep = {"a": {"b": {"c": {"d": "too deep"}}}}
        result = sanitize_metadata(deep, max_depth=3)
        # Depth 0 -> a, depth 1 -> b, depth 2 -> c, depth 3 -> dropped
        assert result == {"a": {"b": {"c": {}}}}

    def test_list_values_cleaned(self) -> None:
        result = sanitize_metadata({"items": ["hello\x00", "world"]})
        assert result == {"items": ["hello", "world"]}

    def test_list_capped_at_100(self) -> None:
        result = sanitize_metadata({"items": list(range(200))})
        assert len(result["items"]) == 100

    def test_non_string_keys_dropped(self) -> None:
        result = sanitize_metadata({123: "val", "ok": "yes"})  # type: ignore[dict-item]
        assert result == {"ok": "yes"}

    def test_empty_key_after_cleaning_dropped(self) -> None:
        result = sanitize_metadata({"\x00": "val", "ok": "yes"})
        assert result == {"ok": "yes"}

    def test_string_values_truncated(self) -> None:
        result = sanitize_metadata({"key": "a" * 20_000})
        assert len(result["key"]) == 10_000

    def test_empty_dict(self) -> None:
        assert sanitize_metadata({}) == {}
