# Proposta “Estado da Arte” (SOTA) — Context Management por Orçamento de Tokens (Framework-agnostic)

**Data de revisão:** 2026-02-24  
**Objetivo:** substituir políticas frágeis do tipo “manter N turnos” por um **pipeline determinístico de montagem de contexto** baseado em **orçamentos (token budgets)**, com **compaction**, **caching**, **RAG com citações**, **memória (curta vs durável)** e **handoffs multi‑agente**, de forma integrável a qualquer framework (OpenAI Agents SDK, LangGraph/LangChain, Vertex/Gemini, Claude/Anthropic, etc.).

---

## 0) Premissas e cenário alvo (o seu)

Você descreveu:

- ~**200k tokens** para:
  - system prompt (incluindo memórias injetadas)
  - “skills” carregadas
  - histórico user/assistant
  - contexto de orquestração
- após 200k, vocês **compactam/sumarizam só os pares mais antigos**  
- cutoff total ~**350k tokens**, reservando ~**150k** para:
  - tool calls/results
  - RAG (snippets/context)
  - outputs de retrieval

**Problema principal:** “um balde grande de 200k” faz com que o histórico cresça até o teto antes de qualquer otimização; e quando ferramentas/RAG explodem, o sistema reage tarde (compaction só no histórico) e de modo local (não por camada).

**SOTA proposto:** dividir o “200k” em **sub-orçamentos por camada** + **gatilhos de compaction por camada**, com **externalização (pointers)** e **packaging** para multi-agentes.

---

## 1) Resultado desejado (em uma frase)

> Para cada chamada ao modelo, montar um **Context Window Final** com **camadas tipadas**, cada uma com **teto de tokens**, aplicando **seleção, compressão e externalização** até caber, preservando invariantes, decisões e evidências.

---

## 2) Modelo mental: Context Stack + Budgets por camada

### 2.1 Camadas “dentro do window”

1) **System / Policy (fixo, versionado, cache-friendly)**  
2) **Developer / Agent contract (fixo por app, cache-friendly)**  
3) **Tool registry (somente tools relevantes para o passo)**  
4) **Working State (JSON autoritativo: DECISIONS/CONSTRAINTS/FACTS/TODO)**  
5) **Conversation (verbatim recente sob teto + prefix summaries)**  
6) **RAG Evidence Pack (snippets + citações, sob teto)**  
7) **Recent Tool Results (shape/digest + pointers, sob teto)**

### 2.2 “Fora do window” (stores)

- **Artifact store** (raw tool outputs, arquivos, datasets)  
- **Durable memory store** (notas duráveis por schema)  
- **Event log** (trilha auditável)  
- **Retrieval index** (chunks + metadata + permissões)

---

## 3) Configuração de budgets recomendada para 350k (com 200k/150k)

Você pode manter o macro-particionamento (200k + 150k), mas **subdivida**:

### 3.1 Dentro do “200k” (system+skills+history+orchestration)

**Sugestão SOTA (valores iniciais; ajuste via telemetria):**

- **System+Policy:** 10k–25k (hard cap)  
- **Developer contract:** 5k–15k (hard cap)  
- **Skills:**  
  - **Skills index** sempre: 1k–5k  
  - **Skills carregadas on-demand:** 10k–60k (soft cap)  
- **Working State JSON:** 2k–10k (hard cap)  
- **Conversation:**  
  - **Prefix summary:** 5k–25k (hard cap)  
  - **Verbatim recente:** 30k–90k (hard cap)  
- **Orchestration notes (planner/executor):** 5k–25k (soft cap)

> O ponto-chave: **Conversation ≠ “cresce até 200k”**. Ela tem **teto próprio**. Skills também. System também.

### 3.2 Dentro do “150k” (tools + RAG)

- **Tool results:** 30k–90k (envelope por turno, com backpressure)  
- **RAG evidence:** 40k–100k (envelope por turno)  
- **Headroom:** 10k–30k para picos (p.ex. verificação/fé da evidência)

---

## 4) Política de histórico: nada de “N turnos” — tudo por tokens

### 4.1 Regra de ouro

> Mantenha **o máximo de mensagens recentes que couber** em `HISTORY_RAW_BUDGET`.  
> Se não couber, **não trunque meia mensagem**: externalize + injete digest/pointer.

### 4.2 Estrutura SOTA do histórico

