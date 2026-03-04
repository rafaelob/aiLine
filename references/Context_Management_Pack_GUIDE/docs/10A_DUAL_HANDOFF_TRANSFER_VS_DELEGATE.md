# 10A — Padrões de Handoff: **Transfer** vs **Delegate** (Dual handoff, coexistindo)

> **Objetivo deste doc:** formalizar (e operacionalizar) dois modos *coexistentes* de coordenação multi‑agente que aparecem em stacks modernos (OpenAI Agents SDK, Google ADK, LangGraph/LangChain, Claude Code) e têm impacto direto em **custo**, **risco**, **latência** e **qualidade** do **context management**.

## 1) O que significa “Dual handoff”

A tabela da imagem que você compartilhou descreve uma distinção que vem se consolidando na prática:

- **Transfer (control handoff / routing)**: um agente **entrega o controle** da conversa para outro agente, e o novo agente passa a ser o *owner* do loop de interação.
- **Delegate (agents-as-tools / subroutine)**: um agente **mantém o controle**, mas “chama” outro agente como se fosse uma tool/subrotina e **espera um resultado** tipado (I/O bem definido).

Em termos de engenharia de contexto: **Transfer** tende a mover *histórico*; **Delegate** tende a mover *payload* (entradas/saídas estruturadas) e manter o histórico “sagrado” com o orquestrador.

### 1.1 Tabela de comparação (implementação‑orientada)

| Dimensão | **Transfer (handoff de controle)** | **Delegate (chamada de agente como tool)** |
|---|---|---|
| Intenção | mudar o “dono” da conversa | resolver uma subtarefa sem mudar o dono |
| Forma típica | *tool* `transfer_to_<agent>` / `transfer_to_agent(...)` | *tool* do agente especialista (`<agent>_expert`) ou “AgentTool” |
| Contexto movido | histórico **full** ou **filtrado** (recency + state + anexos) | **task payload** + *context digest* + constraints (mínimo necessário) |
| Saída | resposta conversacional do agente “destino” | resultado **tipado/estruturado** que o orquestrador integra |
| Segurança | maior risco de vazamento (histórico carregado) → exige filters | menor risco (least privilege por payload) → mais controlável |
| Token/custo | pode explodir se você “passa tudo” | geralmente mais barato (I/O curto + retorno resumido) |
| Quando brilha | suporte/triagem, UX “fala com especialista”, roteamento | análise, verificação, execução de tarefas, workers paralelos |

> **Regra prática:** **Delegate‑first** para performance/custo/controle; **Transfer** quando a UX exige que o especialista converse diretamente, ou quando a “identidade” do agente muda (ex.: suporte → billing).

---

## 2) Como esses padrões aparecem nos vendors/frameworks

### 2.1 OpenAI Agents SDK

O próprio Agents SDK descreve dois padrões recorrentes de multi‑agente:

1) **Manager (agents as tools)**: um “customer‑facing agent” chama especialistas como tools e mantém o controle da conversa.
2) **Handoffs**: agentes pares transferem o controle para um especialista que passa a “tomar a conversa”.[^openai_agents_design_patterns]

#### Transfer em OpenAI (Handoffs)
- No Agents SDK, **handoffs são representados como tools** para o modelo; o nome padrão do tool é `transfer_to_{agent_name}`.[^openai_agents_handoffs_tools]
- O SDK fornece **input filters** para controlar o que do histórico é passado ao agente destino (ex.: remover tool dumps, remover PII, manter só `STATE_JSON`).[^openai_agents_handoffs_input_filters]
- Há suporte a **nested handoffs** (beta/opt‑in) para reduzir bloat e manter legibilidade quando há várias transferências em sequência.[^openai_agents_handoffs_nested]

**Implicação de contexto:** se você usa Transfer com histórico full, você precisa obrigatoriamente de:
- `handoff_input_filter` (ou equivalente) 
- budgets por slice (para recency, state e tool results)
- “handoff package” com state estruturado + ponteiros

