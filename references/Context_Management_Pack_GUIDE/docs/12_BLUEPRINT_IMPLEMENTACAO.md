# 12 — Blueprint de Implementação (framework‑agnostic)

## Objetivo

Implementar um **Context Assembly Pipeline** que:
- respeite budgets por slice,
- compacte/sumarize com segurança,
- externalize artefatos grandes,
- suporte multi‑agente via handoffs,
- e produza observabilidade (ledger + tracing).

---

## Arquitetura de referência (Mermaid)

```mermaid
flowchart LR
  subgraph Inputs
    U[User message]
    H[Conversation history store]
    S[System/Dev/Policy kernel]
    K[Skills registry]
    T[Tool registry + schemas]
    R[RAG index / vector store]
    M[Durable memory store]
  end

  subgraph ContextAssembly["Context Assembly Pipeline"]
    C1[Classify workload
(tool-heavy? rag-heavy? risk?)]
    C2[Select budget profile
(config+dynamic reallocation)]
    C3[Build slices
(system/dev, skills, state, recency, summaries, tools, evidence)]
    C4[Token count + trim
(preflight)]
    C5[Compaction/summarization
(prefix/history/tool results)]
    C6[Finalize window
(order + boundaries + provenance)]
    L[Context Ledger
(tokens_by_slice + decisions)]
  end

  subgraph Execution
    A[LLM call]
    P[Tool calls]
    O[Outputs]
  end

  subgraph Stores
    B[Blob store
(artifacts/pointers)]
    E[Event log
(append-only)]
  end

  U --> C1
  H --> C3
  S --> C3
  K --> C3
  T --> C3
  R --> C3
  M --> C3

  C1 --> C2 --> C3 --> C4 --> C5 --> C6 --> A
  A --> P --> O

  C5 --> B
  C6 --> L --> E
  O --> E
```

---

## Pipeline: inputs → filtros → budgets → compaction → janela final

### 1) Classificação do workload (barata)
- tool-heavy vs tool-light
- rag-heavy vs no-rag
- long-horizon vs short
- risk-level (low/med/high)
- latency SLA

### 2) Seleção do budget profile
- `balanced`, `tool_heavy`, `rag_heavy`, `high_stakes`, `multi_agent`, etc.
- realocação dinâmica dentro de `min/max`.

**Sessão contínua (long-running):** prefira perfis *steady/burst*:
- **steady**: `utilization_target_ratio < 1.0` (watermark) para operar sustentado com headroom.
- **burst**: `utilization_target_ratio ≈ 1.0` para turns com tool/RAG explosivo.

➡️ Referência: `docs/03A_SESSOES_MULTI_VS_CONTINUA.md`.

### 3) Construção de slices tipadas
Cada slice tem:
- `type` (ex.: `STATE_JSON`, `RAG_EVIDENCE`, `TOOL_RESULT_DIGEST`)
- `priority` (hard/soft)
- `trusted` (sim/não)
- `token_cost`
- `content`
- `provenance` (source ids, pointers)

### 4) Preflight token counting
- contar tokens do conjunto
- se overflow, aplicar políticas de trim (por prioridade)

OpenAI documenta contagem de tokens via endpoint dedicado (pré‑call).[^openai_token_counting]

### 5) Compaction/summarization (gated)
- sumário prefixo de histórico (hierárquico)
- tool result digest + pointer
- remover evidência obsoleta

### 6) Finalização
- ordenar slices por prioridade
- inserir boundaries (“UNTRUSTED TOOL OUTPUT”)
- registrar ledger (tokens_by_slice + decisões)

---

## Pseudocódigo (núcleo)

### `context_budget_manager()`
```python
def context_budget_manager(cfg, workload_signals):
    profile = select_profile(cfg.profiles, workload_signals)

    # compute base input + apply steady-state watermark (sessão contínua)
    base = profile.window_tokens - profile.reserve_output_tokens - profile.safety_margin_tokens
    util = clamp_float(profile.get('utilization_target_ratio', 1.0), 0.0, 1.0)
    Y = int(base * util)

    # convert ratios to absolute budgets
    budgets = {}
    for slice_name, b in profile.slices.items():
        if profile.mode == "ratio":
            budgets[slice_name] = clamp(int(b["ratio"] * Y), b["min"], b["max"])
        else:
            budgets[slice_name] = b["tokens"]

    return Y, budgets, profile
```

