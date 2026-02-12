"""Gloss-to-text translator for Libras captioning.

Translates a sequence of Libras glosses (e.g., ["EU", "GOSTAR", "ESCOLA"])
into fluent Brazilian Portuguese using an LLM via the ChatLLM port.
Includes caching for common phrase patterns.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any

import structlog

from ..domain.ports.llm import ChatLLM

logger = structlog.get_logger(__name__)

_SYSTEM_PROMPT = """\
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
- AMANHA ESCOLA NAO -> Amanha nao tem escola.
"""


class GlossToTextTranslator:
    """Translates Libras glosses to fluent Portuguese via LLM.

    Maintains a simple LRU cache for recently translated gloss sequences
    to reduce LLM calls for repeated phrases.
    """

    def __init__(
        self,
        llm: ChatLLM,
        cache_size: int = 128,
    ) -> None:
        self._llm = llm
        self._cache: OrderedDict[str, str] = OrderedDict()
        self._cache_size = cache_size

    async def translate(self, glosses: list[str]) -> str:
        """Translate a sequence of glosses to Portuguese.

        Args:
            glosses: List of uppercase Libras glosses.

        Returns:
            Fluent Portuguese translation.
        """
        if not glosses:
            return ""

        cache_key = " ".join(glosses)

        # Check cache
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            logger.debug("gloss_translator.cache_hit", glosses=cache_key)
            return self._cache[cache_key]

        # Call LLM
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": cache_key},
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
            glosses=cache_key,
            translation=translation,
            elapsed_ms=round(elapsed * 1000),
        )

        # Update cache
        self._cache[cache_key] = translation
        if len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)

        return translation

    async def translate_streaming(self, glosses: list[str]):
        """Translate glosses with streaming response.

        Yields translation chunks as they arrive from the LLM.
        """
        if not glosses:
            return

        cache_key = " ".join(glosses)
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            yield self._cache[cache_key]
            return

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": cache_key},
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
