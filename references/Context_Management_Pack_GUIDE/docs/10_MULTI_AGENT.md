# 10 — Multi‑agent: contexto numa rede de agentes (manager, handoffs, especialistas)

> Este doc descreve **como particionar, transferir e compartilhar contexto** quando você tem mais de um agente. Para a distinção “Dual handoff” (**Transfer vs Delegate**), veja também **`10A_DUAL_HANDOFF_TRANSFER_VS_DELEGATE.md`**.

---

## 10.1 Por que multi‑agent explode contexto (e como evitar)

Em multi‑agent, o custo não cresce linearmente:

- Você pode duplicar o mesmo histórico N vezes (1 por worker).
- Handoffs em cadeia geram “metade do contexto” que é apenas logística.
- Tool results e RAG podem vazar para agentes que não precisam ver aquilo.

**Regra SOTA:** cada agente recebe um **context pack mínimo** para cumprir seu papel; a orquestração mantém uma **fonte de verdade estruturada** (STATE) e um **ledger de tokens**.

---

## 10.2 Dois modos que coexistem: Transfer vs Delegate

Os vendors/frameworks modernos convergem para dois modos principais (descritos em detalhe no doc 10A):

- **Transfer (handoff de controle)**: muda o “dono” da conversa.
- **Delegate (agents-as-tools / subrotina)**: o orquestrador chama um especialista como tool e integra a saída.

O OpenAI Agents SDK documenta explicitamente ambos como “Manager (agents as tools)” e “Handoffs”.[^openai_agents_design_patterns]
O Google ADK também: “LLM‑Driven Delegation (Agent Transfer)” e “Explicit Invocation (AgentTool)”.[^google_adk_multi_agents_transfer][^google_adk_multi_agents_agenttool]

**Heurística prática:** *delegate-first* (controle central, I/O tipado) e use *transfer* quando a UX exige que o especialista converse diretamente.

---

## 10.3 Padrões de arquitetura multi‑agente

### A) Manager pattern (agents-as-tools)

**Como funciona:**
- Um “manager” (ou “customer-facing agent”) mantém o diálogo com o usuário.
- Especialistas são expostos como **tools** (agentes chamáveis).

No OpenAI Agents SDK, isso aparece como o padrão “Manager (agents as tools)”, com especialistas expostos via `agent.as_tool(...)`.[^openai_agents_design_patterns]
No Google ADK, isso aparece como “Explicit Invocation (AgentTool)”.[^google_adk_multi_agents_agenttool]

**Contexto recomendado (pack do worker):**
- payload de tarefa (tipado)
- constraints relevantes
- `STATE_JSON` mínimo necessário (não o transcript)
- ponteiros para artefatos (diff, docs, logs) 

**Benefícios:**
- custo previsível (payload curto)
- melhor segurança (least privilege)
- bom para paralelismo (fan‑out)

**Riscos:**
- subtarefa mal especificada → worker erra ou diverge

**Mitigação:**
- contratos formais (schemas)
- outputs estruturados + validação


### B) Decentralized / Peer Handoffs (Transfer)

**Como funciona:**
- Um agente “roteador” transfere o controle para um especialista.
- O especialista recebe histórico e “assume a conversa”.

No OpenAI Agents SDK:
- handoffs viram tools com nome padrão `transfer_to_{agent_name}`.[^openai_agents_handoffs_tools]
- há **input filters** para controlar que partes do histórico passam ao destino.[^openai_agents_handoffs_input_filters]
- há suporte a **nested handoffs** (beta/opt-in) para reduzir bloat em cadeias longas.[^openai_agents_handoffs_nested]

No Google ADK:
- o roteamento usa `transfer_to_agent(agent_name=...)`.[^google_adk_multi_agents_transfer]

**Contexto recomendado (pack do destino):**
- `STATE_JSON` completo
- recency por tokens (somente o necessário)
- digests + pointers de tools/RAG (não dumps)

**Benefícios:**
- UX natural (“agora você está com o especialista”)
- bom para suporte/triagem

**Riscos:**
- **bloat** de histórico
- vazamento de dados e tool outputs

**Mitigação:**
- input filters
- quotas por slice
- separar “untrusted data” do que é instrução


### C) Workflow/pipeline (sem handoff conversacional)

