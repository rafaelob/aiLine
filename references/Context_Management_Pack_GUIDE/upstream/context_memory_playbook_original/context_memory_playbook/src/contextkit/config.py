from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Budgets:
    """Centraliza os orçamentos do modelo X/Y.

    Definições:
      - X_core_tokens: teto para o *core* (system/dev + regras duráveis + skills ativas + rolling summary + âncoras + estado).
      - Y_total_tokens: teto para o *turno inteiro* (input total).
      - (Y − X): reserva para tools/MCP/RAG/memória recuperada/result summaries.

    Notas:
      - Separe uma reserva de output (`output_reserve_tokens`) fora de Y se você controla max_output_tokens.
      - Em produção, ajuste X e Y com telemetria (token ledger).
    """
    X_core_tokens: int = 48_000
    Y_total_tokens: int = 120_000

    # Reserva para a resposta do modelo (não conta como input).
    output_reserve_tokens: int = 4_000

    # Margem para overhead/variações do tokenizer.
    safety_margin_tokens: int = 2_000

    # Modo estrito: (quase nunca necessário) — exigir core == X (padding conceitual).
    strict_core_equals_X: bool = False

    def min_tool_budget_tokens(self) -> int:
        return max(self.Y_total_tokens - self.X_core_tokens, 0)


@dataclass(frozen=True)
class HistoryPolicy:
    """Controla como manter/compactar histórico."""
    anchor_turns: int = 6                    # manter os últimos N turns intactos
    min_turns_to_compact: int = 2            # evita compactar agressivamente
    rolling_summary_max_tokens: int = 8_000  # teto do rolling summary dentro do core


@dataclass(frozen=True)
class SkillsPolicy:
    """Progressive disclosure para skills."""
    skills_index_budget_tokens: int = 4_000   # catálogo (name+description)
    max_active_skill_tokens: int = 20_000     # SKILL.md completo (ou seções)
    allow_skill_chunking: bool = True


@dataclass(frozen=True)
class ToolsPolicy:
    """Catálogo/schema/result de tools."""
    tool_catalog_budget_tokens: int = 8_000     # name+desc+assinatura curta
    max_inline_tool_result_chars: int = 50_000  # fallback por chars quando não há tokenizer
    max_inline_tool_result_tokens: int = 6_000  # preferível: cap por tokens
    max_inline_tool_schema_tokens: int = 6_000  # schema on-demand deve caber aqui

    # Reserva dentro do tool budget para “pós-tool” (evita estourar ao inserir resultados).
    reserve_tool_result_tokens: int = 8_000


@dataclass(frozen=True)
class RAGPolicy:
    """Compressão de evidências (RAG/web)."""
    top_k: int = 6
    max_quote_chars: int = 700
    total_quote_budget_tokens: int = 6_000
    include_coverage_gaps: bool = True


@dataclass
class Storage:
    """Paths para persistência (artefatos, DB de memória, caches)."""
    base_dir: Path = field(default_factory=lambda: Path(".contextkit"))
    artifacts_dir: Path = field(init=False)
    memory_db_path: Path = field(init=False)

    def __post_init__(self) -> None:
        self.artifacts_dir = self.base_dir / "artifacts"
        self.memory_db_path = self.base_dir / "memory.db"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class Config:
    """Config unificada (evite limites hardcoded espalhados)."""
    budgets: Budgets = field(default_factory=Budgets)
    history: HistoryPolicy = field(default_factory=HistoryPolicy)
    skills: SkillsPolicy = field(default_factory=SkillsPolicy)
    tools: ToolsPolicy = field(default_factory=ToolsPolicy)
    rag: RAGPolicy = field(default_factory=RAGPolicy)
    storage: Storage = field(default_factory=Storage)

    # Hint opcional para tokenizer/modelo (para TokenCounter plugável).
    tokenizer_model: Optional[str] = None