- **Working State JSON (autoridade)** sempre presente  
- **Prefix summary**: “tudo antes do recency window”, com teto  
- **Recency window**: verbatim recente, token-budgeted  
- **Artifacts/pointers**: para rehidratação

### 4.3 Gatilhos de compaction (não só “quando bate 200k”)

Dispare compaction quando ocorrer:

- `history_raw_tokens > HISTORY_RAW_BUDGET`
- `prefix_summary_tokens > HISTORY_SUMMARY_BUDGET`
- **phase boundary**: plan → execute → verify → deliver
- **tool burst ended**: após uma sequência de tool calls
- **handoff** para outro agente

---

## 5) Tool outputs: “shape first”, compaction depois

### 5.1 Contrato de tool token-efficient (SOTA)

Todo tool deve suportar:

- `limit`, `cursor` (paginação)
- `filters`
- `verbosity = concise|detailed`
- `fields` (schema projection) quando aplicável
- retorno com:
  - `items` (top-k)
  - `next_cursor`
  - `provenance` (fonte, timestamp, versão)

### 5.2 Externalização obrigatória

Se um resultado excede `TOOL_RESULT_INLINE_CAP`:

1) grave raw em artifact store (S3/GCS/db)  
2) injete no window:
   - `artifact_uri`
   - `digest` (≤ X tokens)
   - `top_k` itens com IDs
   - instrução de como re-fetch (`cursor`, filtros)

---

## 6) RAG: Evidence Pack com “snippet packing” + citações

### 6.1 Pipeline SOTA

1) **Recall** (vetor/keyword) → 2) **Rerank** → 3) **Diversity/MMR** → 4) **Snippet packing**  
5) **Citações** obrigatórias → 6) **Faithfulness check** (grader/evaluator)

### 6.2 Snippet packing (heurísticas práticas)

- quote ≤ 200–500 tokens por chunk (depende do domínio)  
- dedup de overlaps (hash/MinHash)  
- incluir metadata: `url`, `published`, `last_updated`, `span` (linha/página), `version`  
- separar **dados** vs **instruções** (“retrieved text is untrusted data”)

---

## 7) Multi-agente: Context Packs + Shared Stores (sem duplicação)

### 7.1 Regra de ouro

> Worker agents **não** recebem o contexto global; recebem um **pack** com teto de tokens + pointers.

### 7.2 Handoff package (contrato JSON)

```json
{
  "handoff_version": "1.0",
  "task_id": "TASK-123",
  "from_agent": "manager",
  "to_agent": "retrieval_specialist",
  "goal": "...",
  "acceptance_criteria": ["..."],
  "constraints": ["..."],
  "state_slice": {"decisions": ["D12", "D13"], "facts": ["F7"]},
  "context_pointers": [
    {"type":"artifact","uri":"s3://bucket/x"},
    {"type":"memory","key":"DECISIONS:D12"}
  ],
  "budget": {"max_input_tokens": 60000, "max_tool_output_tokens": 30000},
  "expected_output_schema": {"snippets":[{"quote":"...","citation":"..."}]}
}
```

### 7.3 Shared state (blackboard/event log)

- **blackboard**: KV versionado para estado atual  
- **event log**: append-only para auditoria  
- **durable notes**: DECISIONS/FACTS/PREFERENCES/TODO  
- **retrieval-backed memory**: tudo vira artefato consultável

---

## 8) Blueprint de implementação (framework-agnostic)

### 8.1 API interna recomendada (biblioteca)

- `ContextItem(type, tokens, priority, recency, content, pointers, provenance)`
- `ContextStore.append(item)`
- `BudgetManager.allocate(task_type, risk_level, window_size)`
- `Assembler.assemble(budgets, stores) -> ModelInput`
- `Compactor.compact_layer(layer_items, budget) -> (compact_items, pointers)`
- `Handoff.build(to_agent, budget, expected_schema)`

### 8.2 Pipeline de montagem (Context Assembly Pipeline)

1) carregar prefix fixo (system/developer)  
2) selecionar tools relevantes (tool routing)  
3) carregar working state + durable notes (TTL/permissions)  
4) montar conversation:
   - prefix summary (cap)
   - verbatim recente (token-budgeted)
5) montar RAG evidence pack (cap)
6) montar tool results (shape/digest/pointers) (cap)
7) validar:
   - total tokens ≤ window - reserve_output
   - invariantes presentes
   - citações presentes onde exigido