### `select_context_slices()`
```python
def select_context_slices(slices, budgets):
    # slices: list[Slice(type, cost, priority, group)]
    selected = []
    used = {k: 0 for k in budgets}

    # hard-first, then soft by score
    for s in sorted(slices, key=lambda x: (x.priority, -x.score)):
        group = s.group
        if used[group] + s.cost <= budgets[group]:
            selected.append(s)
            used[group] += s.cost

    return selected, used
```

### `summarize_prefix_if_needed()`
```python
def summarize_prefix_if_needed(history, budget_history_summary, summarizer):
    prefix = history.prefix_outside_recency()
    if prefix.token_cost <= budget_history_summary:
        return prefix.as_text()

    # hierarchical: summarize chunks then summarize summary
    chunk_summaries = [summarizer(chunk) for chunk in prefix.chunks(max_tokens=4000)]
    summary = summarizer("\n".join(chunk_summaries))

    return truncate_to_budget(summary, budget_history_summary)
```

### `tool_result_compaction()`
```python
def tool_result_compaction(tool_result, budget, blob_store, summarizer):
    if tool_result.token_cost <= budget:
        return {"mode":"raw", "content": tool_result.content}

    # store raw externally
    uri = blob_store.put(tool_result.content)
    digest = summarizer(tool_result.content)

    return {
        "mode":"digest",
        "summary": truncate_to_budget(digest, budget),
        "pointer": {"uri": uri, "hash": sha256(tool_result.content)}
    }
```

### `multi_agent_handoff_pack()`
```python
def multi_agent_handoff_pack(
    *,
    handoff_mode,   # 'delegate' | 'transfer'
    from_agent,
    to_agent,
    objective,
    constraints,
    state_json,
    evidence_refs=None,
    artifacts=None,
    context_policy=None,   # how much history/slices to pass
    delegate_input=None,   # typed payload (delegate mode)
    budget_hint=None,
    token_ledger_snapshot=None,
    trace=None,
):
    pack = {
        'schema_version': 'handoff_contract_v2',
        'handoff_mode': handoff_mode,
        'handoff_id': new_id(),
        'from_agent': from_agent,
        'to_agent': to_agent,
        'objective': objective,
        'constraints': constraints,
        'state': state_json,
        'context_policy': context_policy or {},
        'evidence_refs': evidence_refs or [],
        'artifacts': artifacts or [],
        'budget_hint': budget_hint or {},
        'observability': {
            'trace_id': trace.id if trace else None,
            'span_id': trace.span_id if trace else None,
            'token_ledger_snapshot': token_ledger_snapshot or {},
        },
    }

    if handoff_mode == 'delegate':
        pack['delegate_io'] = {
            'input': delegate_input or {},
            'output': None,
        }

    return pack
```

---

## Código mínimo (runnable) no pack

Veja:
- `code/context_manager.py`
- `code/examples/` (histórico por tokens, truncation + digests, evidence pack packing, handoffs)

> O código é framework‑agnostic: você só precisa adaptar o “message serializer” do vendor (OpenAI/Anthropic/Google).

---

## Integração com vendors/frameworks (como “adapter layer”)

### Adapter: OpenAI
- serializar slices para roles / items
- tool results como `tool` messages ou `function_call_output` (conforme API)
- aproveitar `previous_response_id` quando possível[^openai_conversation_state]

### Adapter: Anthropic
- tool calls/results como content blocks (`tool_use` / `tool_result`)
- prompt caching via `cache_control`[^anthropic_prompt_caching]

### Adapter: Google
- conteúdos como `parts` com `functionCall`/`functionResponse`
- context caching quando suportado[^google_context_caching]

### Framework adapters
- LangGraph: integrar assembler como “node” e persistir state via checkpointer
- LangChain: integrar como middleware antes do LLM call

---

## Referências
[^openai_token_counting]: OpenAI API Docs, “Counting tokens”, **date not found**, https://developers.openai.com/api/docs/guides/token-counting
[^openai_conversation_state]: OpenAI API Docs, “Conversation state”, **date not found**, https://developers.openai.com/api/docs/guides/conversation-state
[^anthropic_prompt_caching]: Claude API Docs, “Prompt caching”, **date not found**, https://platform.claude.com/docs/en/build-with-claude/prompt-caching
[^google_context_caching]: Google, “Context caching (Gemini API)”, **date not found**, https://ai.google.dev/gemini-api/docs/caching
