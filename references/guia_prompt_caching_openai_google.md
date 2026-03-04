# Guia exaustivo de Prompt/Context Caching  
**OpenAI Responses API + Google GenAI (`google-genai` SDK)**  
_Objetivo: reduzir custo e latência sem abrir mão do seu próprio gerenciamento de contexto/conversas._

> **TL;DR**  
> - **OpenAI (Responses API):** “Prompt Caching” é **automático** (prefixo idêntico), funciona **sem WebSocket** e aparece em `usage.prompt_tokens_details.cached_tokens`.  
> - **Google GenAI (Gemini API / Vertex AI via `google-genai`):** há **implicit caching** (automático) e **explicit caching** (manual, com `cache.name` + TTL e storage).  
> - O “pulo do gato” em ambos: **prefixo estável no início** + **conteúdo variável no final**.

---

## Sumário
1. [Conceitos e diferença entre “caching” e “state/continuation”](#1-conceitos-e-diferença-entre-caching-e-statecontinuation)  
2. [OpenAI Responses API — Prompt Caching (sem WebSocket)](#2-openai-responses-api--prompt-caching-sem-websocket)  
   2.1 [Como funciona](#21-como-funciona)  
   2.2 [O que é cacheável](#22-o-que-é-cacheável)  
   2.3 [Parâmetros importantes](#23-parâmetros-importantes)  
   2.4 [Retenção (in_memory vs 24h) + ZDR](#24-retenção-in_memory-vs-24h--zdr)  
   2.5 [Como medir e provar economia](#25-como-medir-e-provar-economia)  
   2.6 [Receitas práticas de prompt](#26-receitas-práticas-de-prompt)  
   2.7 [Estratégias de `prompt_cache_key` (incl. sharding)](#27-estratégias-de-prompt_cache_key-incl-sharding)  
   2.8 [Armadilhas comuns](#28-armadilhas-comuns)  
3. [Google GenAI (`google-genai` SDK) — Context Caching](#3-google-genai-google-genai-sdk--context-caching)  
   3.1 [Implicit caching](#31-implicit-caching)  
   3.2 [Explicit caching](#32-explicit-caching)  
   3.3 [Vertex AI vs Gemini API (diferenças práticas)](#33-vertex-ai-vs-gemini-api-diferenças-práticas)  
   3.4 [Como medir e provar economia](#34-como-medir-e-provar-economia)  
   3.5 [Receitas práticas de cache](#35-receitas-práticas-de-cache)  
   3.6 [Armadilhas comuns](#36-armadilhas-comuns)  
4. [Framework de decisão](#4-framework-de-decisão)  
5. [Estratégias por padrão de tráfego](#5-estratégias-por-padrão-de-tráfego)  
6. [Checklist de implementação (produção)](#6-checklist-de-implementação-produção)  
7. [Referências oficiais (links)](#7-referências-oficiais-links)  

---

## 1) Conceitos e diferença entre “caching” e “state/continuation”

### 1.1 Caching (o que você quer aqui)
Caching é reaproveitar **cálculos de prefill/prefixo** (tokens iniciais) já processados recentemente:
- reduz **latência de prefill** (especialmente prompts longos)  
- reduz **custo de tokens de entrada** (desconto em “cached input”)  

**Ponto crítico:** caching não depende de você “não reenviar” o contexto.  
Você pode continuar com seu **gerenciador de contexto** (histórico, RAG, templates), e ainda assim obter economia se o **prefixo** for estável.

### 1.2 State/Continuation (não é a mesma coisa)
- Em OpenAI, “continuation” (ex.: `previous_response_id` e WebSocket mode) evita reenviar todo o histórico a cada turno, e é excelente para fluxos agentic com muitas chamadas.  
- Em Google, “explicit caching” se parece com “state” porque você referencia um `cache.name`, mas tecnicamente é um **prefixo cacheado** com TTL.

Este guia foca no **caching** (economia/latência) mantendo seu próprio state.

---

## 2) OpenAI Responses API — Prompt Caching (sem WebSocket)

### 2.1 Como funciona

#### Regras de ouro
- Cache hit exige **match exato de prefixo** do prompt.  
- O caching entra em jogo quando o prompt tem **≥ 1024 tokens**.  
- A OpenAI “cacha” o **maior prefixo** reaproveitável; historicamente isso começa em 1024 e cresce em **incrementos de 128 tokens** (varia por modelo/infra).  
- A resposta traz a contagem de cache hit em `cached_tokens`.

#### Roteamento e `prompt_cache_key`
A plataforma roteia requests para máquinas que **recentemente processaram** o mesmo prefixo (hash do prefixo).  
- Tipicamente o hash usa os **primeiros ~256 tokens** (pode variar por modelo).  
- Se você fornece `prompt_cache_key`, ele é combinado com o hash para melhorar “stickiness” e hit rate.  
- Existe um comportamento de “overflow”: se o mesmo par (prefixo + cache_key) exceder ~15 req/min, parte do tráfego pode ir para outras máquinas e o cache fica menos efetivo.

> **Implicação prática:** cache funciona melhor com **prefixo grande + repetição constante** e com uma estratégia de `prompt_cache_key` coerente com seu tráfego.

---

### 2.2 O que é cacheável

O caching é sobre o **prefixo do prompt** e pode incluir:
- array de mensagens (system/user/assistant)  
- ferramentas (`tools`) e sua definição (importante manter idênticas)  
- imagens (incluindo parâmetros que alteram tokenização)  
- schemas de structured output (JSON schema costuma entrar como prefixo)

**Regra geral:** qualquer coisa que mude o prefixo quebra o cache.

---

### 2.3 Parâmetros importantes

#### `prompt_cache_key`
- string opcional  
- serve para otimizar roteamento e hit rate  
- boa prática: usar consistentemente para workloads com prompts semelhantes  
- **nota:** em algumas referências da API, ele substitui o campo `user` antigo em Chat Completions.

#### `prompt_cache_retention`
Define política de retenção do cache:
- `in_memory` (default)  
- `24h` (extended) — disponível só em alguns modelos

---

### 2.4 Retenção (`in_memory` vs `24h`) + ZDR

#### `in_memory`
- prefixes geralmente ficam ativos por **5–10 min** sem uso, e no máximo **1 hora**  
- fica em memória volátil de GPU

#### `24h`
- mantém prefixos ativos **até 24h**  
- funciona offloadando tensores KV para storage local de GPU  
- **atenção ZDR:** `in_memory` é elegível para Zero Data Retention; `24h` tipicamente **não é considerado** elegível para ZDR (porque KV tensors podem persistir).

> **Regra prática:**  
> - se você precisa de ZDR “estrito”, prefira `in_memory`.  
> - se você precisa de economia previsível em tráfego espaçado (ex.: jobs ao longo do dia), `24h` pode ser decisivo (quando permitido pela sua política).

---

### 2.5 Como medir e provar economia

#### Campo-chave em Responses API
- `response.usage.prompt_tokens_details.cached_tokens`  
  - `cached_tokens > 0` = houve cache hit  
  - `uncached_input_tokens = prompt_tokens - cached_tokens`

#### Fórmula de custo (por request)

#### Exemplos rápidos (OpenAI)

> **Importante:** o desconto de “cached input” varia por modelo. Sempre confira o pricing atual.

Exemplos (preços por 1M tokens — consulte a tabela oficial):
- **gpt-5.2**: Input $1.75, Cached input $0.175 (≈ **90% desconto**), Output $14  
- **gpt-4o**: Input $2.50, Cached input $1.25 (≈ **50% desconto**), Output $10  

**Como interpretar na prática:**  
Se seu request tem `prompt_tokens=50k` e `cached_tokens=40k`:
- você paga 10k tokens a preço “input”  
- e 40k tokens a preço “cached input”  
— o que costuma derrubar bastante o custo do “contexto fixo” (system/tools/schema).

Para um modelo com preços:
- `input_rate` ($/token)  
- `cached_input_rate` ($/token)  
- `output_rate` ($/token)

Então:

```
cost = (prompt_tokens - cached_tokens) * input_rate
     + cached_tokens * cached_input_rate
     + completion_tokens * output_rate
```

> **Dica:** use sempre o pricing oficial do modelo (há coluna “Cached input”).

#### Métricas mínimas (por rota/feature/agent/model)
- `prompt_tokens`, `cached_tokens`, `completion_tokens`, `total_tokens`
- `cache_hit_rate` por request: `cached_tokens / prompt_tokens`
- latência (p50/p90/p99) e TTFT, se você mede
- distribuição de tamanho de prompt (quantos ≥ 1024)
- “prefix reuse score”: % de requests que compartilham o mesmo prefixo (ver seção 6)

---

### 2.6 Receitas práticas de prompt (para maximizar cache hit)

#### Receita A — “Prefixo estável + sufixo dinâmico”
Estruture o prompt como:

1) System “fixo”: persona, regras, estilo  
2) (Opcional) “Toolkit fixo”: ferramentas + schemas JSON (nunca mexer sem versionar)  
3) (Opcional) “Contexto semi-fixo”: documento base, guideline, spec, repo map  
4) **Somente no final:** RAG variável, dados do usuário, pergunta, outputs de tool, etc.

**Exemplo conceitual:**

- `SYSTEM`: instruções estáveis (grandes)  
- `SYSTEM/DEV`: schema e toolset  
- `ASSISTANT`: contexto fixo do agente (playbook)  
- `USER`: pergunta final + variáveis

#### Receita B — “Separar toolset por agente”
Se você tem N agentes com toolsets diferentes, não compartilhe um “mega toolset” variável.
- Cada agente = toolset + schema fixos = melhor caching

#### Receita C — “Versionar prompts e schemas”
Sempre que mudar instruções ou schema:
- mude um “prompt_version” no texto (no prefixo)  
- e/ou mude `prompt_cache_key` (ex.: `agentX:v3`)  
Assim você evita comparar métricas de caching de versões diferentes.

---

### 2.7 Estratégias de `prompt_cache_key` (incl. sharding)

A escolha do `prompt_cache_key` é o principal “controle” que você tem.

#### Estratégia 1 — Por agente (default recomendado)
- `prompt_cache_key = "{agent_name}:{prompt_version}"`  
Bom para: múltiplos agentes com prompts grandes e estáveis.

#### Estratégia 2 — Por tenant (isolamento/privacidade interna)
- `prompt_cache_key = "{tenant_id}:{agent}:{version}"`  
Bom para: multi-tenant em uma única org, quando você quer **evitar** qualquer chance de roteamento cruzado (mesmo que o prefixo seja “genérico”).  
Custo: reduz reuse cross-tenant.

#### Estratégia 3 — Sharding por volume (evitar overflow)
Se um mesmo prefixo recebe tráfego alto, você pode shardear para manter cada bucket abaixo do limiar (~15 req/min) e melhorar “stickiness”:

- `prompt_cache_key = "{agent}:{version}:shard={hash(user_id)%N}"`

Escolha `N` de modo que:
- `(RPS_total * 60) / N` fique próximo (ou abaixo) de ~15 rpm por shard.

> Observação: sharding cria caches separados por shard; funciona bem quando o volume é alto o suficiente para “aquecer” todos os shards.

#### Estratégia 4 — Por workflow (ex.: repo_id, doc_id)
- `prompt_cache_key = "repo:{repo_id}:{agent}:{version}"`  
Bom para: análise recorrente do mesmo repositório ou documento.

---

### 2.8 Armadilhas comuns

1) **Prompts < 1024 tokens**: caching não engata (cached_tokens = 0).  
2) **Variações invisíveis**: espaços, ordering de keys JSON, pequenas diferenças em tool schema -> quebram prefixo.  
3) **Tools mudando por request**: se você “anexa” tools dinamicamente, você mata o cache.  
4) **RAG antes das instruções**: se você coloca chunks variáveis no começo, você destrói o prefixo cacheável.  
5) **Troca constante de modelo**: cache não “transfere” entre modelos. Se seu model-mapper alterna modelos para a mesma classe de prompt, você perde cache hit.

---

## 3) Google GenAI (`google-genai` SDK) — Context Caching

A família Gemini tem **dois mecanismos**:

- **Implicit caching**: automático, sem garantia de savings (quando ocorre, a plataforma aplica desconto).  
- **Explicit caching**: você cria um cache (recurso) e referencia por `cache.name`. Garante savings, mas exige gestão (TTL, storage, invalidação).

---

### 3.1 Implicit caching

#### Propriedades
- habilitado por padrão em modelos suportados  
- depende de **prefixo comum** e requests relativamente próximos (curta janela)  
- tem **limiar mínimo de tokens** por modelo (ex.: 1024 para Flash, 4096 para Pro em alguns docs)

#### Como maximizar hit rate
- prefixo grande e comum no início  
- variação no final  
- enviar requests com prefixo similar em um curto intervalo

---

### 3.2 Explicit caching

#### O que você faz
1) cria cache com `client.caches.create(...)`  
2) usa em `client.models.generate_content(...)` com `cached_content = cache.name`  
3) gerencia TTL/expire_time  
4) pode listar/get/update/delete caches

#### Importante
- não dá para “ver” o conteúdo cacheado depois (apenas metadados)  
- TTL default costuma ser **1 hora** se não setar  
- há **custo de storage** (por token*hora) em explicit caching (ver pricing)

---

### 3.3 Vertex AI vs Gemini API (diferenças práticas)

#### Diferenças importantes (não ignore)
**Gemini Developer API (ai.google.dev)** e **Vertex AI (cloud.google.com)** têm diferenças de limites e pricing/caching:

- **Limiar mínimo de tokens** para caching pode variar:
  - No guia do **Gemini API**, o mínimo de implicit caching aparece **por modelo** (ex.: 1024 para Flash e 4096 para Pro).  
  - No **Vertex AI**, a documentação descreve caching com mínimo **2.048 tokens** para requests de caching.  
- **Desconto**: no **Vertex AI**, a doc afirma que implicit caching dá **90% de desconto** em tokens cacheados, e explicit caching dá **90% (Gemini 2.5) / 75% (Gemini 2.0)**.  
- **Região e armazenamento (Vertex)**: caches são armazenados na região onde você cria o cache; há limites como 10 MB para cache via blob/text e orientações específicas para arquivos em Cloud Storage.

**Ação recomendada:** na sua camada de provider, trate `gemini_api` e `vertex_ai` como “targets” distintos (configs, limites, métricas e custos).


Você pode usar `google-genai`:
- contra **Gemini Developer API** (ai.google.dev) com API key  
- contra **Vertex AI** (cloud.google.com) com projeto/região/credenciais

Diferenças que você precisa respeitar:
- mínimos de tokens / modelos suportados podem mudar entre docs/ambientes  
- explicit caching no Vertex tem detalhes de região e limites (blob/text 10MB, etc.)  
- no Vertex, implicit caching é default e explicit caching tem descontos por geração e storage

> Se você é multi-cloud/multi-ambiente, trate “Gemini API” e “Vertex AI” como **targets diferentes** na sua camada de provider.

---

### 3.4 Como medir e provar economia

#### Break-even (quando explicit caching vale a pena)

No **explicit caching** (Google), você tem 3 componentes relevantes:
1) **Criação do cache**: tokens de entrada cobrados a preço normal (input).  
2) **Uso do cache**: tokens cacheados cobrados a “context caching price” (mais barato).  
3) **Storage**: custo por token*hora (enquanto o cache existe).

Uma forma simples de decidir é calcular quantas “reutilizações” dentro do TTL você precisa para empatar.

Defina:
- `P_in` = preço de input ($/1M tokens)  
- `P_cache` = preço de “context caching” ($/1M tokens)  
- `P_store` = preço de storage ($/1M tokens por hora)  
- `T` = TTL em horas  
- `N` = número de vezes que você vai reutilizar o cache durante o TTL (chamadas que referenciam `cache.name`)

O break-even aproximado (ignorando outputs) é:

```
N > (P_in + P_store * T) / (P_in - P_cache)
```

Exemplos usando preços típicos do Gemini Developer API (Standard):
- **Gemini 2.5 Flash**: `P_in=0.30`, `P_cache=0.03`, `P_store=1.00`  
  - TTL=1h → `N > (0.30 + 1.00) / (0.30-0.03) ≈ 4.81` → **~5 usos**  
- **Gemini 2.5 Pro**: `P_in=1.25`, `P_cache=0.125`, `P_store=4.50`  
  - TTL=1h → `N > (1.25 + 4.50) / (1.25-0.125) ≈ 5.11` → **~6 usos**

> Interpretação: explicit caching costuma valer quando você faz **várias perguntas** sobre o mesmo corpus/repo/manual dentro do TTL.


Campos relevantes (variam por API/SDK, mas a ideia é a mesma):
- `usage_metadata.cached_content_token_count` (ou equivalente)  
- contadores de prompt/total tokens

Modelo mental de custo (Gemini):
- você paga para **criar** o cache (input tokens a preço normal)  
- depois, ao **referenciar** o cache, os tokens cacheados são cobrados a uma taxa menor  
- explicit caching também cobra **storage** por token*hora (TTL)

---

### 3.5 Receitas práticas de cache

#### Receita G1 — Cache por “corpus grande” (doc/repo)
Use explicit caching quando você tem:
- repositórios grandes  
- PDFs extensos  
- guideline longo + consultado muitas vezes  
- multimodal (vídeo/áudio) com muitas perguntas

Estratégia:
- `cache_key` no seu sistema: `tenant_id + artifact_id + model + version`  
- TTL curto para exploração (5–60 min) e TTL maior para uso contínuo (se ROI justificar)

#### Receita G2 — Cache por sessão/usuário (quando faz sentido)
Para conversas que reutilizam o mesmo “manual”:
- crie cache do manual + instruções  
- cada turno só envia a pergunta (curta) referenciando cache

#### Receita G3 — Invalidação por mudança de artefato
Se o documento/repo muda:
- gere novo `artifact_version`  
- crie novo cache e delete/expirar o antigo

---

### 3.6 Armadilhas comuns

1) **Criar cache demais**: explicit caching tem storage. Se TTL for alto e hit rate baixo, você perde dinheiro.  
2) **Artefato mutável (GCS) sendo alterado**: em Vertex, não altere objetos em bucket antes do cache expirar/deletar.  
3) **Confundir implicit com explicit**: implicit é “best effort”; se você precisa de previsibilidade, use explicit.

---

## 4) Framework de decisão

### 4.1 Perguntas objetivas (antes de mexer em arquitetura)
1) **Qual % dos requests têm ≥ 1024 tokens (OpenAI) / ≥ limiar do modelo (Gemini)?**  
2) **Quanto do prompt é realmente repetido?**  
3) **Qual é o intervalo típico entre chamadas com o mesmo prefixo?**  
4) **Qual é o volume por prefixo?** (para evitar overflow e decidir sharding)  
5) **Você alterna modelos para a mesma classe de request?** (mata cache)  
6) **ZDR/privacidade:** você pode usar retenção estendida (24h / TTL alto) ou precisa ficar “in-memory”?

