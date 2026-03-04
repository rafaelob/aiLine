# 01 — Estado da Arte (SOTA) em Context Management para Agentes LLM (2026)

## O que “SOTA” significa aqui

Em agentes LLM, “estado da arte” **não** é apenas aumentar o contexto. É tratar contexto como um **recurso finito com retornos decrescentes** (atenção/qualidade) e operar um **pipeline de montagem** que seleciona, comprime e valida o que entra na janela a cada passo.

Anthropic popularizou essa visão ao descrever **context rot** e “attention budget”: conforme o contexto cresce, a capacidade do modelo de recuperar/usar informação do meio do contexto tende a degradar, exigindo curadoria e compressão deliberadas.[^anthropic_context_engineering]

Em paralelo, o ecossistema de vendors e frameworks evoluiu com:
- **APIs de compaction** (reduzir o histórico mantendo estado essencial).[^openai_compaction][^anthropic_compaction]
- **Prompt caching** (reusar prefixos estáticos para reduzir custo/latência).[^openai_prompt_caching][^anthropic_prompt_caching]
- **Sistemas de “conversation state” / continuidade** para reduzir reenvio de histórico (ex.: `previous_response_id` na Responses API).[^openai_conversation_state]
- **Padrões de interoperabilidade de ferramentas** (MCP) e controles de consentimento/aprovação.[^mcp_spec][^openai_connectors_mcp]
- **Memória gerenciada** (ex.: ADK/Vertex Memory Bank) e ferramentas de preload/load.[^google_adk_memory]
- **Tracing/evals** de ponta a ponta para observabilidade (não “prompt superstition”).[^openai_trace_grading]

---

## As 10 teses SOTA (práticas) para o seu contexto (350k, multi‑agentes, tool‑heavy)

1. **Contexto = stack tipado + orçamento por camada (tokens), não transcript.**  
   Você precisa de um “context assembler” que monta a janela final com quotas por slice (instructions, state, history, tools, RAG…).

2. **Budgets são parametrizáveis por orquestração, não globais.**  
   “200k core + 150k tools” é um perfil, não uma lei. Diferentes workflows exigem redistribuição (tool‑heavy vs RAG‑heavy vs chatty). Veja `docs/04_PROFILES_DE_ORCAMENTO.md`.

3. **O “núcleo” (instruções + políticas + estado) deve ser pequeno e estável — e cacheável.**  
   Mantenha o prefixo estático (system/dev + registry de ferramentas/skills) curto o bastante para caber sempre e ativar caching quando disponível.[^openai_prompt_caching]

4. **Histórico deve ser mantido por *limite de tokens*, com sumarização hierárquica + estado estruturado.**  
   “Últimos 10 turnos” é uma heurística fraca. O correto é “últimos X tokens de turnos + sumário prefixo + STATE_JSON”.

5. **Resultados de ferramentas e RAG são os maiores vilões de contexto — então têm que ser *desenhados* para token efficiency.**  
   Otimize ferramentas com paginação, filtros e modos “concise vs detailed”.[^anthropic_tools]  
   Reinjete **digest + pointer**, não dumps.

6. **RAG precisa virar “Evidence Pack” (snippets + metadados + citações), não “colar tudo”.**  
   Recuperação sem compressão, proveniência e checagem de fé vira bloat e alucinação.

7. **Trate outputs de ferramentas/RAG como *untrusted input*.**  
   Tool outputs podem conter prompt injection; o modelo deve ser instruído a não obedecer a instruções vindas de dados.[^mcp_spec][^openai_agent_safety][^openai_skills]

8. **Use compaction quando disponível — mas como parte do pipeline, com gates e telemetria.**  
   OpenAI descreve `/responses/compact` retornando um item de compaction “opaco” que deve ser reaplicado como janela canônica.[^openai_compaction]

9. **Multi‑agente exige partição de contexto por papel (role packs) e contratos de handoff.**  
   Duplicar background em todos os agentes explode qualquer janela (mesmo 350k). Use **dual handoff** (delegate vs transfer), handoff contract JSON e shared state retrieval-backed (ver `10A_DUAL_HANDOFF_TRANSFER_VS_DELEGATE.md`).

10. **Sem observabilidade, não existe “melhor estratégia”: existe mito.**  
   Token ledger por slice, tracing, taxas de compaction, drift de sumário e “lost constraints” precisam virar métricas (ver `docs/11_OBSERVABILIDADE_E_GOVERNANCA.md`).[^openai_token_counting][^openai_trace_grading][^google_adk_context]

