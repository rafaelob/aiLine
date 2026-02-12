# 13 — Custos (Claude Opus 4.6) + Estratégia para ficar barato

> O hackathon dá créditos; ainda assim, custo/latência impactam demo.

---

## 1) Preços oficiais (resumo)
Claude Opus 4.6 (padrão, prompts ≤ 200k tokens):
- **Input:** $5 / MTok
- **Output:** $25 / MTok

Para prompts > 200k tokens:
- **Input:** $10 / MTok
- **Output:** $37.50 / MTok

Prompt caching (≤ 200k tokens):
- Write: $6.25 / MTok
- Read: $0.50 / MTok

---

## 2) Onde o AiLine gasta tokens
### 2.1) Planner (DeepAgents)
- tende a produzir output longo (plano + justificativas + checklist)
- piora quando o agente “pensa demais”

### 2.2) Executor (Agent SDK)
- chamadas de tool + síntese final
- output geralmente menor se você for disciplinado

---

## 3) Estratégias para reduzir custo sem matar o demo

### 3.1) Separar “draft curto” de “expansão”
- Primeiro: gerar um draft com bullets curtos
- Depois: expandir só se necessário (ou só em 1 seção no demo)

### 3.2) Prompt caching
- o refinement loop repete muito contexto → caching ajuda muito

### 3.3) Long-context com cuidado
- usar 1M context só quando for “momento wow”
- caso contrário, use RAG + mapa resumido

### 3.4) Limitar iterações
- `max_iters = 2` ou `3` no refinement loop já parece “persistência” no demo

---

## 4) Regra de bolso (estimativa rápida)
Se um run típico consumir:
- 30k tokens input
- 10k tokens output

Custo aproximado:
- input: 0.03 MTok * $5 = **$0.15**
- output: 0.01 MTok * $25 = **$0.25**
- total: **$0.40** por run

Isso é totalmente ok para demo + avaliação.

---