### 4.2 Decisão rápida (heurística)
- **Prompts curtos (< 1024 tokens):** caching quase não importa → foque em otimizar prompt/tokens, batching, compressão de contexto.  
- **Prefixo grande + repetição alta:** caching dá ROI forte (OpenAI automático; Google implicit/expl).  
- **Prefixo grande + repetição espaçada:**  
  - OpenAI: considerar `24h` (se permitido)  
  - Google: explicit caching com TTL ajustado  
- **Workflows agentic com tool calls:** caching ajuda, mas o maior ganho costuma vir de state/continuation (se você aceitar). Se não aceitar, maximize cache via prefixo/toolset fixos.

---

## 5) Estratégias por padrão de tráfego

> Use esta seção como “playbook”: identifique seu padrão e aplique a estratégia correspondente.

### Padrão A — “Chat curto e variado” (long tail)
**Sinais**
- maioria dos prompts < 1024 tokens  
- baixo reuse de prefixo  
- usuários fazem perguntas muito diferentes

**OpenAI**
- caching terá impacto limitado (cached_tokens ~ 0)  
- estratégia: reduzir tokens, resumir histórico local, RAG menor, escolher modelos mais baratos

**Google**
- implicit caching pode ser irrelevante  
- explicit caching só faz sentido se há um “manual/policy” fixo grande que entra sempre

