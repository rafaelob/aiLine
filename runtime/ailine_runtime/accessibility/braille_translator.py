"""Grade 1 (uncontracted) BRF Braille translator.

Converts plain text to BRF (Braille Ready Format) using the North American
Braille Computer Code (NABCC) mapping.  Supports EN, PT-BR, and ES character
sets including accented characters common in Portuguese and Spanish.

BRF format:
- ASCII chars 32-95 represent Braille cells
- 40 cells per line (standard Braille display width)
- 25 lines per page (standard embosser page)
- Form feed (0x0C) separates pages
- Capital indicator (,) precedes uppercase letters
- Number indicator (#) precedes digit sequences

Reference: BANA (Braille Authority of North America), NABCC standard.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# NABCC ASCII-Braille mapping (Grade 1)
# ---------------------------------------------------------------------------

# Lowercase letters -> Braille ASCII characters
_LETTER_MAP: dict[str, str] = {
    "a": "a", "b": "b", "c": "c", "d": "d", "e": "e",
    "f": "f", "g": "g", "h": "h", "i": "i", "j": "j",
    "k": "k", "l": "l", "m": "m", "n": "n", "o": "o",
    "p": "p", "q": "q", "r": "r", "s": "s", "t": "t",
    "u": "u", "v": "v", "w": "w", "x": "x", "y": "y",
    "z": "z",
}

# Digits -> Braille uses letter values with a number indicator prefix.
# In NABCC: 1=a, 2=b, 3=c, 4=d, 5=e, 6=f, 7=g, 8=h, 9=i, 0=j
_DIGIT_MAP: dict[str, str] = {
    "0": "j", "1": "a", "2": "b", "3": "c", "4": "d",
    "5": "e", "6": "f", "7": "g", "8": "h", "9": "i",
}

# Punctuation and symbols -> NABCC Braille ASCII
_PUNCT_MAP: dict[str, str] = {
    " ": " ",
    ".": "4",       # dots 2,5,6
    ",": "1",       # dots 2
    ";": "3",       # dots 2,3
    ":": "5",       # dots 2,5
    "!": "6",       # dots 2,3,5
    "?": "8",       # dots 2,3,6
    "'": "'",       # dots 3 (apostrophe)
    '"': "7",       # dots 2,3,5,6 (opening quote)
    "-": "-",       # dots 3,6 (hyphen)
    "(": "\"",      # dots 1,2,3,5,6
    ")": "\"",      # same Braille cell for close paren
    "/": "/",       # dots 3,4
    "@": "@",       # dots 4,7 (used in computer Braille)
    "&": "&",       # dots 1,2,3,4,6
    "*": "*",       # dots 1,6
    "+": "+",       # dots 3,4,6
    "=": "=",       # dots 1,2,3,4,5,6
    "%": "%",       # dots 1,4,6
    "$": "$",       # dots 1,2,4,6
    "#": "#",       # number indicator (dots 3,4,5,6)
    "\n": "\n",
    "\t": "  ",     # tab -> 2 spaces
}

# Accented characters (PT-BR, ES) -> decomposed to base letter.
# In Grade 1 Braille, accented chars use a prefix indicator + base letter.
# For BRF simplicity, we use dot-4 (`) as accent indicator.
_ACCENT_INDICATOR = "`"  # dots 3,4,5 — used as accent prefix in NABCC

_ACCENTED_MAP: dict[str, str] = {
    # Portuguese accents
    "á": f"{_ACCENT_INDICATOR}a",
    "à": f"{_ACCENT_INDICATOR}a",
    "â": f"{_ACCENT_INDICATOR}a",
    "ã": f"{_ACCENT_INDICATOR}a",
    "ä": f"{_ACCENT_INDICATOR}a",
    "é": f"{_ACCENT_INDICATOR}e",
    "è": f"{_ACCENT_INDICATOR}e",
    "ê": f"{_ACCENT_INDICATOR}e",
    "í": f"{_ACCENT_INDICATOR}i",
    "ì": f"{_ACCENT_INDICATOR}i",
    "î": f"{_ACCENT_INDICATOR}i",
    "ó": f"{_ACCENT_INDICATOR}o",
    "ò": f"{_ACCENT_INDICATOR}o",
    "ô": f"{_ACCENT_INDICATOR}o",
    "õ": f"{_ACCENT_INDICATOR}o",
    "ö": f"{_ACCENT_INDICATOR}o",
    "ú": f"{_ACCENT_INDICATOR}u",
    "ù": f"{_ACCENT_INDICATOR}u",
    "û": f"{_ACCENT_INDICATOR}u",
    "ü": f"{_ACCENT_INDICATOR}u",
    "ç": f"{_ACCENT_INDICATOR}c",
    # Spanish accents
    "ñ": f"{_ACCENT_INDICATOR}n",
    # Additional
    "ý": f"{_ACCENT_INDICATOR}y",
}

# Capital indicator in NABCC
_CAP_INDICATOR = ","
# Number indicator in NABCC
_NUM_INDICATOR = "#"

# Page format defaults
DEFAULT_LINE_WIDTH = 40
DEFAULT_PAGE_HEIGHT = 25
FORM_FEED = "\x0c"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BrfConfig:
    """Configuration for BRF output formatting."""

    line_width: int = DEFAULT_LINE_WIDTH
    page_height: int = DEFAULT_PAGE_HEIGHT
    page_numbers: bool = True
    line_ending: str = "\r\n"


# ---------------------------------------------------------------------------
# Core translator
# ---------------------------------------------------------------------------

@dataclass
class BrfTranslator:
    """Grade 1 (uncontracted) BRF Braille translator.

    Translates plain text to BRF format. Supports English, Portuguese (BR),
    and Spanish character sets with accented characters.
    """

    config: BrfConfig = field(default_factory=BrfConfig)

    # -- Public API ----------------------------------------------------------

    def translate(self, text: str) -> str:
        """Translate plain text to BRF format string.

        Args:
            text: Input plain text (any of EN, PT-BR, ES).

        Returns:
            BRF-formatted string with page breaks and line wrapping.
        """
        braille_chars = self._text_to_braille(text)
        lines = self._wrap_lines(braille_chars)
        pages = self._paginate(lines)
        return self._format_output(pages)

    def translate_to_bytes(self, text: str) -> bytes:
        """Translate plain text to BRF bytes (ASCII encoding).

        Returns:
            BRF content as ASCII-encoded bytes, suitable for .brf file.
        """
        return self.translate(text).encode("ascii", errors="replace")

    # -- Internal: char-level translation ------------------------------------

    def _text_to_braille(self, text: str) -> str:
        """Convert text to Braille ASCII characters with indicators."""
        result: list[str] = []
        in_number = False

        for char in text:
            lower = char.lower()

            # Newline: reset number mode, pass through
            if char == "\n":
                in_number = False
                result.append("\n")
                continue

            # Accented characters
            if lower in _ACCENTED_MAP:
                in_number = False
                if char != lower:  # uppercase accented
                    result.append(_CAP_INDICATOR)
                result.append(_ACCENTED_MAP[lower])
                continue

            # Digits
            if char.isdigit():
                if not in_number:
                    result.append(_NUM_INDICATOR)
                    in_number = True
                result.append(_DIGIT_MAP[char])
                continue

            # Letters
            if lower in _LETTER_MAP:
                if in_number:
                    in_number = False
                if char.isupper():
                    result.append(_CAP_INDICATOR)
                result.append(_LETTER_MAP[lower])
                continue

            # Punctuation and symbols
            if char in _PUNCT_MAP:
                in_number = False
                result.append(_PUNCT_MAP[char])
                continue

            # Unknown character: replace with question mark indicator
            in_number = False
            result.append("8")  # question mark in Braille

        return "".join(result)

    # -- Internal: line wrapping ---------------------------------------------

    def _wrap_lines(self, braille_text: str) -> list[str]:
        """Wrap Braille text into lines of configured width.

        Wraps at word boundaries (spaces) when possible.
        """
        raw_lines = braille_text.split("\n")
        wrapped: list[str] = []
        width = self.config.line_width

        for raw_line in raw_lines:
            if not raw_line:
                wrapped.append("")
                continue

            while len(raw_line) > width:
                # Find last space within line width
                break_pos = raw_line.rfind(" ", 0, width + 1)
                if break_pos <= 0:
                    # No space found: hard break at width
                    break_pos = width
                wrapped.append(raw_line[:break_pos].rstrip())
                raw_line = raw_line[break_pos:].lstrip()

            wrapped.append(raw_line)

        return wrapped

    # -- Internal: pagination ------------------------------------------------

    def _paginate(self, lines: list[str]) -> list[list[str]]:
        """Split lines into pages of configured height.

        If page numbering is enabled, the first line of each page
        (after page 1) is reserved for the page number header.
        """
        pages: list[list[str]] = []
        page_height = self.config.page_height
        idx = 0

        page_num = 1
        while idx < len(lines):
            if page_num == 1:  # noqa: SIM108
                # First page: full height
                usable = page_height
            else:
                # Subsequent pages: reserve first line for page number
                usable = page_height - 1 if self.config.page_numbers else page_height

            page_lines = lines[idx : idx + usable]
            pages.append(page_lines)
            idx += usable
            page_num += 1

        # Ensure at least one page
        if not pages:
            pages.append([""])

        return pages

    def _format_page_number(self, page_num: int) -> str:
        """Format a right-aligned page number header line."""
        num_str = self._translate_number(page_num)
        padding = self.config.line_width - len(num_str)
        return " " * max(padding, 0) + num_str

    def _translate_number(self, n: int) -> str:
        """Translate an integer to Braille number notation."""
        digits = str(n)
        result = _NUM_INDICATOR
        for d in digits:
            result += _DIGIT_MAP[d]
        return result

    # -- Internal: output formatting -----------------------------------------

    def _format_output(self, pages: list[list[str]]) -> str:
        """Assemble pages into final BRF string with form feeds."""
        le = self.config.line_ending
        parts: list[str] = []

        for page_idx, page_lines in enumerate(pages):
            page_num = page_idx + 1

            if page_num > 1:
                parts.append(FORM_FEED)
                if self.config.page_numbers:
                    parts.append(self._format_page_number(page_num))
                    parts.append(le)

            for line in page_lines:
                parts.append(line)
                parts.append(le)

        return "".join(parts)


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_DEFAULT_TRANSLATOR = BrfTranslator()


def text_to_brf(text: str, *, config: BrfConfig | None = None) -> str:
    """Translate plain text to BRF format string.

    Args:
        text: Input plain text.
        config: Optional BRF configuration. Uses defaults if None.

    Returns:
        BRF-formatted string.
    """
    if config is not None:
        return BrfTranslator(config).translate(text)
    return _DEFAULT_TRANSLATOR.translate(text)


def text_to_brf_bytes(text: str, *, config: BrfConfig | None = None) -> bytes:
    """Translate plain text to BRF bytes (ASCII encoding).

    Args:
        text: Input plain text.
        config: Optional BRF configuration. Uses defaults if None.

    Returns:
        BRF content as ASCII bytes.
    """
    if config is not None:
        return BrfTranslator(config).translate_to_bytes(text)
    return _DEFAULT_TRANSLATOR.translate_to_bytes(text)
