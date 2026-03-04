from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

from ..token_count import TokenCounter


@dataclass(frozen=True)
class EvidenceItem:
    source_id: str
    title: str
    url: str
    date: Optional[str]
    relevance: float
    quote: str
    notes: str = ""


@dataclass
class EvidencePack:
    query: str
    items: list[EvidenceItem] = field(default_factory=list)
    coverage_gaps: list[str] = field(default_factory=list)

    def compress(self, token_counter: TokenCounter, max_quote_chars: int, total_quote_budget_tokens: int, top_k: int) -> "EvidencePack":
        """Reduce size by trimming quotes and limiting items."""
        new_items: list[EvidenceItem] = []
        quote_budget_chars = int(total_quote_budget_tokens * token_counter.chars_per_token)

        used = 0
        for item in sorted(self.items, key=lambda x: x.relevance, reverse=True)[:top_k]:
            q = item.quote.strip()
            if len(q) > max_quote_chars:
                q = q[:max_quote_chars] + "…"
            if used + len(q) > quote_budget_chars:
                break
            used += len(q)
            new_items.append(EvidenceItem(**{**item.__dict__, "quote": q}))

        return EvidencePack(query=self.query, items=new_items, coverage_gaps=self.coverage_gaps)

    def to_context_snippet(self) -> str:
        lines: list[str] = [f"## EVIDENCE_PACK", f"- query: {self.query}", ""]
        for i, it in enumerate(self.items, 1):
            lines.append(f"### Evidence {i}")
            lines.append(f"- title: {it.title}")
            lines.append(f"- url: {it.url}")
            if it.date:
                lines.append(f"- date: {it.date}")
            lines.append(f"- relevance: {it.relevance:.2f}")
            lines.append(f"- quote: {it.quote}")
            if it.notes:
                lines.append(f"- notes: {it.notes}")
            lines.append("")
        if self.coverage_gaps:
            lines.append("### Coverage gaps")
            for g in self.coverage_gaps:
                lines.append(f"- {g}")
        return "\n".join(lines).strip()