---

### Padrão B — “Template fixo + perguntas variáveis” (alto reuse)
**Sinais**
- 1–N prompts base repetidos com pequenas variações  
- prompts geralmente ≥ 1024 tokens

**OpenAI**
- ideal para Prompt Caching  
- use prefixo fixo + `prompt_cache_key` por template/agente  
- monitore `cached_tokens` e latência

**Google**
- implicit caching costuma funcionar  
- se quiser previsibilidade: explicit caching por template (TTL 1h)

---

### Padrão C — “Alto volume no mesmo prefixo” (hot key)
**Sinais**
- muito tráfego no mesmo prompt base  
- hit rate inconsistente apesar de prefixo estável

**OpenAI**
- adote **sharding** de `prompt_cache_key` (ex.: hash(user_id)%N) para reduzir overflow  
- mantenha o prefixo idêntico em cada shard

**Google**
- implicit caching pode ficar menos previsível; explicit caching pode dar previsibilidade se o custo de storage valer  
- no Vertex, observe limites e custo de storage

---

### Padrão D — “Agentic coding/orchestration” (tools, multi-step)
**Sinais**
- muitas chamadas por tarefa  
- tool schemas longos  
- contexto cresce com outputs de ferramentas

**OpenAI**
- mantenha tools e schemas **fixos** no prefixo  
- coloque outputs de tools no final (dinâmico)  
- se o mesmo “agente” roda muitas vezes por dia, use `prompt_cache_retention=24h` (se permitido)  
- (Opcional) manter o modelo estável no workflow para maximizar caching

