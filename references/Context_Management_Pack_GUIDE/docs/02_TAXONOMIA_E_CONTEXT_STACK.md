# 02 — Glossário, Taxonomia e Context Stack

## Glossário (definições operacionais)

> Definições focadas em engenharia: “o que é” + “para que serve” + “onde mora” no pipeline.

### System prompt
Instruções de **maior prioridade** (chain-of-command) que definem comportamento, limites e estilo do agente. Em muitos vendors, é um campo separado (`system`/`instructions`) ou mensagem com role `system`.[^openai_model_spec]

**Regra prática:** manter curto, estável e auditável. Idealmente cacheável.

### Developer prompt
Camada de instruções do **desenvolvedor/orquestrador**, abaixo do system e acima do usuário (ex.: regras de saída, schemas, definições do produto). Em OpenAI pode existir como role `developer` (ou como `instructions`/prefixo).[^openai_model_spec]

### Conversation history
Sequência de pares user/assistant + tool interactions que compõem o “transcript”. **Não** é sinônimo de “contexto”: em SOTA, histórico é uma fonte que será **composta, resumida e fatiada**.

### Tool schema
Definição formal de uma ferramenta: `name`, `description`, `parameters` (JSON Schema ou equivalente) + restrições (idempotência, side effects, auth, approvals).[^openai_function_calling][^anthropic_tool_use][^google_function_calling]

### Tool result
Payload retornado por uma ferramenta (resultado de API/DB/código). **Sempre tratar como untrusted data** (pode conter instruções maliciosas ou dados irrelevantes).

### RAG (Retrieval‑Augmented Generation)
Arquitetura que injeta no contexto **evidência recuperada** (docs/trechos) para responder com fidelidade. Em SOTA, RAG vira um **Evidence Pack** com snippets, metadados e citações.

### Working memory
Memória de curto prazo, específica do **turno/tarefa atual** (ex.: variáveis de execução, resultados temporários). Idealmente vive como `STATE_JSON` no contexto + armazenamento de runtime.

### Durable memory
Memória persistente (cross‑turn / cross‑session) como decisões, preferências e fatos do usuário. Em SOTA: **schema explícito + TTL + privacidade**. Pode ser DB, store, “memory bank”, etc.[^google_adk_memory]

### Summarization / compaction
- **Summarization:** compressão textual/estrutural produzida pelo seu sistema (ou pelo modelo) para reduzir tokens mantendo invariantes e decisões.
- **Compaction:** forma “sistêmica” de compressão suportada por alguns vendors (ex.: endpoint específico) que retorna uma janela compactada canônica.[^openai_compaction][^anthropic_compaction]

### Handoff package
Contrato de transferência de contexto entre agentes (manager→worker ou peer→peer). Deve ser **estruturado (JSON)** e conter objetivo, constraints, evidência e artefatos (com pointers).

### Skills registry
Catálogo modular de “processos codificados” (skills), tipicamente versionado e carregado on‑demand. OpenAI define “Skills” com `SKILL.md` e compatibilidade com um padrão aberto.[^openai_skills]

### Context budget
Orçamento de tokens por slice (ou por camada) para montar a janela final.

### Context window
Limite total de tokens que o modelo aceita como entrada (somando mensagens, tools, etc). **Não assuma números fixos**: trate como capability do modelo/config.

### Context assembly pipeline
Pipeline determinístico que pega fontes (system/dev/história/tools/RAG/memória) e produz a **janela final** dentro do orçamento: seleção → compressão → validação → ordenação.

---

## Taxonomia: o “stack” de contexto (camadas)

### Diagrama (camadas do mais prioritário para o menos prioritário)

```mermaid
flowchart TB
  A[System / Safety / Policy
(estável, curto, cacheável)] --> B[Developer / Product contract
(output schema, tone, do/don't)]
  B --> C[Skills Index
(metadados curtos)]
  C --> D[Active Skills
(apenas as selecionadas)]
  D --> E[STATE_JSON
(decisions, constraints, todos, plan vars)]
  E --> F[Recency Window
(últimos turnos por tokens)]
  F --> G[History Summary
(prefixo hierárquico)]
  G --> H[RAG Evidence Pack
(snippets+metadados+citações)]
  H --> I[Tool Context
(schemas + policies)]
  I --> J[Tool Results
(digest + pointers)]
  J --> K[Attachments / Files
(pointers, não dumps)]
```

### Por que essa ordem funciona
- Coloca invariantes (política/contratos) primeiro.
- Separa “metadados” (skills index) do corpo grande (skills selecionadas).
- Força **estado estruturado** antes do transcript.
- Mantém RAG como evidência “abaixo” do estado e das instruções, reduzindo risco de instruções maliciosas competirem com o system/dev.

