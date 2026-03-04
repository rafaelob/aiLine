# Modelo X/Y de orçamento de contexto

O modelo X/Y é uma forma simples (e eficaz) de evitar que um agente vire “prompt soup”.

- **X = Core Budget**  
  Teto para o “núcleo” do turno: *system/dev + regras duráveis + skills ativas + rolling summary + histórico recente + estado de orquestração*.

- **Y = Total Budget**  
  Teto total de input do turno (contexto inteiro que você envia ao modelo).

- **(Y − X) = Tool/RAG/Memory Budget**  
  Reserva dedicada para *tool catalogs/schemas, MCP, RAG/evidências, memória recuperada e resumos de resultados*.

A propriedade que você quer garantir:

> Mesmo em sessões longas, o agente sempre terá espaço garantido para ferramentas e evidências, sem sacrificar o “núcleo” que mantém coerência.

---

## 1) Definições operacionais

### 1.1 O que é “core”
Core é o conjunto mínimo necessário para o modelo:
- entender o objetivo e as regras,
- manter consistência com o histórico relevante,
- escolher um plano e/ou decidir quais ferramentas usar.

O core **não** deve conter:
- payloads brutos grandes (HTML, logs),
- transcrições extensas,
- catálogos enormes de tools ou schemas completos “por via das dúvidas”.

### 1.2 O que é “tool budget”
É o espaço para “trazer o mundo” para dentro do turno **sob demanda**:
- catálogo de tools (mínimo),
- schemas só das tools escolhidas,
- evidence packs de RAG,
- memória recuperada (perfil/subgrafo),
- resumos de tool results.

---

## 2) Como escolher X e Y

### 2.1 Comece pela janela do modelo (context window)

Defina:

- **C** = janela máxima do modelo (input + output).
- **O** = reserva de output (para a resposta do modelo).
- **S** = margem de segurança (overhead de mensagens, variação do tokenizer, etc.).

Então use:

- **Y = C − O − S**

> Em produção, prefira usar o “token counting endpoint” do provedor quando existir; contadores locais são aproximações (especialmente com tools, imagens e schemas).

### 2.2 Escolha X a partir do pior caso de tools

Defina o seu “pior caso de tool context”:

- catálogo mínimo de tools (ou lista MCP),
- schemas de 1–3 tools,
- evidence pack (top‑k com quotes curtas),
- memória recuperada,
- tool result summaries (N ferramentas),
- *+* overhead.

Chame isso de **B_tools_worst**.

Então:

- **X = Y − B_tools_worst**

Como regra prática (quando você ainda não tem telemetria):
- **X entre 35% e 60% de Y** funciona bem na maioria dos agentes.
  - mais perto de 35% se seu agente usa muitas tools/RAG,
  - mais perto de 60% se quase nunca chama tools.

> Depois, ajuste com dados (token ledger). Em geral, agentes “tool‑heavy” fracassam por falta de reserva para resultados.

---

## 3) Estratégia de compaction/sumarização (quando core > X)

Você precisa de uma política de “quebra” quando o core ultrapassar X:

### 3.1 Rolling summary (client‑side)
Padrão universal e portável entre provedores.

- mantenha apenas **N âncoras recentes** intactas;
- compacte turns antigos em um **rolling summary canônico** (sempre no mesmo schema);
- limite o rolling summary por um teto próprio (ex.: 6–12k tokens) e deixe o resto “evaporar”.

**Vantagens**
- funciona em qualquer stack,
- summary é auditável (humano lê),
- você controla o schema.

**Riscos**
- drift/“alucinação” se o sumarizador inventar fatos,
- perda de detalhe útil.

Mitigações:
- schema rígido,
- “facts vs hypotheses”,
- rastrear “decisions + rationale”,
- manter “handles” para artefatos.

### 3.2 Compaction server‑side (quando disponível)
Alguns provedores oferecem um mecanismo de **compaction interno** que comprime o histórico em um item opaco/criptografado.  
Quando você usa isso:

- **não** precisa re‑enviar todo o histórico como texto,
- o provedor pode manter estado de forma mais eficiente,
- o item de compaction é “canônico” e não foi feito para ser lido por humanos.