**Google**
- explícito é forte para “repo analysis”: cache do repo/mapa e perguntar várias vezes  
- TTL baseado no tempo típico de sessão (ex.: 30–120 min)

---

### Padrão E — “RAG pesado” (contexto recuperado muda muito)
**Sinais**
- chunks recuperados variam por query  
- grande parte do prompt é conteúdo variável

**OpenAI**
- caching ainda ajuda no “cabeçalho” (instruções + toolset + schema)  
- estratégia: manter RAG no final; e evitar que RAG mude o prefixo

**Google**
- se você consulta sempre o mesmo corpus, explicit caching do corpus e depois só enviar query  
- se corpus muda a cada query, implicit caching só pega o prefixo fixo

---

### Padrão F — “Multi-tenant SaaS”
**Sinais**
- múltiplos clientes na mesma org/projeto  
- risco de misturar “warm caches” entre tenants (mesmo que sem exposição direta)

**OpenAI**
- mantenha dados de tenant fora do prefixo; se necessário, use `prompt_cache_key` com tenant_id  
- padronize toolset por agente

**Google**
- explicit caching por tenant+artefato  
- TTL curto por padrão; evite caches longos para tenants inativos

---

### Padrão G — “Jobs batch / offline”
**Sinais**
- muitas execuções parecidas em janelas de tempo  
- não precisa de latência baixíssima, mas custo importa