#### Delegate em OpenAI (Manager / agents-as-tools)
- Especialistas são expostos como tools via algo como `booking_agent.as_tool(...)`, e o agente principal mantém o loop.[^openai_agents_design_patterns]

**Implicação de contexto:** o contrato de tool deve ser:
- **tipado** (structured outputs quando fizer sentido)
- com **payload mínimo** (não passe transcript)
- com **retorno resumido** (digest + ponteiros)

> **Tradução do screenshot para OpenAI:** `transfer_to_<agent>` = Handoffs (Transfer). “delegate_to_agent” = Manager chamando especialistas como tools (não necessariamente com esse nome literal).

---

### 2.2 Google ADK (Agent Development Kit)

O ADK nomeia explicitamente os dois mecanismos:

- **LLM‑Driven Delegation (Agent Transfer)**: o LLM “roteia” e usa `transfer_to_agent(agent_name=...)` para passar controle.[^google_adk_multi_agents_transfer]
- **Explicit Invocation (AgentTool)**: o agente “pai” chama um agente “filho” como tool via `AgentTool`, que executa o agente e devolve o resultado como tool result.[^google_adk_multi_agents_agenttool]

> Isso é quase uma correspondência 1:1 com Transfer vs Delegate.

O ADK também diferencia esses mecanismos de um terceiro padrão comum:
- **Sequential Pipeline** (workflow agent): os agentes rodam em sequência compartilhando estado, sem “transfer” conversacional.[^google_adk_multi_agents_pipelines]

---

### 2.3 LangGraph / LangChain (handoffs, supervisor, message forwarding)

No ecossistema LangGraph/LangChain:

- “**Handoff**” aparece como um **padrão de roteamento** (muitas vezes implementado como uma tool cujo efeito é mudar o próximo nó/agent a executar). O próprio LangChain observa que o termo *handoff* foi cunhado pela OpenAI.[^langgraph_handoffs_term]

- O time do LangChain publicou resultados mostrando que o design do supervisor/handoffs **impacta performance** e **bloat de contexto**. Em particular, eles testaram tool naming do tipo `delegate_to_<agent>` vs `transfer_to_<agent>` e mudaram o supervisor para reduzir/evitar mensagens de handoff no histórico e melhorar qualidade.[^langchain_benchmarking_multi_agent]

**Implicação de contexto:** em grafos, Transfer/Delegate é, no fundo, uma decisão de:
- **qual estado** passa entre nós,
- **quais mensagens** entram no contexto do nó,
- e **quais eventos** ficam só no log/tracing.

---

### 2.4 Anthropic Claude Code (subagents)

No Claude Code, “subagents” são descritos como agentes especializados que rodam **em sua própria janela de contexto**, com prompt e permissões próprias; Claude “delega” tarefas para eles e recebe resultados.[^anthropic_claude_code_subagents]

Isso é uma forma forte de **Delegate**, com dois efeitos relevantes:
- **Isolamento de contexto**: exploração pesada não polui o thread principal.
- **Compaction independente**: o subagent pode compactar/limpar seu próprio histórico sem afetar o principal.[^anthropic_claude_code_subagents]

---

## 3) O que estava (e não estava) contemplado no nosso pack

### Já contemplado
- O pack já tinha **Manager pattern** e **Handoffs** como conceitos em `10_MULTI_AGENT.md`.

### Gap (endereço neste update)
O pack **não explicitava** a leitura “dual handoff” (Transfer vs Delegate) como:
- decisão de *modo de handoff*;
- contrato técnico (schemas) diferente por modo;
- implicações de budgeting e observabilidade por modo;
- mapeamento 1:1 com ADK (transfer_to_agent vs AgentTool) e com o vocabulário recente do LangChain (delegate_to vs transfer_to).

Este doc (10A) fecha esse gap e adiciona templates + exemplos.

---

## 4) Guia de decisão: quando usar Transfer vs Delegate

