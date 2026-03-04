# 04 — Perfis de Orçamento (parametrizáveis) e knobs de realocação

## Objetivo

Você quer **flexibilidade**: cada orquestração pode ter propósito diferente, então o sistema precisa:
- selecionar um **perfil** (budget profile) por workflow/turno,
- montar a janela com **limite por tokens**,
- e registrar **observabilidade** (ledger + tracing) para ajustes.

Este documento define:
1) um **modelo de configuração** (budget vector),
2) uma biblioteca de **perfis** (inclui seu cenário 350k),
3) heurísticas para **realocação dinâmica**.

---

## Modelo recomendado: budgets como *ratio* + *min/max*

> O erro comum é usar só valores absolutos e depois “não caber” em modelos menores/maiores.

### Campos mínimos do profile
- `window_tokens`: tamanho da janela do modelo (capability/config)
- `reserve_output_tokens`
- `safety_margin_tokens`
- `utilization_target_ratio` *(opcional, recomendado em sessão contínua)*: fração do window usada para **budgets de input** (o restante vira headroom/buffer)
- `mode`: `ratio` ou `absolute`
- `slices`: dicionário de budgets por slice

Exemplo (ratio, simplificado):

```yaml
profile_name: tool_heavy_350k
window_tokens: 350000
reserve_output_tokens: 8000
safety_margin_tokens: 2000
utilization_target_ratio: 1.0
mode: ratio
slices:
  system_dev: { ratio: 0.05, min: 8000, max: 25000 }
  skills_index: { ratio: 0.01, min: 1000, max: 6000 }
  skills_active: { ratio: 0.08, min: 8000, max: 45000 }
  state_json: { ratio: 0.04, min: 4000, max: 20000 }
  history_recency: { ratio: 0.12, min: 12000, max: 60000 }
  history_summary: { ratio: 0.05, min: 6000, max: 30000 }
  tool_schemas: { ratio: 0.03, min: 3000, max: 20000 }
  tool_results: { ratio: 0.32, min: 30000, max: 160000 }
  rag_evidence: { ratio: 0.30, min: 20000, max: 160000 }
  orchestration_notes: { ratio: 0.00, min: 0, max: 8000 }

### Quando usar `utilization_target_ratio`

Esse knob é o jeito mais simples de implementar **watermarks**:

- `window_tokens` = janela/cap (o que o modelo suporta ou o que o orquestrador permite)
- `utilization_target_ratio` = quanto você quer ocupar **de forma sustentada**

Exemplo (sessão contínua):

```yaml
profile_name: continuous_tool_heavy_400k_60pct
window_tokens: 400000
reserve_output_tokens: 8000
safety_margin_tokens: 2000
utilization_target_ratio: 0.60
mode: ratio
...
```

➡️ Veja `docs/03A_SESSOES_MULTI_VS_CONTINUA.md` para critérios (multi‑sessão vs contínua) e heurísticas iniciais (ex.: 60%).
```

### Por que ratio + min/max
- Ratio escala com janelas diferentes.
- Min/max impõe limites para evitar:
  - **system bloat** (system/skills comendo tudo),
  - **tool bloat** (tool results dominando),
  - e protege invariantes.

---

## A biblioteca de perfis (inclui 350k e alternativas)

> Os perfis completos estão em `configs/budget_profiles.yaml`.

### 1) `balanced_350k` (seu baseline “melhorado”)
- Mantém core moderado, mas já impõe quotas duras para tools e RAG.
- Bom para orquestrações mistas.

### 2) `tool_heavy_350k` (o que você pediu explicitamente)
- **Reduz system+skills+history** e aumenta tool results + RAG.
- Usar quando o agente chama muitos tools (DB, APIs, pipelines) e precisa carregar outputs.

### 3) `rag_heavy_350k`
- Aumenta `rag_evidence` e reduz `tool_results`.
- Bom para pesquisa, compliance, respostas com citações.

### 4) `long_horizon_350k`
- Aumenta `state_json` e `history_summary`.
- Reduz recency e tool results; força externalização (pointers).
- Bom para tarefas que duram dias/semanas.

### 5) `low_latency_128k` (exemplo para janela menor)
- Core cacheável pequeno + tool results “tight”.
- Usa mais pointers e menos dumps.

### 6) `high_stakes_128k/350k`
- Reserva tokens para:
  - evidência/citações,
  - checklists,
  - e “auditable state”.
- Reduz recency “conversacional” para dar lugar a controles.

### 7) Perfis para **sessão contínua** (steady/burst)

Para threads longas, o pack inclui perfis que implementam **watermarks** via `utilization_target_ratio`:

- `continuous_*_steady_*` (ex.: 60%) → operar sustentado, evitar degradação e thrash.
- `continuous_*_burst_*` (ex.: 85%–90%) → permitir *bursts* de tools/RAG quando necessário.

O orquestrador alterna perfis por turno (com base em sinais como `expected_tool_calls`, `rag_required`, etc.) e volta ao **steady** após compaction.

➡️ Detalhes e heurísticas: `docs/03A_SESSOES_MULTI_VS_CONTINUA.md`.

---

## Realocação dinâmica (por turno) — sem virar caos

Perfis são estáveis, mas você pode realocar dentro de limites com **regras simples**.

### Sinais que você pode usar (baratos)
- `expected_tool_calls` (planner/heurística)
- `rag_required` (flag do workflow)
- `risk_level` (low/medium/high)
- `latency_sla_ms`
- `user_goal_type` (pesquisa vs execução vs chat)

### Exemplo de política (heurística)
- Se `expected_tool_calls >= 3`:
  - `tool_results += 10%`, `history_recency -= 5%`, `skills_active -= 5%`
- Se `rag_required == true`:
  - `rag_evidence += 10%`, `tool_results -= 5%`, `history_recency -= 5%`
- Se `risk_level == high`:
  - `state_json += 5%`, `rag_evidence += 5%`, `history_recency -= 5%`, `tool_results -= 5%`

> **Regra SOTA:** realocação só dentro de bandas `min/max`, e sempre registrada no ledger (“por que mudou?”).

---

## Como você evita “system prompt gigante” com skills

OpenAI Skills: quando disponíveis, o sistema injeta metadados (name/description/path) no contexto e o modelo pode ler o `SKILL.md` quando invoca a skill.[^openai_skills]

**Implicação:**  
- mantenha um **skills index** pequeno (metadados curtos),
- e carregue **skills ativas** apenas quando selecionadas.

---

## Observabilidade por perfil (obrigatório)

Cada profile deve declarar como medir:
- tokens por slice (antes/depois de compaction),
- número de eventos de summarization/compaction,
- taxa de “pointer rehydrate”,
- latência e custo por turno,
- taxa de “lost constraints”.

Veja `docs/11_OBSERVABILIDADE_E_GOVERNANCA.md`.

---

## Referências
[^openai_skills]: OpenAI API Docs, “Skills”, **date not found**, https://developers.openai.com/api/docs/guides/tools-skills
