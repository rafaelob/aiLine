# 09 — Memória e Compaction: working vs durable + triggers + safe restart

## 1) Duas memórias, dois mundos

### Working memory (curto prazo)
- Variáveis de execução do turno.
- Resultados temporários de tools.
- Plan/steps atuais.

**Onde vive:** `STATE_JSON` no contexto + runtime store (cache) com TTL curto.

### Durable memory (persistente)
- Preferências do usuário (ex.: formato de saída).
- Decisões estáveis do projeto.
- Fatos verificados e relevantes.

**Onde vive:** banco/kv/“memory bank” + retrieval on-demand.

No ADK (Google), MemoryService pode ser in‑memory ou Vertex AI Memory Bank, com ferramentas para preload ou load conforme política.[^google_adk_memory]

---

## 2) Schema recomendado para durable notes (SOTA)

> O maior erro é “salvar texto livre” sem estrutura: vira lixo e aumenta risco de drift.

### Esquema DECISIONS / FACTS / PREFERENCES / TODO
```yaml
durable_notes:
  decisions:
    - id: D-001
      text: "Adotar budget profiles por workflow"
      rationale: "tool-heavy explode janela"
      date: "2026-02-24"
      status: "active"
  facts:
    - id: F-010
      text: "Ferramentas retornam digest+pointer; dumps ficam fora"
      evidence: ["E1","E2"]
      confidence: "high"
  preferences:
    - id: P-002
      subject: "user"
      text: "Preferir respostas em português técnico"
      ttl_days: 180
  todos:
    - id: T-007
      text: "Implementar token ledger por slice"
      owner: "platform"
      status: "open"
```

### TTLs e refresh
- Preferências podem expirar (TTL).
- Fatos devem ter “confidence” e “evidence ids”.
- Decisões podem ser revogadas (status).

---

## 3) Compaction: quando e como

### Quando compactar
- Quando `history_recency` estoura budget.
- Em “phase boundaries” (fim de etapa).
- Antes de handoff para outro agente (reduzir payload).
- Em intervalos fixos (ex.: a cada 10–20 turnos) *apenas se* o ledger indicar bloat.

### Como compactar (SOTA)
- Não compactar tudo junto. Compactar por fatias:
  1) histórico antigo → sumário hierárquico
  2) tool dumps → digest + pointer
  3) RAG “obsoleto” → remover, manter apenas citações usadas

### Vendor compaction (quando disponível)
OpenAI documenta um endpoint de compaction (`/responses/compact`) que retorna uma janela compactada canônica e um item opaco (criptografado) que deve ser reaplicado nas próximas chamadas.[^openai_compaction]

Claude (Anthropic) também documenta compaction e outras técnicas de gerenciamento de contexto.[^anthropic_compaction]

> **SOTA:** trate compaction como **operação observável** com diffs, contagem de tokens e testes de regressão.

---

## 4) Safe restart patterns (reinicializar sem perder o estado)

Padrão recomendado:
1) Persistir `durable_notes` (schema acima)
2) Persistir `session_event_log` (event sourcing)
3) Persistir `artifacts` grandes (blobs)
4) Ao reiniciar:
   - carregar `policy kernel` + `tools registry`
   - carregar `STATE_JSON` reconstruído (a partir de durable notes + últimas N ações)
   - rehidratar apenas pointers necessários

No ADK, o conceito de session/state/artifacts ajuda a implementar esse padrão.[^google_adk_context]

---

## 5) Privacidade e limites (não-negociável)

- Não salvar segredos (tokens, chaves) em durable memory.
- Segmentar memória por tenant/user.
- Redigir PII em logs.
- Aplicar least privilege às ferramentas que acessam memória.

O MCP spec enfatiza consentimento explícito, privacidade e cautela com ferramentas (arbitrary code/data access).[^mcp_spec]

---

## Referências
[^google_adk_memory]: Google ADK Docs, “Memory”, **date not found**, https://google.github.io/adk-docs/sessions/memory/
[^google_adk_context]: Google ADK Docs, “Context”, **date not found**, https://google.github.io/adk-docs/context/
[^openai_compaction]: OpenAI API Docs, “Compaction”, **date not found**, https://developers.openai.com/api/docs/guides/compaction
[^anthropic_compaction]: Claude API Docs, “Compaction”, **date not found**, https://platform.claude.com/docs/en/build-with-claude/compaction
[^mcp_spec]: Model Context Protocol, “Specification (Version 2025-06-18)”, **2025-06-18**, https://modelcontextprotocol.io/specification/2025-06-18
