"""Tests for Grade 1 BRF Braille translator.

Covers:
- Single letter/digit/punctuation translation
- Capital and number indicators
- Accented characters (PT-BR, ES)
- Word and sentence translation
- Line wrapping at configurable width
- Page formatting and pagination
- Page number headers
- Form feed separators
- Edge cases (empty input, long words, mixed content)
- Byte output (ASCII encoding)
- Custom config
"""

from __future__ import annotations

import pytest

from ailine_runtime.accessibility.braille_translator import (
    FORM_FEED,
    BrfConfig,
    BrfTranslator,
    text_to_brf,
    text_to_brf_bytes,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def translator() -> BrfTranslator:
    return BrfTranslator()


@pytest.fixture
def narrow_translator() -> BrfTranslator:
    """Translator with narrow lines for easier wrapping tests."""
    return BrfTranslator(BrfConfig(line_width=20, page_height=5))


# ---------------------------------------------------------------------------
# Basic character translation
# ---------------------------------------------------------------------------

class TestSingleCharacters:
    def test_lowercase_letter(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("a")
        assert result == "a"

    def test_uppercase_letter(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("A")
        assert result == ",a"  # capital indicator + letter

    def test_digit(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("1")
        assert result == "#a"  # number indicator + digit value (1=a)

    def test_digit_zero(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("0")
        assert result == "#j"  # 0=j

    def test_space(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille(" ")
        assert result == " "

    def test_period(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille(".")
        assert result == "4"

    def test_comma(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille(",")
        assert result == "1"

    def test_question_mark(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("?")
        assert result == "8"

    def test_exclamation(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("!")
        assert result == "6"


# ---------------------------------------------------------------------------
# Number sequences
# ---------------------------------------------------------------------------

class TestNumbers:
    def test_multi_digit_number(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("42")
        assert result == "#db"  # number indicator + 4=d + 2=b

    def test_number_followed_by_letter(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("3a")
        # Number indicator for 3, then letter 'a' (exits number mode)
        result = translator._text_to_braille("3a")
        assert result == "#ca"  # #(3=c) then a

    def test_number_space_number(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("5 9")
        assert result == "#e #i"  # each number group gets indicator

    def test_year(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("2026")
        assert result == "#bjbf"  # #(2=b)(0=j)(2=b)(6=f)


# ---------------------------------------------------------------------------
# Capital letters
# ---------------------------------------------------------------------------

class TestCapitals:
    def test_capitalized_word(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("Hello")
        assert result == ",hello"

    def test_all_caps_word(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("OK")
        assert result == ",o,k"  # each uppercase letter gets indicator

    def test_mixed_case(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("AiLine")
        assert result == ",ai,line"


# ---------------------------------------------------------------------------
# Accented characters (PT-BR, ES)
# ---------------------------------------------------------------------------

class TestAccentedCharacters:
    def test_cedilla(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("ç")
        assert result == "`c"

    def test_tilde_a(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("ã")
        assert result == "`a"

    def test_acute_e(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("é")
        assert result == "`e"

    def test_tilde_n_spanish(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("ñ")
        assert result == "`n"

    def test_umlaut_u(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("ü")
        assert result == "`u"

    def test_uppercase_accented(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("É")
        assert result == ",`e"  # capital indicator + accent + letter

    def test_portuguese_word(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("ação")
        assert result == "a`c`ao"

    def test_spanish_word(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("niño")
        assert result == "ni`no"


# ---------------------------------------------------------------------------
# Full sentences
# ---------------------------------------------------------------------------

class TestSentences:
    def test_simple_english(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("Hello, world!")
        assert result == ",hello1 world6"

    def test_portuguese_sentence(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("Olá")
        assert result == ",ol`a"

    def test_mixed_numbers_and_text(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("Step 1: Read")
        assert result == ",step #a5 ,read"


# ---------------------------------------------------------------------------
# Line wrapping
# ---------------------------------------------------------------------------

class TestLineWrapping:
    def test_wraps_at_space(self, narrow_translator: BrfTranslator) -> None:
        braille = narrow_translator._text_to_braille("hello world again today")
        lines = narrow_translator._wrap_lines(braille)
        for line in lines:
            assert len(line) <= 20

    def test_preserves_empty_lines(self, translator: BrfTranslator) -> None:
        braille = translator._text_to_braille("line one\n\nline three")
        lines = translator._wrap_lines(braille)
        assert "" in lines

    def test_hard_break_long_word(self, narrow_translator: BrfTranslator) -> None:
        # A word longer than line width forces a hard break
        braille = narrow_translator._text_to_braille("abcdefghijklmnopqrstuvwxyz")
        lines = narrow_translator._wrap_lines(braille)
        assert len(lines) >= 2
        assert len(lines[0]) <= 20


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

class TestPagination:
    def test_single_page(self, translator: BrfTranslator) -> None:
        result = translator.translate("Hello")
        assert FORM_FEED not in result

    def test_multi_page_has_form_feed(self) -> None:
        config = BrfConfig(line_width=40, page_height=3)
        t = BrfTranslator(config)
        text = "line\n" * 10
        result = t.translate(text)
        assert FORM_FEED in result

    def test_page_numbers_on_subsequent_pages(self) -> None:
        config = BrfConfig(line_width=40, page_height=3, page_numbers=True)
        t = BrfTranslator(config)
        text = "line\n" * 10
        result = t.translate(text)
        # Page 2 should have a number header containing #b (number indicator + 2=b)
        pages = result.split(FORM_FEED)
        assert len(pages) >= 2
        assert "#b" in pages[1]  # page number 2

    def test_no_page_numbers_when_disabled(self) -> None:
        config = BrfConfig(line_width=40, page_height=3, page_numbers=False)
        t = BrfTranslator(config)
        text = "line\n" * 10
        result = t.translate(text)
        pages = result.split(FORM_FEED)
        # Second page should not start with page number header
        if len(pages) >= 2:
            lines = pages[1].strip().split("\n")
            # First line should be content, not a right-aligned number
            assert not lines[0].strip().startswith("#")


# ---------------------------------------------------------------------------
# Output format
# ---------------------------------------------------------------------------

class TestOutputFormat:
    def test_line_endings_crlf(self, translator: BrfTranslator) -> None:
        result = translator.translate("hello")
        assert "\r\n" in result

    def test_line_endings_lf(self) -> None:
        config = BrfConfig(line_ending="\n")
        t = BrfTranslator(config)
        result = t.translate("hello")
        assert "\r\n" not in result
        assert "\n" in result

    def test_bytes_output_is_ascii(self, translator: BrfTranslator) -> None:
        result = translator.translate_to_bytes("Hello, World!")
        assert isinstance(result, bytes)
        # All bytes should be ASCII (0-127)
        for byte in result:
            assert byte < 128

    def test_bytes_output_from_accented_text(self, translator: BrfTranslator) -> None:
        result = translator.translate_to_bytes("São Paulo")
        assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

class TestConvenienceFunctions:
    def test_text_to_brf(self) -> None:
        result = text_to_brf("hello")
        assert isinstance(result, str)
        assert "hello" in result

    def test_text_to_brf_with_config(self) -> None:
        config = BrfConfig(line_width=10)
        result = text_to_brf("hello world", config=config)
        assert isinstance(result, str)

    def test_text_to_brf_bytes(self) -> None:
        result = text_to_brf_bytes("hello")
        assert isinstance(result, bytes)

    def test_text_to_brf_bytes_with_config(self) -> None:
        config = BrfConfig(line_width=10)
        result = text_to_brf_bytes("hello world", config=config)
        assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_string(self, translator: BrfTranslator) -> None:
        result = translator.translate("")
        # Should produce at least one empty line
        assert result is not None

    def test_only_spaces(self, translator: BrfTranslator) -> None:
        result = translator.translate("   ")
        assert "   " in result

    def test_only_newlines(self, translator: BrfTranslator) -> None:
        result = translator.translate("\n\n\n")
        assert result is not None

    def test_unknown_character_replaced(self, translator: BrfTranslator) -> None:
        # Chinese character should be replaced with question mark
        result = translator._text_to_braille("\u4e16")
        assert result == "8"  # question mark indicator

    def test_tab_replaced_with_spaces(self, translator: BrfTranslator) -> None:
        result = translator._text_to_braille("\t")
        assert result == "  "

    def test_very_long_text(self) -> None:
        text = "hello world " * 500
        result = text_to_brf(text)
        assert FORM_FEED in result  # should span multiple pages
        assert len(result) > 0


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

class TestBrfConfig:
    def test_default_config(self) -> None:
        config = BrfConfig()
        assert config.line_width == 40
        assert config.page_height == 25
        assert config.page_numbers is True
        assert config.line_ending == "\r\n"

    def test_custom_config(self) -> None:
        config = BrfConfig(line_width=32, page_height=20, page_numbers=False, line_ending="\n")
        t = BrfTranslator(config)
        result = t.translate("hello")
        assert "\r\n" not in result

    def test_frozen_config(self) -> None:
        config = BrfConfig()
        with pytest.raises(AttributeError):
            config.line_width = 10  # type: ignore[misc]
