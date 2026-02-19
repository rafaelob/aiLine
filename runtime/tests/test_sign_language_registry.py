"""Tests for the international sign language registry.

Covers:
- SignLanguageCode enum: all 8 codes, StrEnum behavior
- SignLanguageInfo model: field types, required/optional fields
- SIGN_LANGUAGES registry: completeness (8 languages), metadata correctness
- COMMON_GESTURES: 8 gestures per language, required fields
- LOCALE_TO_SIGN_LANGUAGE mapping: locale-to-sign-language resolution
- get_sign_language(): lookup by code, case insensitivity, invalid code
- get_sign_language_for_locale(): exact match, base language fallback,
    underscore normalization, unknown locale fallback to ASL
- list_all_sign_languages(): returns all 8
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from ailine_runtime.accessibility.sign_language_registry import (
    COMMON_GESTURES,
    LOCALE_TO_SIGN_LANGUAGE,
    SIGN_LANGUAGES,
    SignLanguageCode,
    SignLanguageInfo,
    get_sign_language,
    get_sign_language_for_locale,
    list_all_sign_languages,
)

# ---------------------------------------------------------------------------
# SignLanguageCode enum
# ---------------------------------------------------------------------------


class TestSignLanguageCode:
    """Tests for the SignLanguageCode StrEnum."""

    ALL_CODES = ("asl", "bsl", "lgp", "dgs", "lsf", "lse", "libras", "isl")

    def test_enum_count(self) -> None:
        assert len(SignLanguageCode) == 8

    @pytest.mark.parametrize("code", ALL_CODES)
    def test_code_exists(self, code: str) -> None:
        sl = SignLanguageCode(code)
        assert sl.value == code

    def test_is_str_enum(self) -> None:
        """SignLanguageCode values should be usable as strings."""
        assert str(SignLanguageCode.ASL) == "asl"
        assert SignLanguageCode.LIBRAS == "libras"

    def test_invalid_code_raises(self) -> None:
        with pytest.raises(ValueError):
            SignLanguageCode("xyz")


# ---------------------------------------------------------------------------
# SignLanguageInfo model
# ---------------------------------------------------------------------------


class TestSignLanguageInfo:
    """Tests for the SignLanguageInfo Pydantic model."""

    def test_required_fields(self) -> None:
        info = SignLanguageInfo(
            code=SignLanguageCode.ASL,
            name="American Sign Language",
            name_native="American Sign Language",
            country="United States",
            spoken_language="en",
        )
        assert info.code == SignLanguageCode.ASL
        assert info.name == "American Sign Language"
        assert info.spoken_language == "en"

    def test_optional_defaults(self) -> None:
        info = SignLanguageInfo(
            code=SignLanguageCode.BSL,
            name="BSL",
            name_native="BSL",
            country="UK",
            spoken_language="en",
        )
        assert info.countries == []
        assert info.iso_639_3 == ""
        assert info.writing_system == ""
        assert info.avatar_service == ""
        assert info.avatar_url == ""
        assert info.grammar_notes == ""
        assert info.word_order == ""
        assert info.estimated_users == ""
        assert info.resources_url == ""


# ---------------------------------------------------------------------------
# SIGN_LANGUAGES registry -- completeness
# ---------------------------------------------------------------------------


class TestSignLanguagesRegistry:
    """Tests for the SIGN_LANGUAGES global dict."""

    def test_registry_has_eight_languages(self) -> None:
        assert len(SIGN_LANGUAGES) == 8

    def test_every_enum_member_present(self) -> None:
        for code in SignLanguageCode:
            assert code in SIGN_LANGUAGES, f"Missing entry for {code}"

    @pytest.mark.parametrize(
        ("code", "expected_name"),
        [
            (SignLanguageCode.ASL, "American Sign Language"),
            (SignLanguageCode.BSL, "British Sign Language"),
            (SignLanguageCode.LGP, "Portuguese Sign Language"),
            (SignLanguageCode.DGS, "German Sign Language"),
            (SignLanguageCode.LSF, "French Sign Language"),
            (SignLanguageCode.LSE, "Spanish Sign Language"),
            (SignLanguageCode.LIBRAS, "Brazilian Sign Language"),
            (SignLanguageCode.ISL, "Irish Sign Language"),
        ],
    )
    def test_language_name(self, code: SignLanguageCode, expected_name: str) -> None:
        assert SIGN_LANGUAGES[code].name == expected_name

    @pytest.mark.parametrize(
        ("code", "expected_spoken"),
        [
            (SignLanguageCode.ASL, "en"),
            (SignLanguageCode.BSL, "en"),
            (SignLanguageCode.LGP, "pt"),
            (SignLanguageCode.DGS, "de"),
            (SignLanguageCode.LSF, "fr"),
            (SignLanguageCode.LSE, "es"),
            (SignLanguageCode.LIBRAS, "pt-BR"),
            (SignLanguageCode.ISL, "en"),
        ],
    )
    def test_spoken_language(
        self, code: SignLanguageCode, expected_spoken: str
    ) -> None:
        assert SIGN_LANGUAGES[code].spoken_language == expected_spoken

    def test_all_languages_have_country(self) -> None:
        for code, info in SIGN_LANGUAGES.items():
            assert info.country, f"{code} missing country"

    def test_all_languages_have_iso_code(self) -> None:
        for code, info in SIGN_LANGUAGES.items():
            assert info.iso_639_3, f"{code} missing ISO 639-3 code"

    def test_libras_has_avatar_service(self) -> None:
        """Libras is the only language with a configured avatar (VLibras)."""
        libras = SIGN_LANGUAGES[SignLanguageCode.LIBRAS]
        assert libras.avatar_service == "VLibras"
        assert "vlibras.gov.br" in libras.avatar_url

    def test_all_have_grammar_notes(self) -> None:
        for code, info in SIGN_LANGUAGES.items():
            assert info.grammar_notes, f"{code} missing grammar_notes"

    def test_all_have_word_order(self) -> None:
        for code, info in SIGN_LANGUAGES.items():
            assert info.word_order, f"{code} missing word_order"


# ---------------------------------------------------------------------------
# COMMON_GESTURES
# ---------------------------------------------------------------------------


class TestCommonGestures:
    """Tests for the COMMON_GESTURES per-language gesture lists."""

    def test_all_languages_have_gestures(self) -> None:
        for code in SignLanguageCode:
            assert code in COMMON_GESTURES, f"Missing gestures for {code}"

    def test_each_language_has_eight_gestures(self) -> None:
        for code in SignLanguageCode:
            gestures = COMMON_GESTURES[code]
            assert (
                len(gestures) == 8
            ), f"{code} has {len(gestures)} gestures, expected 8"

    def test_gesture_required_fields(self) -> None:
        """Every gesture must have id, name, and gloss."""
        for code, gestures in COMMON_GESTURES.items():
            for i, g in enumerate(gestures):
                assert "id" in g, f"{code} gesture[{i}] missing 'id'"
                assert "name" in g, f"{code} gesture[{i}] missing 'name'"
                assert "gloss" in g, f"{code} gesture[{i}] missing 'gloss'"

    def test_gesture_ids_unique_per_language(self) -> None:
        for code, gestures in COMMON_GESTURES.items():
            ids = [g["id"] for g in gestures]
            assert len(ids) == len(set(ids)), f"Duplicate gesture IDs in {code}"

    def test_asl_gestures_in_english(self) -> None:
        asl_gestures = COMMON_GESTURES[SignLanguageCode.ASL]
        names = {g["name"] for g in asl_gestures}
        assert "Hello" in names
        assert "Thank You" in names
        assert "Yes" in names
        assert "No" in names

    def test_libras_gestures_in_portuguese(self) -> None:
        libras = COMMON_GESTURES[SignLanguageCode.LIBRAS]
        names = {g["name"] for g in libras}
        assert "Oi / Ola" in names
        assert "Obrigado/a" in names
        assert "Sim" in names
        assert "Nao" in names

    def test_dgs_gestures_in_german(self) -> None:
        dgs = COMMON_GESTURES[SignLanguageCode.DGS]
        names = {g["name"] for g in dgs}
        assert "Hallo" in names
        assert "Danke" in names

    def test_lsf_gestures_in_french(self) -> None:
        lsf = COMMON_GESTURES[SignLanguageCode.LSF]
        names = {g["name"] for g in lsf}
        assert "Bonjour" in names
        assert "Merci" in names

    def test_lse_gestures_in_spanish(self) -> None:
        lse = COMMON_GESTURES[SignLanguageCode.LSE]
        names = {g["name"] for g in lse}
        assert "Hola" in names
        assert "Gracias" in names

    def test_gloss_is_uppercase(self) -> None:
        """Sign language glosses are conventionally uppercase."""
        for code, gestures in COMMON_GESTURES.items():
            for g in gestures:
                gloss = g["gloss"]
                assert (
                    gloss == gloss.upper()
                ), f"{code} gesture '{g['id']}' gloss '{gloss}' is not uppercase"


# ---------------------------------------------------------------------------
# LOCALE_TO_SIGN_LANGUAGE mapping
# ---------------------------------------------------------------------------


class TestLocaleMapping:
    """Tests for the LOCALE_TO_SIGN_LANGUAGE mapping."""

    EXPECTED_MAPPINGS: ClassVar[dict[str, SignLanguageCode]] = {
        "en": SignLanguageCode.ASL,
        "en-US": SignLanguageCode.ASL,
        "en-GB": SignLanguageCode.BSL,
        "en-IE": SignLanguageCode.ISL,
        "pt": SignLanguageCode.LGP,
        "pt-PT": SignLanguageCode.LGP,
        "pt-BR": SignLanguageCode.LIBRAS,
        "de": SignLanguageCode.DGS,
        "de-DE": SignLanguageCode.DGS,
        "fr": SignLanguageCode.LSF,
        "fr-FR": SignLanguageCode.LSF,
        "es": SignLanguageCode.LSE,
        "es-ES": SignLanguageCode.LSE,
    }

    def test_mapping_count(self) -> None:
        assert len(LOCALE_TO_SIGN_LANGUAGE) == 13

    @pytest.mark.parametrize(
        ("locale", "expected_code"),
        list(EXPECTED_MAPPINGS.items()),
    )
    def test_locale_resolves_correctly(
        self, locale: str, expected_code: SignLanguageCode
    ) -> None:
        assert LOCALE_TO_SIGN_LANGUAGE[locale] == expected_code


# ---------------------------------------------------------------------------
# get_sign_language()
# ---------------------------------------------------------------------------


class TestGetSignLanguage:
    """Tests for get_sign_language() lookup function."""

    @pytest.mark.parametrize(
        "code", ["asl", "bsl", "lgp", "dgs", "lsf", "lse", "libras", "isl"]
    )
    def test_valid_code_returns_info(self, code: str) -> None:
        info = get_sign_language(code)
        assert info is not None
        assert info.code.value == code

    def test_case_insensitive(self) -> None:
        info_upper = get_sign_language("ASL")
        info_lower = get_sign_language("asl")
        assert info_upper is not None
        assert info_lower is not None
        assert info_upper.code == info_lower.code

    def test_mixed_case(self) -> None:
        info = get_sign_language("Libras")
        assert info is not None
        assert info.code == SignLanguageCode.LIBRAS

    def test_invalid_code_returns_none(self) -> None:
        assert get_sign_language("xyz") is None
        assert get_sign_language("") is None

    def test_unknown_but_format_ok_returns_none(self) -> None:
        assert get_sign_language("abc") is None


# ---------------------------------------------------------------------------
# get_sign_language_for_locale()
# ---------------------------------------------------------------------------


class TestGetSignLanguageForLocale:
    """Tests for get_sign_language_for_locale() with fallback logic."""

    def test_exact_locale_match(self) -> None:
        info = get_sign_language_for_locale("pt-BR")
        assert info.code == SignLanguageCode.LIBRAS

    def test_base_language_fallback(self) -> None:
        """en-AU is not mapped; should fall back to 'en' -> ASL."""
        info = get_sign_language_for_locale("en-AU")
        assert info.code == SignLanguageCode.ASL

    def test_underscore_normalization(self) -> None:
        """Underscores should be converted to hyphens (pt_BR -> pt-BR)."""
        info = get_sign_language_for_locale("pt_BR")
        assert info.code == SignLanguageCode.LIBRAS

    def test_underscore_normalization_german(self) -> None:
        info = get_sign_language_for_locale("de_DE")
        assert info.code == SignLanguageCode.DGS

    def test_unknown_locale_falls_back_to_asl(self) -> None:
        """Completely unknown locale should default to ASL."""
        info = get_sign_language_for_locale("zh-CN")
        assert info.code == SignLanguageCode.ASL

    def test_unknown_base_language_falls_back_to_asl(self) -> None:
        info = get_sign_language_for_locale("ja")
        assert info.code == SignLanguageCode.ASL

    @pytest.mark.parametrize(
        ("locale", "expected_code"),
        [
            ("en", SignLanguageCode.ASL),
            ("en-US", SignLanguageCode.ASL),
            ("en-GB", SignLanguageCode.BSL),
            ("en-IE", SignLanguageCode.ISL),
            ("pt", SignLanguageCode.LGP),
            ("pt-PT", SignLanguageCode.LGP),
            ("pt-BR", SignLanguageCode.LIBRAS),
            ("de", SignLanguageCode.DGS),
            ("fr", SignLanguageCode.LSF),
            ("es", SignLanguageCode.LSE),
        ],
    )
    def test_all_known_locales(
        self, locale: str, expected_code: SignLanguageCode
    ) -> None:
        info = get_sign_language_for_locale(locale)
        assert info.code == expected_code

    def test_returns_full_info_object(self) -> None:
        info = get_sign_language_for_locale("fr")
        assert isinstance(info, SignLanguageInfo)
        assert info.name == "French Sign Language"
        assert info.spoken_language == "fr"


# ---------------------------------------------------------------------------
# list_all_sign_languages()
# ---------------------------------------------------------------------------


class TestListAllSignLanguages:
    """Tests for list_all_sign_languages()."""

    def test_returns_eight_languages(self) -> None:
        languages = list_all_sign_languages()
        assert len(languages) == 8

    def test_returns_sign_language_info_objects(self) -> None:
        languages = list_all_sign_languages()
        for lang in languages:
            assert isinstance(lang, SignLanguageInfo)

    def test_all_codes_represented(self) -> None:
        languages = list_all_sign_languages()
        codes = {lang.code for lang in languages}
        expected_codes = set(SignLanguageCode)
        assert codes == expected_codes

    def test_returns_list_not_dict_values_view(self) -> None:
        languages = list_all_sign_languages()
        assert isinstance(languages, list)
