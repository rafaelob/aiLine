"""International sign language registry.

Provides metadata, grammar rules, and resources for 8 sign languages:
ASL (American), BSL (British), LGP (Portuguese), DGS (German),
LSF (French), LSE (Spanish), Libras (Brazilian), ISL (Irish).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class SignLanguageCode(StrEnum):
    """ISO-like codes for supported sign languages."""

    ASL = "asl"  # American Sign Language
    BSL = "bsl"  # British Sign Language
    LGP = "lgp"  # Lingua Gestual Portuguesa
    DGS = "dgs"  # Deutsche Gebardensprache
    LSF = "lsf"  # Langue des Signes Francaise
    LSE = "lse"  # Lengua de Signos Espanola
    LIBRAS = "libras"  # Lingua Brasileira de Sinais
    ISL = "isl"  # Irish Sign Language


class SignLanguageInfo(BaseModel):
    """Metadata for a sign language."""

    code: SignLanguageCode
    name: str
    name_native: str
    country: str
    countries: list[str] = Field(default_factory=list)
    iso_639_3: str = ""
    spoken_language: str  # The corresponding spoken language
    writing_system: str = ""  # SignWriting, HamNoSys, etc.
    avatar_service: str = ""  # VLibras, HandTalk, etc.
    avatar_url: str = ""
    grammar_notes: str = ""
    word_order: str = ""  # SOV, OSV, Topic-Comment, etc.
    estimated_users: str = ""
    resources_url: str = ""


# -- Registry of all supported sign languages --------------------------------

SIGN_LANGUAGES: dict[SignLanguageCode, SignLanguageInfo] = {
    SignLanguageCode.ASL: SignLanguageInfo(
        code=SignLanguageCode.ASL,
        name="American Sign Language",
        name_native="American Sign Language",
        country="United States",
        countries=["US", "CA"],
        iso_639_3="ase",
        spoken_language="en",
        writing_system="SignWriting, ASL Gloss",
        grammar_notes=(
            "Topic-Comment structure, non-manual markers, classifiers, "
            "ASL-specific facial grammar"
        ),
        word_order="OSV / Topic-Comment",
        estimated_users="500,000 - 2,000,000",
        resources_url="https://www.handspeak.com/",
    ),
    SignLanguageCode.BSL: SignLanguageInfo(
        code=SignLanguageCode.BSL,
        name="British Sign Language",
        name_native="British Sign Language",
        country="United Kingdom",
        countries=["GB"],
        iso_639_3="bfi",
        spoken_language="en",
        writing_system="SignWriting",
        grammar_notes=(
            "Topic-Comment structure, two-handed alphabet (differs from ASL "
            "one-handed), BSL-specific non-manual features"
        ),
        word_order="Topic-Comment / SOV",
        estimated_users="150,000+",
        resources_url="https://www.british-sign.co.uk/",
    ),
    SignLanguageCode.LGP: SignLanguageInfo(
        code=SignLanguageCode.LGP,
        name="Portuguese Sign Language",
        name_native="Lingua Gestual Portuguesa",
        country="Portugal",
        countries=["PT"],
        iso_639_3="psr",
        spoken_language="pt",
        grammar_notes=(
            "Topic-Comment structure, influenced by LSF (French), two-handed "
            "alphabet, rich use of classifiers and spatial grammar"
        ),
        word_order="SOV / Topic-Comment",
        estimated_users="60,000+",
        resources_url="https://www.fpas.org.pt/",
    ),
    SignLanguageCode.DGS: SignLanguageInfo(
        code=SignLanguageCode.DGS,
        name="German Sign Language",
        name_native="Deutsche Gebardensprache",
        country="Germany",
        countries=["DE"],
        iso_639_3="gsg",
        spoken_language="de",
        writing_system="HamNoSys, SignWriting",
        grammar_notes=(
            "SOV word order, mouthing patterns from spoken German, productive "
            "use of classifier predicates and mouth actions"
        ),
        word_order="SOV",
        estimated_users="200,000+",
        resources_url="https://www.dgs-korpus.de/",
    ),
    SignLanguageCode.LSF: SignLanguageInfo(
        code=SignLanguageCode.LSF,
        name="French Sign Language",
        name_native="Langue des Signes Francaise",
        country="France",
        countries=["FR"],
        iso_639_3="fsl",
        spoken_language="fr",
        writing_system="SignWriting",
        grammar_notes=(
            "Historical parent of many sign languages (ASL, LSE, LGP). "
            "Rich facial grammar, spatial reference, iconic signs"
        ),
        word_order="SOV / Topic-Comment",
        estimated_users="100,000+",
        resources_url="https://www.lsf.fr/",
    ),
    SignLanguageCode.LSE: SignLanguageInfo(
        code=SignLanguageCode.LSE,
        name="Spanish Sign Language",
        name_native="Lengua de Signos Espanola",
        country="Spain",
        countries=["ES"],
        iso_639_3="ssp",
        spoken_language="es",
        writing_system="SignWriting",
        grammar_notes=(
            "Influenced by LSF (French), SOV word order, strong use of "
            "mouthing, spatial grammar, and role-shifting"
        ),
        word_order="SOV",
        estimated_users="100,000+",
        resources_url="https://www.cnse.es/",
    ),
    SignLanguageCode.LIBRAS: SignLanguageInfo(
        code=SignLanguageCode.LIBRAS,
        name="Brazilian Sign Language",
        name_native="Lingua Brasileira de Sinais",
        country="Brazil",
        countries=["BR"],
        iso_639_3="bzs",
        spoken_language="pt-BR",
        writing_system="SignWriting, ELiS",
        avatar_service="VLibras",
        avatar_url="https://vlibras.gov.br/",
        grammar_notes=(
            "Influenced by LSF (French), Topic-Comment structure, "
            "5 parameters (handshape, location, movement, orientation, "
            "non-manual), classifiers for description"
        ),
        word_order="Topic-Comment / SOV",
        estimated_users="5,000,000+",
        resources_url="https://www.libras.com.br/",
    ),
    SignLanguageCode.ISL: SignLanguageInfo(
        code=SignLanguageCode.ISL,
        name="Irish Sign Language",
        name_native="Teanga Chomharthaiochta na hEireann",
        country="Ireland",
        countries=["IE"],
        iso_639_3="isg",
        spoken_language="en",
        writing_system="SignWriting",
        grammar_notes=(
            "Influenced by LSF (French) via Catholic educational institutions. "
            "Distinct from BSL despite geographic proximity. Strong use of "
            "fingerspelling for Irish names"
        ),
        word_order="SOV / Topic-Comment",
        estimated_users="5,000+",
        resources_url="https://www.irishdeafsociety.ie/",
    ),
}


# -- Common basic gestures per sign language ----------------------------------

COMMON_GESTURES: dict[SignLanguageCode, list[dict[str, str]]] = {
    SignLanguageCode.ASL: [
        {"id": "hello", "name": "Hello", "gloss": "HELLO"},
        {"id": "thank_you", "name": "Thank You", "gloss": "THANK-YOU"},
        {"id": "yes", "name": "Yes", "gloss": "YES"},
        {"id": "no", "name": "No", "gloss": "NO"},
        {"id": "please", "name": "Please", "gloss": "PLEASE"},
        {"id": "sorry", "name": "Sorry", "gloss": "SORRY"},
        {"id": "help", "name": "Help", "gloss": "HELP"},
        {"id": "understand", "name": "I understand", "gloss": "UNDERSTAND"},
    ],
    SignLanguageCode.BSL: [
        {"id": "hello", "name": "Hello", "gloss": "HELLO"},
        {"id": "thank_you", "name": "Thank You", "gloss": "THANK-YOU"},
        {"id": "yes", "name": "Yes", "gloss": "YES"},
        {"id": "no", "name": "No", "gloss": "NO"},
        {"id": "please", "name": "Please", "gloss": "PLEASE"},
        {"id": "sorry", "name": "Sorry", "gloss": "SORRY"},
        {"id": "help", "name": "Help", "gloss": "HELP"},
        {"id": "understand", "name": "I understand", "gloss": "UNDERSTAND"},
    ],
    SignLanguageCode.LGP: [
        {"id": "ola", "name": "Ola", "gloss": "OLA"},
        {"id": "obrigado", "name": "Obrigado/a", "gloss": "OBRIGADO"},
        {"id": "sim", "name": "Sim", "gloss": "SIM"},
        {"id": "nao", "name": "Nao", "gloss": "NAO"},
        {"id": "por_favor", "name": "Por Favor", "gloss": "POR-FAVOR"},
        {"id": "desculpe", "name": "Desculpe", "gloss": "DESCULPE"},
        {"id": "ajuda", "name": "Ajuda", "gloss": "AJUDA"},
        {"id": "compreendo", "name": "Compreendo", "gloss": "COMPREENDO"},
    ],
    SignLanguageCode.DGS: [
        {"id": "hallo", "name": "Hallo", "gloss": "HALLO"},
        {"id": "danke", "name": "Danke", "gloss": "DANKE"},
        {"id": "ja", "name": "Ja", "gloss": "JA"},
        {"id": "nein", "name": "Nein", "gloss": "NEIN"},
        {"id": "bitte", "name": "Bitte", "gloss": "BITTE"},
        {"id": "entschuldigung", "name": "Entschuldigung", "gloss": "ENTSCHULDIGUNG"},
        {"id": "hilfe", "name": "Hilfe", "gloss": "HILFE"},
        {"id": "verstehen", "name": "Ich verstehe", "gloss": "VERSTEHEN"},
    ],
    SignLanguageCode.LSF: [
        {"id": "bonjour", "name": "Bonjour", "gloss": "BONJOUR"},
        {"id": "merci", "name": "Merci", "gloss": "MERCI"},
        {"id": "oui", "name": "Oui", "gloss": "OUI"},
        {"id": "non", "name": "Non", "gloss": "NON"},
        {"id": "svp", "name": "S'il vous plait", "gloss": "S-V-P"},
        {"id": "pardon", "name": "Pardon", "gloss": "PARDON"},
        {"id": "aide", "name": "Aide", "gloss": "AIDE"},
        {"id": "comprendre", "name": "Je comprends", "gloss": "COMPRENDRE"},
    ],
    SignLanguageCode.LSE: [
        {"id": "hola", "name": "Hola", "gloss": "HOLA"},
        {"id": "gracias", "name": "Gracias", "gloss": "GRACIAS"},
        {"id": "si", "name": "Si", "gloss": "SI"},
        {"id": "no", "name": "No", "gloss": "NO"},
        {"id": "por_favor", "name": "Por Favor", "gloss": "POR-FAVOR"},
        {"id": "perdon", "name": "Perdon", "gloss": "PERDON"},
        {"id": "ayuda", "name": "Ayuda", "gloss": "AYUDA"},
        {"id": "entiendo", "name": "Entiendo", "gloss": "ENTIENDO"},
    ],
    SignLanguageCode.LIBRAS: [
        {"id": "oi", "name": "Oi / Ola", "gloss": "OI"},
        {"id": "obrigado", "name": "Obrigado/a", "gloss": "OBRIGADO"},
        {"id": "sim", "name": "Sim", "gloss": "SIM"},
        {"id": "nao", "name": "Nao", "gloss": "NAO"},
        {"id": "por_favor", "name": "Por Favor", "gloss": "POR-FAVOR"},
        {"id": "desculpa", "name": "Desculpa", "gloss": "DESCULPA"},
        {"id": "ajuda", "name": "Ajuda", "gloss": "AJUDA"},
        {"id": "entender", "name": "Entender", "gloss": "ENTENDER"},
    ],
    SignLanguageCode.ISL: [
        {"id": "hello", "name": "Hello", "gloss": "HELLO"},
        {"id": "thank_you", "name": "Thank You", "gloss": "THANK-YOU"},
        {"id": "yes", "name": "Yes", "gloss": "YES"},
        {"id": "no", "name": "No", "gloss": "NO"},
        {"id": "please", "name": "Please", "gloss": "PLEASE"},
        {"id": "sorry", "name": "Sorry", "gloss": "SORRY"},
        {"id": "help", "name": "Help", "gloss": "HELP"},
        {"id": "understand", "name": "I understand", "gloss": "UNDERSTAND"},
    ],
}


# -- Locale to sign language mapping ------------------------------------------

LOCALE_TO_SIGN_LANGUAGE: dict[str, SignLanguageCode] = {
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


def get_sign_language(code: str) -> SignLanguageInfo | None:
    """Get sign language info by code."""
    try:
        sl_code = SignLanguageCode(code.lower())
        return SIGN_LANGUAGES.get(sl_code)
    except ValueError:
        return None


def get_sign_language_for_locale(locale: str) -> SignLanguageInfo:
    """Get the default sign language for a locale.

    Normalizes underscores to hyphens (e.g., pt_BR -> pt-BR).
    Falls back to ASL if the locale is not recognized.
    """
    normalized = locale.replace("_", "-")
    code = LOCALE_TO_SIGN_LANGUAGE.get(normalized)
    if code is None:
        # Try base language (e.g., "en" from "en-US")
        base = normalized.split("-")[0]
        code = LOCALE_TO_SIGN_LANGUAGE.get(base, SignLanguageCode.ASL)
    return SIGN_LANGUAGES[code]


def list_all_sign_languages() -> list[SignLanguageInfo]:
    """List all supported sign languages."""
    return list(SIGN_LANGUAGES.values())
