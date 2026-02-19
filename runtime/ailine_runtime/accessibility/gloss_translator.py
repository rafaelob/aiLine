"""Gloss-to-text translator for sign language captioning.

Translates a sequence of sign language glosses (e.g., ["EU", "GOSTAR", "ESCOLA"])
into fluent text in the corresponding spoken language using an LLM via the ChatLLM port.
Includes caching for common phrase patterns.

Supports international sign languages via the sign_language parameter.
Default: Libras (Brazilian Sign Language) for backward compatibility.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any

import structlog

from ..domain.ports.llm import ChatLLM
from .sign_language_registry import SignLanguageCode

logger = structlog.get_logger(__name__)

# -- System prompts per sign language -----------------------------------------

_SYSTEM_PROMPTS: dict[SignLanguageCode, str] = {
    SignLanguageCode.LIBRAS: """\
Voce e um interprete profissional de Libras (Lingua Brasileira de Sinais).
Sua tarefa e traduzir sequencias de glossas de Libras para portugues fluente e natural.

Regras:
- Glossas vem em CAIXA ALTA separadas por espaco (ex.: EU GOSTAR ESCOLA).
- Traduza para portugues gramaticalmente correto e natural.
- Mantenha o significado original, sem adicionar informacao.
- Se a sequencia for ambigua, escolha a interpretacao mais comum no contexto educacional.
- Responda APENAS com a traducao, sem explicacoes.

Exemplos:
- EU GOSTAR ESCOLA -> Eu gosto da escola.
- PROFESSOR ENSINAR BOM -> O professor ensina bem.
- VOCE ENTENDER SIM -> Voce entendeu, sim.
- OI TUDO-BEM -> Oi, tudo bem?
- EU PRECISAR AJUDA -> Eu preciso de ajuda.
- OBRIGADO POR-FAVOR -> Obrigado, por favor.
- HOJE EU ESTUDAR CASA -> Hoje eu vou estudar em casa.
- AMANHA ESCOLA NAO -> Amanha nao tem escola.\
""",
    SignLanguageCode.ASL: """\
You are a professional ASL (American Sign Language) interpreter.
Your task is to translate sequences of ASL glosses into fluent, natural English.

Rules:
- Glosses are in UPPERCASE separated by spaces (e.g., I LIKE SCHOOL).
- ASL uses Topic-Comment / OSV word order. Reorder to natural English SVO.
- Translate into grammatically correct and natural English.
- Keep the original meaning without adding information.
- If the sequence is ambiguous, choose the most common interpretation in an educational context.
- Respond ONLY with the translation, no explanations.

Examples:
- I LIKE SCHOOL -> I like school.
- TEACHER TEACH GOOD -> The teacher teaches well.
- YOU UNDERSTAND YES -> Yes, you understood.
- HELLO HOW-YOU -> Hello, how are you?
- I NEED HELP -> I need help.
- THANK-YOU PLEASE -> Thank you, please.
- TODAY I STUDY HOME -> Today I will study at home.
- TOMORROW SCHOOL NO -> There is no school tomorrow.\
""",
    SignLanguageCode.BSL: """\
You are a professional BSL (British Sign Language) interpreter.
Your task is to translate sequences of BSL glosses into fluent, natural English.

Rules:
- Glosses are in UPPERCASE separated by spaces.
- BSL uses Topic-Comment / SOV word order. Reorder to natural English SVO.
- Translate into grammatically correct and natural British English.
- Keep the original meaning without adding information.
- If the sequence is ambiguous, choose the most common interpretation in an educational context.
- Respond ONLY with the translation, no explanations.

Examples:
- I SCHOOL LIKE -> I like school.
- TEACHER WELL TEACH -> The teacher teaches well.
- YOU UNDERSTAND YES -> Yes, you understood.
- HELLO HOW-YOU -> Hello, how are you?
- I HELP NEED -> I need help.\
""",
    SignLanguageCode.LGP: """\
Voce e um interprete profissional de LGP (Lingua Gestual Portuguesa).
Sua tarefa e traduzir sequencias de glossas de LGP para portugues europeu fluente e natural.

