from __future__ import annotations

import sys
from pathlib import Path

# Allow running without installing the package:
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextkit.config import Config, Budgets, HistoryPolicy  # noqa: E402
from contextkit.orchestrator import Orchestrator  # noqa: E402


def main() -> None:
    # Budgets pequenos só para demonstrar compaction rapidamente.
    cfg = Config()
    cfg.budgets = Budgets(X_core_tokens=450, Y_total_tokens=700, strict_core_equals_X=False)

    # Âncoras moderadas; compaction vai acontecer quando o histórico crescer.
    cfg.history = HistoryPolicy(anchor_turns=2, min_turns_to_compact=2, rolling_summary_max_tokens=250)

    skills_dir = Path(__file__).parent / "skills"

    system = "Você é um agente que demonstra o modelo X/Y. Seja objetivo."
    developer = "Siga budgets. Não despeje outputs grandes inline."

    orch = Orchestrator(
        config=cfg,
        system_prompt=system,
        developer_prompt=developer,
        llm=None,              # fallback deterministic compaction
        skills_dir=skills_dir,
    )

    turns = [
        "Quero um guia completo de gerenciamento de contexto e memória.",
        "Inclua também skills e MCP servers; e um módulo de referência.",
        "Detalhe como funciona a sumarização incremental (rolling summary).",
        "Mostre como particionar X e Y e lidar com tool budget.",
        "Agora adicione um exemplo com web search e EvidencePack." + (" bla" * 120),
        "Inclua memória em grafo com proveniência e TTL." + (" foo" * 120),
    ]

    for i, txt in enumerate(turns, 1):
        active = ["mcp-tool-discovery"] if i == 2 else []

        # Exemplo de tool blocks (entram no orçamento Y−core):
        tool_blocks = []
        if i == 5:
            tool_blocks = [
                "## EVIDENCE_PACK\n- query: exemplo\n\n### Evidence 1\n- url: https://example.com\n- quote: \"Trecho curto...\"",
            ]
        if i == 6:
            tool_blocks = [
                "## GRAPH_MEMORY_SLICE\n### Entidades\n- Project:proj1 — Exemplo (conf=0.80, src=user)\n\n### Relações\n- proj1 -[USES]-> db1 (conf=0.70, src=user)",
            ]

        r = orch.run_turn(
            user_text=txt,
            durable_instructions="Use o modelo X/Y. Compaction quando core > X." if i == 1 else None,
            active_skill_names=active,
            tool_blocks=tool_blocks,
        )

        # Para o demo: simula uma resposta do assistente (aqui você chamaria o LLM de verdade).
        orch.state.history[-1].assistant = {"role": "assistant", "content": f"(demo) Resposta do turno {i}."}

        print(f"\nTURN {i}")
        print(
            "core_tokens:",
            r["core_tokens"],
            "tool_budget:",
            r["tool_budget_tokens"],
            "total_tokens:",
            r["total_tokens"],
            "compacted:",
            r["turns_compacted"],
        )

    orch.close()


if __name__ == "__main__":
    main()