---

## Diferenças importantes por vendor (OpenAI vs Anthropic vs Google)

> Objetivo: você integrar o mesmo “context assembly pipeline” independentemente do vendor, trocando apenas o **adapter** de serialização (roles/blocks).

### OpenAI (Responses API / Agents SDK)
- Suporta **roles** como `system`, `developer`, `user`, `assistant`, `tool` (e itens estruturados na Responses API).[^openai_model_spec][^openai_function_calling]
- Continuidade de conversa pode ser feita via `previous_response_id` (reduz reenvio de histórico, quando aplicável).[^openai_conversation_state]
- Possui endpoint de **compaction** (`/responses/compact`) que retorna uma janela compactada canônica e um item de compaction opaco.[^openai_compaction]
- Fornece **Skills** (bundles versionados) e **MCP connectors** na camada de tools, com políticas de aprovação (`require_approval`).[^openai_skills][^openai_connectors_mcp]

### Anthropic (Messages API / Claude Agent SDK)
- Estrutura típica: mensagens `user`/`assistant`; tool calls e tool results são **content blocks** (`tool_use`, `tool_result`) e obedecem regras de formatação/ordem.[^anthropic_tool_use]
- Oferece **prompt caching** e **context management** (compaction/context editing) na plataforma Claude.[^anthropic_prompt_caching][^anthropic_compaction]
- O Claude Agent SDK enfatiza loops com ferramentas, memória e orchestration, com práticas emergentes de produção.[^anthropic_agent_sdk]

### Google (Gemini/Vertex AI + ADK)
- No ADK, “context” inclui bundle de infos disponível ao agente e tools; há **state** mutável e artefatos que podem ser carregados/salvos.[^google_adk_context]
- ADK introduz MemoryService (in‑memory ou Vertex AI Memory Bank) com ferramentas como `PreloadMemory` e `LoadMemory`.[^google_adk_memory]
- Gemini/Vertex suportam function calling e structured output; o formato é diferente (parts / functionCall / functionResponse), exigindo adapter.[^google_function_calling][^google_structured_output]
- Context caching existe no ecossistema Gemini (útil para prefixos estáticos), mas a capacidade varia por produto/modelo.[^google_context_caching]

---

## Confiança & limitações
- Este documento descreve **padrões** e “shapes” de APIs; detalhes de payload variam por SDK/versão. Sempre trate recursos como **capability flags**.
- Onde não há data explícita na doc do vendor, marcamos “date not found” (menor confiança).

---

## Referências
[^openai_model_spec]: OpenAI, “Model Spec”, **date not found**, https://model-spec.openai.com/
[^openai_function_calling]: OpenAI API Docs, “Function calling”, **date not found**, https://platform.openai.com/docs/guides/function-calling
[^openai_conversation_state]: OpenAI API Docs, “Conversation state”, **date not found**, https://developers.openai.com/api/docs/guides/conversation-state
[^openai_compaction]: OpenAI API Docs, “Compaction”, **date not found**, https://developers.openai.com/api/docs/guides/compaction
[^openai_skills]: OpenAI API Docs, “Skills”, **date not found**, https://developers.openai.com/api/docs/guides/tools-skills
[^openai_connectors_mcp]: OpenAI API Docs, “Connectors and MCP servers”, **date not found**, https://developers.openai.com/api/docs/guides/tools-connectors-mcp
[^anthropic_tool_use]: Claude API Docs, “How to implement tool use”, **date not found**, https://platform.claude.com/docs/en/build-with-claude/tool-use
[^anthropic_prompt_caching]: Claude API Docs, “Prompt caching”, **date not found**, https://platform.claude.com/docs/en/build-with-claude/prompt-caching
[^anthropic_compaction]: Claude API Docs, “Compaction”, **date not found**, https://platform.claude.com/docs/en/build-with-claude/compaction
[^anthropic_agent_sdk]: Anthropic Engineering, “Building agents with the Claude Agent SDK”, **Published Sep 29, 2025**, https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk
[^google_adk_context]: Google ADK Docs, “Context”, **date not found**, https://google.github.io/adk-docs/context/
[^google_adk_memory]: Google ADK Docs, “Memory”, **date not found**, https://google.github.io/adk-docs/sessions/memory/
[^google_function_calling]: Google, “Function calling (Gemini API)”, **date not found**, https://ai.google.dev/gemini-api/docs/function-calling
[^google_structured_output]: Google, “Structured output (Gemini API)”, **date not found**, https://ai.google.dev/gemini-api/docs/structured-output
[^google_context_caching]: Google, “Context caching (Gemini API)”, **date not found**, https://ai.google.dev/gemini-api/docs/caching