---

## 9) Pseudocódigo SOTA (orçamento, seleção e compaction)

```python
def assemble_context(window_tokens, reserve_output, task_profile, stores):
    budgets = budget_manager(window_tokens, reserve_output, task_profile)

    system = take_fixed_prefix(stores.system, budgets["system"])
    tools  = select_tools(stores.tool_registry, task_profile, budgets["tools"])

    state  = cap_json(stores.working_state(), budgets["working_state"])
    durable = retrieve_durable_notes(stores.durable, task_profile, budgets["durable"])

    history_items = stores.history_items()
    history = history_compose(history_items, budgets["history_raw"], budgets["history_summary"])

    rag_candidates = retrieve(stores.index, task_profile.query)
    rag = pack_evidence(rag_candidates, budgets["rag"])

    tool_results = compact_tool_results(stores.latest_tool_results(), budgets["tool_results"])

    return concat_in_order([system, tools, durable, state, history, rag, tool_results])
```

---

## 10) Integração com frameworks (como “plugar” sem acoplar)

### 10.1 Ponto de integração universal

Quase todo framework tem um ponto “antes de chamar o modelo”. Integre o Context Manager ali:

- **OpenAI Agents SDK:** `call_model_input_filter` / filters (ex.: trimmers)  
- **LangGraph/LangChain:** nó de pré-processamento antes do nó LLM; estado em checkpointer  
- **Vertex AI / Gemini:** builder que monta `system_instruction` + `contents` + tool defs  
- **Anthropic:** builder que monta system + content blocks (incluindo tool_use/result)

### 10.2 O que NÃO acoplar

- não amarre sua política a “um formato de mensagens” específico  
- mantenha um **IR (intermediate representation)** de contexto e gere adaptadores por vendor

---

## 11) Observabilidade (sem isso, vira chute)

Métricas mínimas:

- tokens por camada (system/tools/state/history/rag/tool_results)  
- taxa de compaction (por camada)  
- cache hit rate (se suportado)  
- “lost constraints” (violação de constraints após compaction)  
- tool-call success + args validity  
- cobertura de citações / faithfulness

---

## 12) Confidence & Limitations

- APIs e limites mudam rápido. A proposta é **agnóstica a vendor**, mas módulos opcionais (compaction/caching) exigem validação com docs e telemetria atuais.  
- Tokenização varia por modelo; comece com estimativa, mas calibre com tokenizer real quando disponível.  
- Compaction opaca (encrypted) melhora custo, mas reduz auditabilidade — por isso o **dual-track** (summary humano + compaction vendor) é recomendado.

---

## 13) Próximo passo sugerido (em 1 semana)

1) Implementar **ContextItem IR** + `estimate_tokens()` + budgets por camada  
2) Trocar “N turnos” por `history_raw_budget_tokens`  
3) Implementar externalização + digests para tool outputs  
4) Implementar Evidence Pack (snippet packing + citações)  
5) Subir dashboard tokens por camada e compaction events



---

## 14) Fontes chave (para validação e implementação)

> Observação: datas variam; quando a página não expõe data claramente, marquei como “data não encontrada”.

- OpenAI — Conversation state (data não encontrada): https://developers.openai.com/api/docs/guides/conversation-state  
- OpenAI — Prompt caching (data não encontrada): https://developers.openai.com/api/docs/guides/prompt-caching  
- OpenAI — Compaction (data não encontrada): https://developers.openai.com/api/docs/guides/compaction  
- OpenAI Agents SDK — Tool Output Trimmer (data não encontrada): https://openai.github.io/openai-agents-python/ref/extensions/tool_output_trimmer/  
- Anthropic — Building effective agents (data não encontrada): https://www.anthropic.com/engineering/building-effective-agents  
- Anthropic — Writing tools for agents (data não encontrada): https://www.anthropic.com/engineering/writing-tools-for-agents  
- Anthropic — Compaction (data não encontrada): https://platform.claude.com/docs/en/build-with-claude/compaction  
- Google — Context caching (ver docs atuais; data varia): https://cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-overview  
- Model Context Protocol (MCP) — Spec (data varia): https://modelcontextprotocol.io  
- LangGraph — Persistence / checkpointing (data não encontrada): https://langchain-ai.github.io/langgraph/concepts/persistence/