**OpenAI**
- Prompt Caching ajuda se há prefixo comum grande  
- considere Batch API (quando aplicável) separadamente do caching

**Google**
- explicit caching com TTL suficiente para o batch; delete ao final  
- avalie batch pricing (se disponível) na Gemini API

---

### Padrão H — “Multimodal (imagens/áudio/vídeo)”
**Sinais**
- inputs multimodais grandes e repetidos  
- muitas perguntas sobre o mesmo artefato

**OpenAI**
- imagens no prefixo podem ser cacheadas se idênticas (incluindo parâmetros de detail/tokenização)  
- se artefatos mudam, caching cai

**Google**
- explicit caching é excelente (cache do vídeo/áudio/PDF e múltiplas queries)  
- atente para limites de tamanho (ex.: 10MB via blob/text no Vertex; acima disso via URI)

---

### Padrão I — “Model-mapping dinâmico” (troca frequente de modelo)
**Sinais**
- roteador alterna modelos para requests muito similares  
- objetivo é custo/qualidade

**Recomendação geral**
- caching é por modelo. Se você alternar modelos, você perde cache reuse.  
- estratégia: para classes de tráfego com alto reuse, “pin” em um modelo por janela (ex.: por sessão, por tenant, por workflow) para maximizar caching.

---


### 6.0 Arquitetura recomendada (mantendo seu próprio gerenciamento de contexto)