### 4.1 Heurística simples (boa o bastante para produção)

**Use Delegate quando:**
- você quer **controle central** (resposta final sempre do orquestrador);
- você precisa de **least privilege** (passar só o necessário);
- a subtarefa tem **I/O bem definido** (ex.: “resuma X”, “valide Y”, “gere Z”);
- você quer **paralelismo** (fan‑out para N workers) sem duplicar todo o histórico.

**Use Transfer quando:**
- a UX exige que o especialista **converse diretamente** com o usuário;
- o especialista precisa fazer **múltiplos turnos de clarificação** sem o manager no meio;
- você quer um “novo modo”/persona (ex.: triagem → billing).

### 4.2 Trade‑offs de contexto e custo (o que de fato muda)

- **Transfer** cria o risco clássico de *“histórico como payload”*: custos e vazamentos.
- **Delegate** cria o risco clássico de *“subtarefa mal especificada”*: se o payload não contém constraints, o worker erra.

> **SOTA operacional:** mantenha **STATE_JSON** e **EVIDENCE_PACK** como fonte de verdade; a conversa (transcript) vira uma fonte “soft” para recency. Isso reduz o impacto de ambos.

---

## 5) Contratos de comunicação: schemas recomendados

Abaixo um contrato único que cobre os dois modos, com campos opcionais por modo.

### 5.1 `handoff_contract_v2` (framework‑agnóstico)

```json
{
  "schema_version": "handoff_contract_v2",
  "handoff_mode": "delegate",
  "handoff_id": "hndf_...",
  "from_agent": "orchestrator",
  "to_agent": "code_review",

  "objective": "...",
  "constraints": ["..."],

  "state": {
    "decisions": [],
    "facts": [],
    "preferences": [],
    "todos": []
  },

  "context_policy": {
    "history_mode": "filtered",
    "max_history_tokens": 12000,
    "include_slices": ["STATE_JSON", "RECENT_DIALOG", "EVIDENCE_REFS"],
    "exclude_slices": ["RAW_TOOL_DUMPS"],
    "redaction": {
      "pii": true,
      "secrets": true
    }
  },

  "delegate_io": {
    "input": {
      "task": "review this diff for security issues",
      "artifacts": [{"uri": "s3://.../diff.patch", "sha256": "..."}],
      "context_digest": "...",
      "expected_output_schema": "review_findings_v1"
    },
    "output": null
  },

  "evidence_refs": [{"id": "src_1", "uri": "...", "citation": "..."}],
  "budget_hint": {"max_input_tokens": 40000, "priority": "high"},

  "observability": {
    "trace_id": "...",
    "span_id": "...",
    "token_ledger_snapshot": {
      "state": 1200,
      "history": 8000,
      "tools": 14000,
      "rag": 6000
    }
  }
}
```

### 5.2 Regras de preenchimento

- **Transfer**: `handoff_mode="transfer"` e `context_policy.history_mode` tende a ser `full|filtered|summary|pointer`.
- **Delegate**: `handoff_mode="delegate"` e `delegate_io.input` deve ser obrigatório (payload mínimo + output schema).

---

## 6) Context management específico por padrão

### 6.1 Transfer: monte um “Context Pack” (não passe transcript cru)

Checklist:
1) **STATE_JSON** (decisions/constraints/todos) sempre entra.
2) **Recency** por tokens (não por turnos).
3) Tool dumps **não** entram: entram *digests* e ponteiros.
4) Aplique **handoff input filters** (vendor) ou o equivalente.
5) Em cadeias de transferências: use **nested handoff history** (quando disponível) + sumarização hierárquica.

> Se você usa Transfer sem filtros, você inevitavelmente vira refém de: bloat + vazamento + “prompt injection por tool output”.

### 6.2 Delegate: “subrotina com contrato”

Checklist:
1) Defina **schema de entrada** (task + constraints + artefatos + context digest).
2) Defina **schema de saída** (structured output) sempre que a saída alimentar decisão downstream.
3) Exija que o worker retorne:
   - findings (curtos)
   - evidência (refs)
   - ponteiros para detalhes (raw logs)
