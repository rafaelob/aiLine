from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass
class TokenCounter:
    """Contador de tokens (com fallback seguro).

    Em produção, prefira:
      - tokenizer real (ex.: tiktoken), ou
      - endpoint oficial de token counting do provedor.

    Este contador existe para *gating* de orçamento e testes locais.
    """
    chars_per_token: float = 4.0

    def count_text(self, text: str) -> int:
        if not text:
            return 0
        # Heurística conservadora: arredonda para cima.
        return int((len(text) / self.chars_per_token) + 0.9999)

    def count_messages(self, messages: list[dict]) -> int:
        # Overhead aproximado por mensagem/estrutura (depende do provedor).
        overhead_per_message = 10
        total = 0
        for m in messages:
            total += overhead_per_message
            total += self.count_text(str(m.get("role", "")))
            total += self.count_text(str(m.get("name", "")))
            total += self.count_text(str(m.get("content", "")))
        return total


class OptionalTiktokenCounter(TokenCounter):
    """Se `tiktoken` estiver instalado, usa; senão cai no fallback."""

    def __init__(self, model: Optional[str] = None, fallback_chars_per_token: float = 4.0) -> None:
        super().__init__(chars_per_token=fallback_chars_per_token)
        self._enc = None
        try:
            import tiktoken  # type: ignore

            if model:
                self._enc = tiktoken.encoding_for_model(model)
            else:
                # encoding amplo (pode mudar por modelo; é um default razoável)
                self._enc = tiktoken.get_encoding("o200k_base")
        except Exception:
            self._enc = None

    def count_text(self, text: str) -> int:
        if not text:
            return 0
        if self._enc is None:
            return super().count_text(text)
        return len(self._enc.encode(text))


class TokenCountingAPI(Protocol):
    """Interface mínima para um endpoint de contagem de tokens.

    Você pode implementar isto com o SDK do seu provedor.
    """

    def count(self, *, model: str, messages: list[dict], tools: Optional[list[dict]] = None) -> int: ...


class ProviderTokenCounter(TokenCounter):
    """TokenCounter que delega para um endpoint oficial (quando disponível).

    - Mantém o fallback heurístico para cenários offline.
    """

    def __init__(self, api: TokenCountingAPI, model: str, fallback_chars_per_token: float = 4.0) -> None:
        super().__init__(chars_per_token=fallback_chars_per_token)
        self.api = api
        self.model = model

    def count_messages(self, messages: list[dict]) -> int:
        try:
            return int(self.api.count(model=self.model, messages=messages))
        except Exception:
            return super().count_messages(messages)