A forma mais robusta de “garantir caching” sem abrir mão do seu state é padronizar a montagem do prompt em **camadas determinísticas**:

1) **Base prefix (100% estável)**  
   - system prompt fixo (com versão)  
   - toolset fixo (por agente)  
   - schemas/structured output fixos  
2) **Contexto semi-estável** (opcional)  
   - policy/handbook do tenant (se muda pouco)  
   - repo map (se muda pouco)  
3) **Contexto dinâmico**  
   - RAG chunks do turno  
   - user message do turno  
   - outputs de tools do turno

Além disso:
- gere um **fingerprint do prefixo** (hash) para observabilidade e troubleshooting  
- mantenha o **modelo estável por classe de tráfego** (cache é por modelo)  
- para OpenAI, derive `prompt_cache_key` do fingerprint + dimensões de negócio (agent/tenant/shard)  
- para Google explicit caching, persista `cache.name` em um “Cache Registry” (tenant+artefato+versão+modelo)

Pseudocódigo de fingerprint (evita false misses por ordenação):
```text
prefix = normalize(system_instructions)
       + normalize(json_schema)
       + normalize(sorted_tools)
       + normalize(agent_playbook)

prefix_fingerprint = sha256(prefix)
```


## 6) Checklist de implementação (produção)

### 6.1 OpenAI — Prompt Caching
- [ ] Medir % de requests ≥ 1024 tokens  
- [ ] Garantir prefixo estável: instruções, exemplos, schemas, tools no começo  
- [ ] Variáveis no final: RAG, user question, tool outputs  
- [ ] Definir política de `prompt_cache_key` (por agente/tenant/shard)  
- [ ] Decidir `prompt_cache_retention` (ZDR? `in_memory` vs `24h`)  
- [ ] Instrumentar `cached_tokens` e criar dashboards por feature/agent/model  
- [ ] A/B test: baseline vs reestruturação de prompt  
- [ ] Documentar “versionamento de prompt/schema”