Um terceiro padrão comum (às vezes confundido com handoff) é pipeline/workflow:
- agentes executam em sequência (ou em fan‑out/gather) compartilhando estado, mas sem “passar o controle conversacional”.

Ex.: no ADK, `SequentialAgent` executa sub‑agentes em ordem compartilhando `session.state`.[^google_adk_multi_agents_pipelines]

**Contexto recomendado:**
- usar `state` como meio de troca
- manter mensagens de “controle” fora do transcript

---

## 10.4 Contratos de comunicação entre agentes (handoff package)

A forma mais robusta de evitar duplicação e drift é padronizar comunicação.

- Para **Transfer**: um “handoff package” com `context_policy` e histórico filtrado.
- Para **Delegate**: um “delegation request” com I/O tipado.

Veja o template `templates/handoff_contract_schema_v2.json` e o doc 10A.

---

## 10.5 Shared state e “shared memory” sem duplicar contexto

### Opção 1 — Blackboard (STATE_JSON)
- Estrutura tipada: DECISIONS / FACTS / PREFERENCES / TODOS.
- Atualização apenas quando algo vira decisão.

### Opção 2 — Event log (tracing) + rehidratação
- O transcript completo vira log/audit trail.
- O contexto do agente recebe apenas o que precisa (via assembler).

### Opção 3 — Retrieval‑backed shared memory
- Armazene artefatos e interações como um corpus.
- Reinjete apenas snippets relevantes (com quotas e citações).

---

## 10.6 Evitando “context bloat” entre agentes

Anti‑padrões:
1. **Replicar o mesmo transcript para todos os workers**.
2. **Passar tool dumps** para agentes que só precisam de um digest.
3. **Handoffs em cadeia** sem nesting/compaction.

Evidência de campo: o time do LangChain reportou que mudanças na arquitetura do supervisor/handoffs (incluindo naming `delegate_to_<agent>` vs `transfer_to_<agent>` e redução de mensagens de handoff) impactam performance e bloat.[^langchain_benchmarking_multi_agent]

---

## 10.7 Observabilidade mínima (multi‑agent)

Métricas recomendadas:
- `handoff_mode` (transfer/delegate)
- tokens por agent run e por slice
- `handoff_count`, `handoff_chain_depth`
- latência e taxa de erro por agente
- “lost constraints” pós-handoff (offline eval)

(Detalhes em `11_OBSERVABILIDADE_E_GOVERNANCA.md`.)

---

## Referências

[^openai_agents_design_patterns]: OpenAI Agents SDK (Python), “Agents — Multi-agent system design patterns (Manager as tools, Handoffs)”, **date not found**, https://openai.github.io/openai-agents-python/agents/

[^openai_agents_handoffs_tools]: OpenAI Agents SDK (Python), “Handoffs — Handoffs are represented as tools… tool name `transfer_to_{agent_name}`”, **date not found**, https://openai.github.io/openai-agents-python/handoffs/

[^openai_agents_handoffs_input_filters]: OpenAI Agents SDK, “Handoffs — Input filters / Handoff filters”, **date not found**, https://openai.github.io/openai-agents-python/handoffs/

[^openai_agents_handoffs_nested]: OpenAI Agents SDK, “Handoffs — nested handoffs history (opt‑in beta)”, **date not found**, https://openai.github.io/openai-agents-python/handoffs/

[^google_adk_multi_agents_transfer]: Google ADK Docs, “Multi-agent systems — LLM‑Driven Delegation (Agent Transfer) / `transfer_to_agent`”, **date not found**, https://google.github.io/adk-docs/agents/multi-agents/

[^google_adk_multi_agents_agenttool]: Google ADK Docs, “Multi-agent systems — Explicit Invocation (`AgentTool`)”, **date not found**, https://google.github.io/adk-docs/agents/multi-agents/

[^google_adk_multi_agents_pipelines]: Google ADK Docs, “Multi-agent systems — Workflow agents / Sequential pipeline”, **date not found**, https://google.github.io/adk-docs/agents/multi-agents/

[^langchain_benchmarking_multi_agent]: LangChain Blog, “Benchmarking Multi-agent Architectures”, **Jun 10, 2025**, https://blog.langchain.dev/benchmarking-multi-agent-architectures/

