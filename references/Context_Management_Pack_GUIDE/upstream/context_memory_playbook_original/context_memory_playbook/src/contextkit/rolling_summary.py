from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

from .types import Turn
from .token_count import TokenCounter


class LLMClient(Protocol):
    """Interface mínima para plugar um provedor real de LLM."""

    def complete(self, messages: list[dict], **kwargs) -> str: ...


ROLLING_SUMMARY_SCHEMA = """# ROLLING_SUMMARY

## Objetivo atual
- ...

## Fatos confirmados
- ...

## Decisões (com rationale)
- decisão: ...
  - rationale: ...
  - impacto: ...

## Restrições e preferências
- ...

## Trabalho feito (resumo)
- ...

## Próximos passos / backlog
- ...

## Perguntas em aberto
- ...

## Artefatos / handles
- handle: <...> — ...

## Candidatos a memória (precisam confirmação)
- ...
"""


def _first_line(text: str, max_chars: int = 220) -> str:
    t = (text or "").strip().replace("\n", " ")
    if not t:
        return ""
    if len(t) > max_chars:
        return t[: max_chars - 1] + "…"
    return t


@dataclass
class RollingSummaryManager:
    """Mantém e atualiza um rolling summary canônico."""

    token_counter: TokenCounter
    llm: Optional[LLMClient] = None

    def _turns_to_compact_log(self, turns: list[Turn], max_items: int = 30) -> str:
        """Fallback determinístico: registra um log compacto dos turns compactados."""
        lines: list[str] = []
        for t in turns[-max_items:]:
            u = _first_line(t.user.get("content", ""))
            a = _first_line((t.assistant or {}).get("content", ""))
            if u:
                lines.append(f"- USER: {u}")
            if a:
                lines.append(f"  - ASSISTANT: {a}")
        if len(turns) > max_items:
            lines.append(f"- (… {len(turns) - max_items} turns adicionais compactados …)")
        return "\n".join(lines).strip()

    def build_compaction_messages(self, existing_summary: str, turns: list[Turn]) -> list[dict]:
        compact_log = self._turns_to_compact_log(turns, max_items=40)

        system = {
            "role": "system",
            "content": (
                "Você é um módulo de compaction/sumarização para sessões longas.\n"
                "Tarefa: atualizar um ROLLING_SUMMARY canônico mantendo estado útil.\n\n"
                "Regras:\n"
                "- NÃO invente fatos. Se não tiver certeza, marque como 'incerto' ou coloque em 'Perguntas em aberto'.\n"
                "- Preserve decisões, restrições, preferências, artefatos/handles e próximos passos.\n"
                "- Mantenha o formato do schema fornecido (mesmos headings).\n"
                "- Seja o mais compacto possível sem perder sinal.\n"
            ),
        }
        user = {
            "role": "user",
            "content": (
                "Atualize o ROLLING_SUMMARY.\n\n"
                "### Schema (use exatamente este formato):\n"
                f"{ROLLING_SUMMARY_SCHEMA}\n\n"
                "### Existing rolling summary (pode estar vazio):\n"
                f"{existing_summary or '(empty)'}\n\n"
                "### Turns to compact (log compacto):\n"
                f"{compact_log}\n"
            ),
        }
        return [system, user]

    def _ensure_header(self, text: str) -> str:
        t = (text or "").strip()
        if not t:
            return "# ROLLING_SUMMARY\n"
        if not t.lstrip().startswith("# ROLLING_SUMMARY"):
            return "# ROLLING_SUMMARY\n\n" + t
        return t

    def compact(self, existing_summary: str, turns: list[Turn], max_tokens: int = 8_000) -> str:
        """Retorna um rolling summary atualizado e limitado por orçamento."""
        if not turns:
            return self._ensure_header(existing_summary)

        if self.llm is None:
            # Fallback determinístico: adiciona um log compactado ao summary.
            base = self._ensure_header(existing_summary)
            log = self._turns_to_compact_log(turns)
            updated = base + "\n\n## Compact log (fallback)\n" + log + "\n"
        else:
            messages = self.build_compaction_messages(existing_summary, turns)
            updated = self.llm.complete(messages, temperature=0.0)
            updated = self._ensure_header(updated)

        # Enforce max_tokens (pós-hoc).
        if self.token_counter.count_text(updated) <= max_tokens:
            return updated

        # Truncamento controlado: preserva o topo e corta o fim.
        char_budget = int(max_tokens * self.token_counter.chars_per_token)
        if len(updated) <= char_budget:
            return updated  # token counter pode ter superestimado
        # Preserve o começo (head) e um pouco do final (tail) para manter handles recentes.
        head = int(char_budget * 0.75)
        tail = char_budget - head
        return updated[:head] + "\n\n… (rolling summary truncado por budget) …\n\n" + updated[-tail:]