4) Faça o orquestrador registrar no **STATE_JSON** apenas o que virou decisão.

> Delegate é onde você ganha *determinismo* e *custos previsíveis*.

---

## 7) Observabilidade: o que medir por modo

Métricas mínimas:
- `handoff_mode` (transfer/delegate)
- `handoff_count_per_task`
- `handoff_context_tokens` (quantos tokens foram *enviados* no pack)
- `handoff_latency_ms`
- `delegate_output_tokens` vs `delegate_payload_tokens`
- `handoff_failure_rate` (tool errors, parsing errors, “wrong agent selected”)
- `constraint_loss_rate` (offline eval: constraints que sumiram após handoff)

> Para tuning: compare *“delegate-first”* vs *“transfer-first”* por tarefa (A/B), mantendo budgets constantes.

---

## 8) Referências (primárias e complementares)

[^openai_agents_design_patterns]: OpenAI Agents SDK (Python), “Agents — Multi-agent system design patterns (Manager as tools, Handoffs)”, **date not found**, https://openai.github.io/openai-agents-python/agents/

[^openai_agents_handoffs_tools]: OpenAI Agents SDK (Python), “Handoffs — Handoffs are represented as tools… tool name `transfer_to_{agent_name}`”, **date not found**, https://openai.github.io/openai-agents-python/handoffs/

[^openai_agents_handoffs_input_filters]: OpenAI Agents SDK, “Handoffs — Input filters / Handoff filters”, **date not found**, https://openai.github.io/openai-agents-python/handoffs/

[^openai_agents_handoffs_nested]: OpenAI Agents SDK, “Handoffs — nested handoffs history (opt‑in beta)”, **date not found**, https://openai.github.io/openai-agents-python/handoffs/

[^google_adk_multi_agents_transfer]: Google ADK Docs, “Multi-agent systems — LLM‑Driven Delegation (Agent Transfer) / `transfer_to_agent`”, **date not found**, https://google.github.io/adk-docs/agents/multi-agents/

[^google_adk_multi_agents_agenttool]: Google ADK Docs, “Multi-agent systems — Explicit Invocation (`AgentTool`)”, **date not found**, https://google.github.io/adk-docs/agents/multi-agents/

[^google_adk_multi_agents_pipelines]: Google ADK Docs, “Multi-agent systems — Workflow agents / Sequential pipeline”, **date not found**, https://google.github.io/adk-docs/agents/multi-agents/

[^langgraph_handoffs_term]: LangChain Docs, “Multi-agent — Handoffs (term coined by OpenAI)”, **date not found**, https://python.langchain.com/docs/how_to/multi_agent/

[^langchain_benchmarking_multi_agent]: LangChain Blog, “Benchmarking Multi-agent Architectures”, **Jun 10, 2025**, https://blog.langchain.dev/benchmarking-multi-agent-architectures/

[^anthropic_claude_code_subagents]: Anthropic Claude Code Docs, “Create custom subagents (each runs in its own context window; delegation; compaction)”, **date not found**, https://code.claude.com/docs/en/sub-agents


[^wooldridge_mas_book]: Michael Wooldridge, “An Introduction to MultiAgent Systems (2nd Edition)”, John Wiley & Sons, **May 2009**, https://dev.store.wiley.com/en-gb/An%2BIntroduction%2Bto%2BMultiAgent%2BSystems%2C%2B2nd%2BEdition-p-9780470519462

[^shoham_leyton_brown_book]: Yoav Shoham & Kevin Leyton-Brown, “Multiagent Systems: Algorithmic, Game-Theoretic, and Logical Foundations”, Cambridge University Press, **2009** (ver também: print 15 Dec 2008 / online 05 Jun 2012), https://www.cambridge.org/core/books/multiagent-systems/B11B69E0CB9032D6EC0A254F59922360
