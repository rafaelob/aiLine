# 11 — Observabilidade, Evals e Governança (token ledger ou it didn’t happen)

## Por que isso é parte de Context Management

Sem telemetria, “estratégia de contexto” vira opinião.  
SOTA exige que o pipeline de contexto seja:

- **observável** (token accounting + tracing)
- **auditável** (diffs, pointers, hashes)
- **testável** (trajetórias e regressões)
- **seguro** (least privilege, approvals, redaction)

OpenAI tem suporte a tracing/evals (ex.: trace grading) na camada de agentes.[^openai_trace_grading]  
O ADK (Google) também fornece caminhos para observabilidade via plugins.[^google_adk_plugins]

---

## 1) Métricas essenciais (mínimo viável)

### Context/Token metrics (por turno)
- `tokens_total_input`
- `context_fill_ratio` = `tokens_total_input / window_tokens` (mede quão “cheio” o window está)
- `utilization_target_ratio` (watermark configurado; útil para sessão contínua)
- `tokens_by_slice`:
  - system/dev
  - skills_index / skills_active
  - state_json
  - history_recency / history_summary
  - tool_schemas / tool_results
  - rag_evidence
- `overflow_events` (quantas vezes quase estourou)
- `compaction_events` (quantas e quando)
- `compaction_events_per_100_turns` (sinal de thrash em sessão contínua)
- `summary_tokens_saved`

### Métricas por **sessão** (especialmente para sessão contínua)
- `session_duration_turns`
- `steady_state_violations` (quantas vezes excedeu `W_steady`)
- `hard_cap_violations` (deve ser ~0)
- `summary_drift_incidents` (diff em DECISIONS/CONSTRAINTS após compaction)

OpenAI documenta endpoint para contagem de tokens de um input antes de chamar o modelo, útil para ledger e prevenção.[^openai_token_counting]

### Multi-agent (handoffs/delegation)
- `handoff_mode` (transfer/delegate)
- `handoff_count` e `handoff_chain_depth`
- `handoff_context_tokens` (tamanho do context pack enviado)
- `wrong_agent_selected_rate` (roteamento incorreto)
- `delegate_parse_fail_rate` (falha ao parsear output tipado)

> Dica: separe métricas por *modo* (transfer vs delegate) porque eles têm trade-offs muito diferentes. (Ver `10A_DUAL_HANDOFF_TRANSFER_VS_DELEGATE.md`.)

### Latência/custo
- tempo de assemble do contexto
- tempo por tool call
- tempo de retrieval/rerank
- custo por turno (se disponível)

### Qualidade do agente
- `tool_call_accuracy` (chama a tool certa? com args corretos?)
- `rerank_quality` (top‑k contém evidência correta?)
- `factuality` / `citation_coverage`
- `repetition_rate`
- `lost_constraints_rate` (violou constraint?)
- `escalation_rate` (quantas vezes pediu HITL?)

---

## 2) Logging/tracing: o que registrar com segurança

### O que logar (SOTA)
- ledger com tokens por slice
- ids/hashes de artefatos (pointers), não o conteúdo bruto
- decisões do assembler (por que incluiu/excluiu slice)
- tool calls: name + args (com redaction)
- tool results: digest + pointer + hash
- evidence pack: ids + urls + spans

### O que NÃO logar
- segredos (keys, tokens)
- PII em claro (a menos que estritamente necessário e permitido)
- dumps completos de documentos/tool results

### Tracing end-to-end
Idealmente, cada turno vira um trace com spans:
- `assemble_context`
- `retrieve_rag`
- `call_tool_X`
- `summarize_prefix`
- `compact_tool_results`
- `final_completion`

OpenAI Agents SDK documenta tracing e trace grading como parte da stack de agentes/evals.[^openai_trace_grading][^openai_agents_tracing]

---

## 3) Offline evals + trajectory tests + regressões

### Offline evals (unit-like)
- “dado um estado e um objetivo, o assembler monta a janela certa?”
- “sumário preserva constraints?”
- “tool result compaction mantém invariantes?”

### Trajectory tests (integration)
Rode roteiros completos e valide:
- constraints nunca violadas
- tool calls corretas
- citações presentes
- budgets respeitados

### Regressões
- Qualquer mudança em prompt/skills/tools/reranker deve rodar regressões mínimas.
- Armazene goldens (inputs → outputs) e compare diffs.

---

## 4) Segurança e governança

### Prompt injection & retrieval poisoning
- Treat tool/RAG as untrusted.
- Strip instructions.
- Use allowlists e approvals.

O MCP spec dedica seção a security/trust & safety, enfatizando consentimento e cautela com ferramentas (arbitrary code/data access).[^mcp_spec]  
OpenAI recomenda práticas para segurança em building agents.[^openai_agent_safety]

### Tool permissioning / least privilege
- tokens de auth por usuário
- scoping por tenant
- separar tools `preview` vs `commit`
- require approval por tool sensível (MCP)

### HITL gates (high-stakes)
- se risco alto, exigir aprovação antes de ação irreversível.
- logar razão do gate.

---

## Referências
[^openai_trace_grading]: OpenAI API Docs, “Trace grading”, **date not found**, https://developers.openai.com/api/docs/guides/trace-grading
[^openai_agents_tracing]: OpenAI Agents SDK Docs, “Tracing”, **date not found**, https://openai.github.io/openai-agents-python/tracing/
[^openai_token_counting]: OpenAI API Docs, “Counting tokens”, **date not found**, https://developers.openai.com/api/docs/guides/token-counting
[^google_adk_plugins]: Google ADK Docs, “Plugins (incl. observability integrations)”, **date not found**, https://google.github.io/adk-docs/plugins/
[^mcp_spec]: Model Context Protocol, “Specification (Version 2025-06-18)”, **2025-06-18**, https://modelcontextprotocol.io/specification/2025-06-18
[^openai_agent_safety]: OpenAI API Docs, “Safety in building agents”, **date not found**, https://developers.openai.com/api/docs/guides/agent-builder-safety
