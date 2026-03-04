# 06 — Histórico de Conversa por Limite de Contexto (tokens) e Compaction de Prefixo

## Por que “últimos N turnos” é inferior

- Turnos variam de tamanho; a mesma regra pode ser 5k tokens ou 200k.
- Tool outputs e RAG podem “ocupar” turnos, distorcendo N.
- Em janelas grandes, o custo de atenção aumenta e você sofre “lost in the middle/context rot”.[^anthropic_context_engineering]

**SOTA:** selecione histórico por **budget em tokens**, com “recency window” + sumários hierárquicos + estado estruturado.

---

## Arquitetura recomendada para histórico

### 1) `STATE_JSON` como fonte de verdade
Um objeto estruturado com campos canônicos:

```json
{
  "objective": "...",
  "constraints": ["..."],
  "decisions": [{"id":"D1","text":"...","date":"..."}],
  "assumptions": ["..."],
  "open_questions": ["..."],
  "todo": [{"id":"T1","owner":"agent","text":"...","status":"open"}],
  "glossary": {"X":"..."}
}
```

- Atualize no fim de cada turno relevante.
- Mantenha pequeno e estável (ex.: 2k–20k tokens, via budget).

### 2) `history_recency` (janela deslizante por tokens)
- Guarde os turnos mais recentes “verbatim” até um limite em tokens.
- Inclua tool interactions recentes (mas compactadas).

### 3) `history_summary` (prefixo hierárquico)
- Um sumário do que ficou fora da recency window.
- Estruturado, com “facts/decisions/constraints”.

### 4) “history as corpus” (opcional)
- Armazene transcript completo fora da janela (DB/blob).
- Faça retrieval de turnos relevantes quando necessário (S3 do doc 03).

---

## Algoritmo: seleção por tokens (recency) + sumarização do prefixo

### Passos
1) Conte tokens do conjunto base (system/dev/skills/state/tools schemas etc).
2) Reserve budgets para:
   - recency window
   - history summary
3) Inclua turnos do mais recente para o mais antigo até estourar `history_recency_budget`.
4) Se houver “prefixo descartado”:
   - gere/atualize `history_summary` (hierárquico), mantendo invariantes.
5) Registre no ledger:
   - quantos tokens foram removidos, quantos entraram, e hashes/ids para rastreio.

Em OpenAI, existe endpoint dedicado para contar tokens de um input (útil para evitar overflow antes do call).[^openai_token_counting]

---

## Hierarchical summaries (multi‑nível)

Para tarefas longas, um único sumário vira “lixo comprimido”. SOTA usa níveis:

- **S1 (turn-level)**: resumo de cada turno/segmento
- **S2 (episode-level)**: agrega 10–50 turnos em um “capítulo”
- **S3 (project-level)**: decisões e marcos

**Trigger típico:**
- Quando `prefix_tokens > threshold`, compacte em S1.
- Quando `S1_count > K`, compacte em S2.
- Quando `S2_count > M`, compacte em S3.

---

## Failure modes e mitigação

### 1) Summary drift
O sumário altera constraints/decisões.

**Mitigação:**
- sumário **estruturado** (campos fixos),
- “do not change constraints” no prompt de sumário,
- validação automática: comparar `constraints` antes/depois.

### 2) Lost constraints
O agente ignora requisito antigo.

**Mitigação:**
- `STATE_JSON` sempre presente,
- testes de trajetória (ver doc 11/14),
- “constraint echo” (o agente reafirma constraints antes de executar ações).

### 3) Context poisoning (via user/tools/RAG)
Instruções maliciosas entram no sumário.

**Mitigação:**
- sumário deve **remover instruções** que venham de dados,
- marcar “untrusted content” explicitamente,
- usar políticas de safety e approvals.

OpenAI enfatiza práticas de segurança para agentes (inclui riscos de tool misuse/prompt injection).[^openai_agent_safety]

---

## Vendor-specific: continuidade vs reenvio

OpenAI descreve `previous_response_id` para continuar conversa sem reenviar todo o histórico (quando o cache de conexão resolve o ID). Se não resolver, deve-se reenviar contexto completo.[^openai_conversation_state]

**Implicação para SOTA:**  
Mesmo com `previous_response_id`, você ainda precisa do pipeline:
- porque tools e retrieval mudam,
- porque você quer budgets por slice,
- e porque multi‑agente exige handoffs.

---

## Referências
[^anthropic_context_engineering]: Anthropic Engineering, “Effective context engineering for AI agents”, **Published Sep 29, 2025**, https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
[^openai_token_counting]: OpenAI API Docs, “Counting tokens”, **date not found**, https://developers.openai.com/api/docs/guides/token-counting
[^openai_agent_safety]: OpenAI API Docs, “Safety in building agents”, **date not found**, https://developers.openai.com/api/docs/guides/agent-builder-safety
[^openai_conversation_state]: OpenAI API Docs, “Conversation state”, **date not found**, https://developers.openai.com/api/docs/guides/conversation-state