### 6.2 Google — Context Caching
- [ ] Identificar se você usa Gemini API key (ai.google.dev) ou Vertex AI  
- [ ] Para implicit: garantir prefixo grande e comum no início + requests próximos  
- [ ] Para explicit:  
  - [ ] definir “o que vira cache”: doc/repo/manual  
  - [ ] definir TTL e política de storage  
  - [ ] persistir mapping (tenant+artefato+versão -> cache.name)  
  - [ ] invalidar quando artefato mudar  
  - [ ] delete caches em massa quando não precisar  
- [ ] Instrumentar `usage_metadata.cached_content_token_count` e storage costs

### 6.3 Experimento mínimo (48h)
1) Escolha 1 rota/agent com prompts longos e repetitivos.  
2) Reestruture em prefixo/sufixo.  
3) Rode com `prompt_cache_key` estável.  
4) Meça:
   - delta de custo (input uncached vs cached)  
   - delta de latência p50/p90  
   - cache hit rate  
5) Só então escale.

---

## 7) Referências oficiais (links)

### OpenAI
- Prompt caching (guia): https://platform.openai.com/docs/guides/prompt-caching  
- Blog de anúncio + detalhes (incl. 1024 tokens e incrementos): https://openai.com/index/api-prompt-caching/  
- Pricing (coluna “Cached input”): https://platform.openai.com/docs/pricing/  
- API pricing (site): https://openai.com/api/pricing/  
- API reference (Chat object) — campos `prompt_cache_key` / `prompt_cache_retention`: https://platform.openai.com/docs/api-reference/chat/object  