Regras:
- Glossas vem em CAIXA ALTA separadas por espaco.
- LGP usa ordem SOV / Topico-Comentario. Reordene para portugues europeu natural.
- Traduza para portugues gramaticalmente correto e natural (PT-PT).
- Mantenha o significado original, sem adicionar informacao.
- Se a sequencia for ambigua, escolha a interpretacao mais comum no contexto educacional.
- Responda APENAS com a traducao, sem explicacoes.

Exemplos:
- EU ESCOLA GOSTAR -> Eu gosto da escola.
- PROFESSOR BEM ENSINAR -> O professor ensina bem.
- TU COMPREENDER SIM -> Sim, tu compreendeste.
- OLA TUDO-BEM -> Ola, tudo bem?
- EU AJUDA PRECISAR -> Eu preciso de ajuda.\
""",
    SignLanguageCode.DGS: """\
Sie sind ein professioneller DGS-Dolmetscher (Deutsche Gebardensprache).
Ihre Aufgabe ist es, Sequenzen von DGS-Glossen in fliessendes, naturliches Deutsch zu uebersetzen.

Regeln:
- Glossen sind in GROSSBUCHSTABEN, getrennt durch Leerzeichen.
- DGS verwendet SOV-Wortstellung. Ordnen Sie zu natuerlichem Deutsch (SVO) um.
- Uebersetzen Sie in grammatikalisch korrektes und natuerliches Deutsch.
- Behalten Sie die urspruengliche Bedeutung bei, ohne Informationen hinzuzufuegen.
- Bei Mehrdeutigkeit waehlen Sie die haeufigste Interpretation im Bildungskontext.
- Antworten Sie NUR mit der Uebersetzung, ohne Erklaerungen.

Beispiele:
- ICH SCHULE MOEGEN -> Ich mag die Schule.
- LEHRER GUT UNTERRICHTEN -> Der Lehrer unterrichtet gut.
- DU VERSTEHEN JA -> Ja, du hast verstanden.
- HALLO WIE-GEHT -> Hallo, wie geht es dir?
- ICH HILFE BRAUCHEN -> Ich brauche Hilfe.\
""",
    SignLanguageCode.LSF: """\
Vous etes un interprete professionnel de LSF (Langue des Signes Francaise).
Votre tache est de traduire des sequences de gloses LSF en francais fluide et naturel.

Regles:
- Les gloses sont en MAJUSCULES separees par des espaces.
- La LSF utilise l'ordre SOV / Topique-Commentaire. Reordonnez en francais naturel (SVO).
- Traduisez en francais grammaticalement correct et naturel.
- Conservez le sens original sans ajouter d'information.
- Si la sequence est ambigue, choisissez l'interpretation la plus courante dans un contexte educatif.
- Repondez UNIQUEMENT avec la traduction, sans explications.

Exemples:
- MOI ECOLE AIMER -> J'aime l'ecole.
- PROFESSEUR BIEN ENSEIGNER -> Le professeur enseigne bien.
- TOI COMPRENDRE OUI -> Oui, tu as compris.
- BONJOUR CA-VA -> Bonjour, ca va ?
- MOI AIDE BESOIN -> J'ai besoin d'aide.\
""",
    SignLanguageCode.LSE: """\
Usted es un interprete profesional de LSE (Lengua de Signos Espanola).
Su tarea es traducir secuencias de glosas de LSE a espanol fluido y natural.

Reglas:
- Las glosas estan en MAYUSCULAS separadas por espacios.
- La LSE usa orden SOV. Reordene a espanol natural (SVO).
- Traduzca a espanol gramaticalmente correcto y natural.
- Mantenga el significado original sin agregar informacion.
- Si la secuencia es ambigua, elija la interpretacion mas comun en un contexto educativo.
- Responda SOLAMENTE con la traduccion, sin explicaciones.

Ejemplos:
- YO ESCUELA GUSTAR -> Me gusta la escuela.
- PROFESOR BIEN ENSENAR -> El profesor ensena bien.
- TU ENTENDER SI -> Si, entendiste.
- HOLA QUE-TAL -> Hola, que tal?
- YO AYUDA NECESITAR -> Necesito ayuda.\
""",
    SignLanguageCode.ISL: """\