Use isso quando:
- você está 100% no ecossistema daquele provedor,
- o custo/latência de sumarizar client‑side é relevante,
- você quer reduzir risco de drift do rolling summary.

> Mesmo com compaction server‑side, X/Y ainda é útil: tool catalogs/results continuam podendo explodir o contexto se você não reservar (Y−X).

---

## 4) Alocação por turno: scheduler em 2 camadas

### 4.1 Construa o core (<= X)
Ordem recomendada (também favorece cache):
1) system
2) developer
3) regras duráveis do projeto (ex.: `AGENTS.md`, `CLAUDE.md`, regras por path)
4) skills index (mínimo)
5) skills ativas (sob demanda)
6) rolling summary
7) últimas N âncoras (pares user/assistant)
8) estado de orquestração do turno (plano, constraints, objetivos)
9) mensagem atual do usuário

Se exceder X:
- compacte turns antigos → rolling summary,
- reduza âncoras,
- e, em último caso, *trim* controlado (sem “cortar no meio” estruturas críticas).

### 4.2 Empacote “tool context” (<= Y − core)
Monte uma lista de blocos com prioridade (exemplo):

1) **memória recuperada relevante** (perfil/subgrafo)
2) **evidence pack** (quotes curtas + fontes)
3) **schemas apenas de tools selecionadas**
4) **tool results resumidos + handles**
5) catálogo de tools (se o modelo precisar ver)

Empacote até preencher o orçamento; o resto fica fora do prompt.

---

## 5) Prompt caching e caps de tools

Caching não aumenta a janela do modelo, mas:
- reduz custo/latência (onde suportado),
- incentiva estabilidade do prefixo,
- ajuda especialmente em loops tool‑heavy (vários passos).

Para maximizar cache hit:
- mantenha o prefixo estável (system/dev/regras/índices),
- coloque conteúdo variável (mensagens do usuário, tool outputs) **no final**,
- evite reordenar blocos e evitar mudanças desnecessárias em tools/schemas.

Notas práticas:
- Em stacks onde caching depende de “prefix match”, **tools e imagens** geralmente precisam estar **idênticos e na mesma ordem** entre chamadas para aproveitar cache.
- Em Anthropic/Claude há `cache_control` para marcar blocos cacheáveis (ver docs oficiais).
- Em OpenAI há prompt caching automático (ver docs oficiais).

### Cap específico de ferramentas (ex.: Web Search)
Mesmo que seu modelo suporte uma janela grande, algumas ferramentas têm limite próprio.  
Por exemplo, o tool de **Web Search** pode limitar o contexto efetivo (e.g., 128k).  
Implicação: quando Web Search estiver habilitado, trate **Y** como `min(Y, limite_da_tool)` e ajuste X.

Referências (oficiais):
- OpenAI: Prompt caching — https://platform.openai.com/docs/guides/prompt-caching  
- Anthropic: Prompt caching — https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching  
- OpenAI: Tools Web Search — https://platform.openai.com/docs/guides/tools-web-search

---

## 6) “Anti‑padrões” comuns

- Jogar **catálogo de 300 tools + schemas completos** no prompt “sempre”.
- Colocar resultados grandes inline sem handle.
- Misturar memória durável com logs efêmeros.
- Sumarização sem schema (drift inevitável).
- Não ter telemetria de tokens (você fica cego).

---

## 7) Recomendações de produção

- Logue por turno: `core_tokens`, `tool_budget_tokens`, `turns_kept`, `turns_compacted`, `tool_payload_bytes`, `inline_summary_tokens`, etc.
- Tenha testes que simulam:
  - sessão curta (sem compaction),
  - sessão longa (compaction recorrente),
  - tool output grande (handle + excerpt),
  - RAG com top‑k,
  - memória em grafo com TTL expirando.
- Mantenha limites explícitos por “classe” de conteúdo:
  - max tokens para rolling summary,
  - max tokens para skill ativa,
  - max tokens para evidence pack,
  - max tokens para tool schema.

---

## Próximo passo

Veja `03_skills_mcp_integration.md` e `05_orchestration_reference.md` para aplicar o modelo ao loop do agente.