### Google (Gemini API / `google-genai`)
- Context caching (Gemini API): https://ai.google.dev/gemini-api/docs/caching/  
- Pricing (Gemini Developer API): https://ai.google.dev/pricing  (ou https://ai.google.dev/gemini-api/docs/pricing)  

### Google (Vertex AI)
- Vertex AI pricing (para storage/caching): https://cloud.google.com/vertex-ai/pricing  (ver seção de Generative AI / caching, quando aplicável)
- Context caching overview: https://cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-overview  
- Create context cache (Vertex): https://docs.cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-create  
- Use context cache (Vertex): https://cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-use  

---

## Apêndice A — Exemplos de código (mínimos)

### A1) OpenAI Responses API (HTTP) — com `prompt_cache_key` e `prompt_cache_retention`
```bash
curl https://api.openai.com/v1/responses \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.2",
    "prompt_cache_key": "agent_code_review:v1",
    "prompt_cache_retention": "in_memory",
    "input": [
      {
        "type": "message",
        "role": "system",
        "content": [{"type": "input_text", "text": "INSTRUCOES GRANDES E FIXAS ..."}]
      },
      {
        "type": "message",
        "role": "user",
        "content": [{"type": "input_text", "text": "Pergunta variavel aqui ..."}]
      }
    ]
  }'
```

### A2) Google GenAI (Python) — explicit caching
```python
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-2.5-flash"

# Exemplo: cache de instrução grande (ou arquivo enviado via Files API)
cache = client.caches.create(
  model=model,
  config=types.CreateCachedContentConfig(
    display_name="manual-v1",
    system_instruction="INSTRUCOES GRANDES E FIXAS ...",
    ttl="3600s",
  )
)

resp = client.models.generate_content(
  model=model,
  contents="Pergunta curta aqui...",
  config=types.GenerateContentConfig(cached_content=cache.name),
)

print(resp.usage_metadata)
print(resp.text)
```

### A3) Google GenAI (Node.js) — explicit caching
```js
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
const model = "gemini-2.5-flash";

const cache = await ai.caches.create({
  model,
  config: {
    displayName: "manual-v1",
    systemInstruction: "INSTRUCOES GRANDES E FIXAS ...",
    ttl: "3600s",
  },
});

const response = await ai.models.generateContent({
  model,
  contents: "Pergunta curta aqui...",
  config: { cachedContent: cache.name },
});

console.log(response.text);
console.log(response.usageMetadata);
```