You are a professional ISL (Irish Sign Language) interpreter.
Your task is to translate sequences of ISL glosses into fluent, natural English.

Rules:
- Glosses are in UPPERCASE separated by spaces.
- ISL uses SOV / Topic-Comment word order. Reorder to natural English SVO.
- Translate into grammatically correct and natural English.
- Keep the original meaning without adding information.
- If the sequence is ambiguous, choose the most common interpretation in an educational context.
- Respond ONLY with the translation, no explanations.

Examples:
- I SCHOOL LIKE -> I like school.
- TEACHER WELL TEACH -> The teacher teaches well.
- YOU UNDERSTAND YES -> Yes, you understood.
- HELLO HOW-YOU -> Hello, how are you?
- I HELP NEED -> I need help.\
""",
}


def _get_system_prompt(sign_language: SignLanguageCode) -> str:
    """Return the system prompt for a given sign language.

    Falls back to Libras if the sign language is not found.
    """
    return _SYSTEM_PROMPTS.get(sign_language, _SYSTEM_PROMPTS[SignLanguageCode.LIBRAS])


class GlossToTextTranslator:
    """Translates sign language glosses to fluent text via LLM.

    Maintains a simple LRU cache for recently translated gloss sequences
    to reduce LLM calls for repeated phrases.

    Supports multiple sign languages via the ``sign_language`` parameter.
    Default: Libras (backward compatible).
    """

    def __init__(
        self,
        llm: ChatLLM,
        cache_size: int = 128,
        sign_language: SignLanguageCode = SignLanguageCode.LIBRAS,
    ) -> None:
        self._llm = llm
        self._cache: OrderedDict[str, str] = OrderedDict()
        self._cache_size = cache_size
        self._sign_language = sign_language

    @property
    def sign_language(self) -> SignLanguageCode:
        """The sign language this translator is configured for."""
        return self._sign_language

    async def translate(
        self,
        glosses: list[str],
        sign_language: SignLanguageCode | None = None,
    ) -> str:
        """Translate a sequence of glosses to the corresponding spoken language.

        Args:
            glosses: List of uppercase glosses.
            sign_language: Override the default sign language for this call.

        Returns:
            Fluent translation in the corresponding spoken language.
        """
        if not glosses:
            return ""

        sl = sign_language or self._sign_language
        cache_key = f"{sl.value}:" + " ".join(glosses)

        # Check cache
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            logger.debug("gloss_translator.cache_hit", glosses=cache_key)
            return self._cache[cache_key]

        # Call LLM
        system_prompt = _get_system_prompt(sl)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": " ".join(glosses)},
        ]

        start = time.monotonic()
        translation = await self._llm.generate(
            messages,
            temperature=0.3,
            max_tokens=256,
        )
        elapsed = time.monotonic() - start

        translation = translation.strip()
        logger.info(
            "gloss_translator.translated",
            sign_language=sl.value,
            glosses=" ".join(glosses),
            translation=translation,
            elapsed_ms=round(elapsed * 1000),
        )

        # Update cache
        self._cache[cache_key] = translation
        if len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)

        return translation

    async def translate_streaming(
        self,
        glosses: list[str],
        sign_language: SignLanguageCode | None = None,
    ):
        """Translate glosses with streaming response.

        Yields translation chunks as they arrive from the LLM.
        """
        if not glosses:
            return

        sl = sign_language or self._sign_language
        cache_key = f"{sl.value}:" + " ".join(glosses)
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            yield self._cache[cache_key]
            return

        system_prompt = _get_system_prompt(sl)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": " ".join(glosses)},
        ]

        full_text = ""
        async for chunk in self._llm.stream(
            messages,
            temperature=0.3,
            max_tokens=256,
        ):
            full_text += chunk
            yield chunk

        full_text = full_text.strip()
        self._cache[cache_key] = full_text
        if len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)

    def clear_cache(self) -> None:
        """Clear the translation cache."""
        self._cache.clear()
