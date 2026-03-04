# Context Management Pack — Estado da Arte (SOTA) — 2026-02-24

Este ZIP (quando exportado) é um **kit completo e parametrizável** para engenharia de **Context Management** em sistemas de agentes com LLM, focado em:

- **Orçamento por tokens** (nada de “manter N turnos”)  
- **Montagem de contexto por camadas** (Context Stack)  
- **RAG com compressão + evidência/citações**  
- **Ferramentas (tool schemas + tool results) token-efficient**  
- **Memória (working vs durable) + compaction**  
- **Multi-agentes (manager/worker, handoffs, blackboard/event-log)**  
- **Observabilidade** (token ledger por camada, tracing, drift/quality gates)

> **Objetivo principal:** permitir que **cada orquestração** (workflow) selecione um **perfil de orçamento** e uma **política de montagem** adequada ao propósito (tool-heavy, RAG-heavy, low-latency, high-stakes, long-horizon, multi-agent, etc.), mantendo **flexibilidade** sem perder determinismo e auditabilidade.

---

## O que você vai encontrar aqui

### 1) Documentação (canônico)
- `docs/00_INDEX.md` — como navegar
- `docs/01_ESTADO_DA_ARTE.md` — o que é “SOTA” em 2026 e por quê
- `docs/02_TAXONOMIA_E_CONTEXT_STACK.md` — glossary + stack + diferenças por vendor
- `docs/03_ORCAMENTO_E_MATRIZ_DE_DECISAO.md` — matriz workload → estratégia
- `docs/03A_SESSOES_MULTI_VS_CONTINUA.md` — multi‑sessão vs sessão contínua + watermarks (steady/burst)
- `docs/04_PROFILES_DE_ORCAMENTO.md` — perfis de orçamento (inclui 350k/200k+150k) + knobs
- `docs/05_SYSTEM_PROMPT_E_SKILLS.md` — system prompt vs context engineering, skills, policies
- `docs/06_HISTORICO_POR_TOKENS.md` — histórico por limite de contexto + rolling/hierarchical summaries
- `docs/07_TOOLS_SCHEMAS_E_RESULTADOS.md` — tooling token-efficient + MCP + approvals
- `docs/08_RAG_EVIDENCE_PACK.md` — RAG, compressão, citações, checks de fé
- `docs/09_MEMORIA_E_COMPACCAO.md` — working vs durable, schemas, triggers, safe restart
- `docs/10_MULTI_AGENT.md` — manager vs descentralizado, handoff packages, shared state
- `docs/10A_DUAL_HANDOFF_TRANSFER_VS_DELEGATE.md` — **Transfer vs Delegate** (dual handoff), contratos e observabilidade
- `docs/11_OBSERVABILIDADE_E_GOVERNANCA.md` — métricas, tracing, logging seguro, segurança
- `docs/12_BLUEPRINT_IMPLEMENTACAO.md` — arquitetura + pipeline + pseudocódigo + exemplos
- `docs/13_ANTI_PADROES.md` — o que não fazer + correções
- `docs/14_ROTEIRO_30_60_90.md` — adoção, DoD, regressões e governança
- `docs/15_MAPA_DE_FONTES.md` — tabela com todas as fontes usadas (URL + data)

### 2) Templates e contratos
- `templates/` contém skeletons de prompts, schemas e contratos: handoff package, tool contract, evidence pack, prompts de sumário.

### 3) Configs (parametrização)
- `configs/` contém **perfis de orçamento** em YAML e um **JSON Schema** de validação.

### 4) Código (mínimo, integrável)
- `code/` contém um **context assembler** simples (framework‑agnostic) + exemplos de integração.

### 5) Upstream/Legado (para auditoria)
- `upstream/context_memory_playbook_original/` — o playbook original que você enviou (não editado)
- `upstream/internal_seed_sources/` — materiais internos fornecidos (seed) + versões anteriores do guia

---

## Quickstart (engenharia)

1. Leia `docs/01_ESTADO_DA_ARTE.md` e `docs/03_ORCAMENTO_E_MATRIZ_DE_DECISAO.md`
   - se você tem thread longa: leia também `docs/03A_SESSOES_MULTI_VS_CONTINUA.md`
2. Escolha um perfil em `configs/budget_profiles.yaml` (ex.: `tool_heavy_350k`)
3. Integre `code/context_manager.py` ao loop do seu agente/orquestrador:
   - antes do `model.call()`: `assemble_context(...)`
   - depois do `tool.call()`: `compact_tool_result(...)`
   - a cada N turnos ou em “phase boundaries”: `maybe_compact_history(...)`
4. Ative `ContextLedger` (token accounting por camada) e exporte métricas
5. Rode regressões mínimas (trajetórias) e ajuste budgets com telemetria

---

## Nota sobre “estado da arte”

SOTA aqui **não é** “guardar mais tokens”. É:
- **curar contexto** por camada (atenção/qualidade > volume),
- **externalizar artefatos**, rehidratar on-demand,
- usar **compaction** quando disponível,
- reduzir custo/latência via **caching**,
- e manter o sistema **observável** e **governável**.

---

## Licenças / atribuição

- O conteúdo em `upstream/context_memory_playbook_original/` mantém a licença original (MIT, conforme arquivo `LICENSE` no upstream).
- Este pack é uma recomposição e expansão técnica, com fontes oficiais listadas em `docs/15_MAPA_DE_FONTES.md`.