---

## O que eu mudaria no seu approach atual (200k core, 150k tools, summariza só chat antigo)

Seu modelo atual é um bom começo, mas tem dois gargalos clássicos:

### Gargalo A — “core” muito amplo e rígido
- Mistura invariantes (política), semi‑invariantes (skills) e voláteis (orquestração e turnos) num pacote só.
- Resultado: quando muda o tipo de tarefa, você não consegue “realocar” tokens.

**SOTA:** transformar o core em **fatias** com *min/max* e habilitar perfis por workload:
- `SYSTEM+DEV` (mínimo, estável, cacheável)
- `SKILLS_INDEX` (metadados curtos)
- `SKILLS_ACTIVE` (somente as skills selecionadas no passo)
- `STATE_JSON` (decisões/constraints/todos)
- `HISTORY_VERBATIM` (janela recency)
- `HISTORY_SUMMARY` (prefixo hierárquico)

### Gargalo B — tool/RAG sem controles fortes de forma
Se você só compacta o chat e deixa tool outputs crescerem, você vai saturar “Y” de qualquer forma.

**SOTA:** “tool/result budgets” por categoria + output shaping:
- “concise by default”
- paginação
- projeção de schema
- digests com ponteiros
- sumarização segura e rastreável

---

## Confiança & limitações (importante)

- Vendors mudam rápido: **não assuma** tamanhos de janela, defaults, limites de caching/compaction sem validar no seu ambiente. Onde a documentação não traz data explícita, marcamos como **date not found** (menor confiança).
- Algumas features (ex.: compaction, prompt caching, memory services) podem ter **comportamento/modelos suportados** diferentes por região/produto. Trate como *capability flags*.
- Mesmo com janelas muito grandes, “context rot” e “lost in the middle” continuam relevantes — logo **curadoria e ordenação** permanecem essenciais.[^anthropic_context_engineering]

---

## Referências (seleção)
As referências completas estão em `docs/15_MAPA_DE_FONTES.md`.

[^anthropic_context_engineering]: Anthropic Engineering, “Effective context engineering for AI agents”, **Published Sep 29, 2025**, https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
[^anthropic_tools]: Anthropic Engineering, “Writing effective tools for agents — with agents”, **Published Sep 11, 2025**, https://www.anthropic.com/engineering/writing-tools-for-agents
[^openai_prompt_caching]: OpenAI API Docs, “Prompt caching”, **date not found**, https://developers.openai.com/api/docs/guides/prompt-caching
[^openai_compaction]: OpenAI API Docs, “Compaction”, **date not found**, https://developers.openai.com/api/docs/guides/compaction
[^openai_conversation_state]: OpenAI API Docs, “Conversation state”, **date not found**, https://developers.openai.com/api/docs/guides/conversation-state
[^openai_token_counting]: OpenAI API Docs, “Counting tokens”, **date not found**, https://developers.openai.com/api/docs/guides/token-counting
[^openai_skills]: OpenAI API Docs, “Skills”, **date not found**, https://developers.openai.com/api/docs/guides/tools-skills
[^openai_connectors_mcp]: OpenAI API Docs, “Connectors and MCP servers”, **date not found**, https://developers.openai.com/api/docs/guides/tools-connectors-mcp
[^openai_agent_safety]: OpenAI API Docs, “Safety in building agents”, **date not found**, https://developers.openai.com/api/docs/guides/agent-builder-safety
[^openai_trace_grading]: OpenAI API Docs, “Trace grading”, **date not found**, https://developers.openai.com/api/docs/guides/trace-grading
[^anthropic_compaction]: Claude API Docs, “Compaction”, **date not found**, https://platform.claude.com/docs/en/build-with-claude/compaction
[^anthropic_prompt_caching]: Claude API Docs, “Prompt caching”, **date not found**, https://platform.claude.com/docs/en/build-with-claude/prompt-caching
[^google_adk_context]: Google ADK Docs, “Context”, **date not found**, https://google.github.io/adk-docs/context/
[^google_adk_memory]: Google ADK Docs, “Memory”, **date not found**, https://google.github.io/adk-docs/sessions/memory/
[^mcp_spec]: Model Context Protocol, “Specification (Version 2025-06-18)”, **2025-06-18**, https://modelcontextprotocol.io/specification/2025-06-18
