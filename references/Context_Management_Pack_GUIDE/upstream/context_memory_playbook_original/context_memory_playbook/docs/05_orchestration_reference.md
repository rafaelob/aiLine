# Orquestração de referência: loop do agente com budgets, skills, MCP, RAG e memória

Este documento descreve um loop de agente “tool‑centric” que mantém previsibilidade via X/Y.

A meta é garantir, a cada turno:

- **core_tokens <= X**
- **total_tokens <= Y**
- tool outputs nunca dominam o contexto

---

## 1) Estado mínimo por sessão (fora do prompt)

- `history_full`: histórico completo (fora do prompt)
- `history_working_set`: âncoras recentes (para o core)
- `rolling_summary`: resumo acumulado (canônico) ou compaction server‑side quando disponível
- `artifacts`: mapa `handle → path/url` para payload grande
- `skills_registry`: catálogo (nome/descrição) + loader sob demanda
- `tool_registry`: catálogos (MCP servers, tools locais/remotas)
- `memory_store`: (vetor/grafo) + policy
- `token_ledger`: métricas por turno (observabilidade)

---

## 2) Loop do turno (alto nível)

### Stage A — Construir core (<= X)
1) receber `user_text`
2) construir `core_messages` com:
   - system + developer
   - regras duráveis (projeto/escopo)
   - skills index (mínimo)
   - skills ativas (se houver)
   - rolling summary (ou item de compaction)
   - últimas âncoras (N turns)
   - estado de orquestração (opcional)
   - mensagem do usuário

3) se `core_tokens > X`:
   - compacte turns antigos → rolling summary
   - reduza âncoras
   - *trim* controlado do summary (último recurso)

### Stage B — Planejar e decidir ferramentas
4) decidir: responder direto **ou** usar tools
   - heurística (classificador simples) + LLM planner (opcional)
   - se usar LLM planner, adicione **tool catalog mínimo** no tool budget

### Stage C — Tool execution com guardrails
5) para cada tool call:
   - (se necessário) pedir aprovação do usuário
   - executar tool fora do prompt
   - persistir payload bruto em artefato (handle)
   - gerar `TOOL_RESULT_SUMMARY` compacto

### Stage D — RAG e evidências (quando aplicável)
6) se houver web/file search/RAG:
   - gerar `EvidencePack` (quotes curtas + URLs + datas)
   - compressão por orçamento

### Stage E — Memória (read + write)
7) recuperar memória relevante (subgrafo/perfil)
   - summarize para caber no tool budget
8) propor escrita de memória (candidatos)
   - exigir confirmação antes de aplicar

### Stage F — Responder
9) construir `final_messages = core_messages + tool_context_blocks`
   - tool_context_blocks devem caber no orçamento disponível (<= Y − core_tokens)
10) chamar LLM para resposta final
11) atualizar `history_full`, `history_working_set`, `rolling_summary`, `ledger`

---

## 3) Onde aplicar recursos “estado‑da‑arte” por provedor (links)

### 3.1 Compaction server‑side (OpenAI)
Quando o provedor oferece compaction interno, você pode reduzir a necessidade de rolling summary client‑side.

OpenAI:  
https://platform.openai.com/docs/guides/compaction

### 3.2 Conversation state (OpenAI)
Em vez de reenviar o histórico todo manualmente, você pode usar estado conversacional (encadeando `previous_response_id` etc.).

OpenAI:  
https://platform.openai.com/docs/guides/conversation-state

### 3.3 Token counting endpoint (OpenAI)
Para métricas exatas e para evitar “estouro” (inclui tools/schemas):
https://platform.openai.com/docs/guides/token-counting

### 3.4 Tools (OpenAI)
- Web search: https://platform.openai.com/docs/guides/tools-web-search  
- File search: https://platform.openai.com/docs/guides/tools-file-search  
- Connectors/MCP: https://platform.openai.com/docs/guides/connectors-mcp

### 3.5 Prompt caching
- OpenAI: https://platform.openai.com/docs/guides/prompt-caching  
- Anthropic: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching

### 3.6 Background mode (OpenAI)
Para tarefas longas e pipelines:
https://platform.openai.com/docs/guides/background-mode

---

## 4) Observabilidade recomendada (token ledger)

Por turno, logue:

- `core_tokens`
- `total_tokens`
- `tool_budget_tokens` (Y − core)
- `history_turns_kept`
- `turns_compacted`
- `rolling_summary_tokens`
- `skills_index_tokens`, `active_skills_tokens`
- `tool_catalog_tokens`, `tool_schema_tokens`
- `tool_payload_bytes`, `tool_inline_tokens`
- `rag_items`, `quote_tokens`
- `memory_slice_tokens`
- tempo por etapa (planner, tools, resposta)

Isso vira:
- tuning de X e Y,
- detecção de regressões,
- custo por sessão.

---

## 5) Padrões recomendados

### 5.1 Two‑pass tool use
1) Passo 1: planner (core + catálogo mínimo)
2) Passo 2: resposta (core + resultados resumidos + evidências)

### 5.2 Evidence‑first answers
Quando a resposta depende de fontes:
- a resposta final deve citar/listar as evidências,
- e o EvidencePack deve ser o input principal do turno de escrita.

### 5.3 Memory write as proposal
Memória durável deve ser:
- proposta,
- confirmada,
- aplicada.

---

## 6) Checklist de erros comuns

- [ ] tool outputs grandes sem handle
- [ ] schemas completos sempre (sem on-demand)
- [ ] rolling summary crescendo sem teto
- [ ] memória persistindo dados instáveis
- [ ] ausência de token ledger
- [ ] falta de política de aprovação para tools perigosas

---

## Referência no código

- `src/contextkit/context_assembler.py`
- `src/contextkit/tool_context_manager.py`
- `src/contextkit/rolling_summary.py`
- `src/contextkit/memory/*`
- `examples/demo_minimal.py`
