# Context + Memory Playbook (X/Y) — Estado‑da‑arte (2026‑02‑24)

Este repositório é um **playbook + módulo de referência** (Python) para construir agentes com:

- **Gerenciamento de contexto com orçamento X/Y**
  - **X (core)**: system + developer + regras duráveis + skills ativas + resumo + pares de mensagens recentes + estado de orquestração.
  - **Y (total)**: teto total do turno.
  - **(Y − X)**: reserva para **tools**, **MCP**, **RAG/evidências**, **memória recuperada** e **resumos de resultados**.
- **Sumarização incremental (rolling summary)** e/ou **compaction server‑side** quando disponível.
- **Skills** (manifest `SKILL.md`, progressive disclosure).
- **MCP servers** (tools/resources/prompts), com filtragem de tools e políticas de aprovação.
- **Memória para personalização** (inclui **memória em grafo** com proveniência e TTL), com políticas de escrita.

> Objetivo: maximizar **controle**, **previsibilidade** e **qualidade** em sessões longas, evitando *prompt soup* e vazamento de orçamento para outputs de tools.

## Leitura rápida

1) `docs/00_GUIDE_COMPLETO.md` (visão geral + decisões de arquitetura)  
2) `docs/01_XY_budget_model.md` (modelo formal + heurísticas + pitfalls)  
3) `docs/03_skills_mcp_integration.md` (skills + MCP, incluindo OpenAI/Anthropic)  
4) `docs/04_memory_graph.md` (memória, governança e grafo)  
5) `docs/05_orchestration_reference.md` (loop do agente)  

## Rodando o exemplo

```bash
python examples/demo_minimal.py
```

> O demo usa budgets pequenos para forçar compaction rapidamente.

## Estrutura

- `docs/` — guia completo (em Markdown)
- `src/contextkit/` — módulo de referência (Python)
- `examples/` — exemplos mínimos
- `templates/` — templates (`AGENTS.md`, `CLAUDE.md`, `SKILL.md`, etc.)
- `references/` — materiais anexados + notas de auditoria

## Fontes oficiais

As fontes oficiais consultadas e as referências estão em:
- `docs/REFERENCIAS_OFICIAIS.md`

## Licença

MIT — ver `LICENSE`.
