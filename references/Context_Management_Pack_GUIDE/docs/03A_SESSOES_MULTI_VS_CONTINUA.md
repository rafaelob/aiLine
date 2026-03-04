# 03A — Sessões (multi‑sessão vs sessão contínua) e Compaction por *watermarks*

## Por que este documento existe

Você trouxe uma distinção crítica para **context management em produção**:

- **Multi‑sessão (episódica)**: a orquestração é reaberta em *múltiplas sessões* (ex.: cada chat/ticket/thread é “um novo começo”), com memória durável reidratada.
- **Sessão contínua (thread única longa)**: a orquestração vive em **uma única sessão** por muito tempo (muitas interações, dias/semanas), acumulando histórico e artefatos.

Essa diferença muda:
- a **política de orçamento** (quanto do window você usa de forma sustentada),
- a **cadência de compaction**,
- e os **controles de observabilidade** para detectar degradação.

> **Resumo SOTA:** para sessão contínua, use **orçamento por *watermarks*** (alvo sustentável + teto duro), e compacte **bem antes** de chegar perto do limite teórico.

---

## 1) Como vendors/frameworks modelam “sessão”

### OpenAI Agents SDK — *Session* como memória de thread
O Agents SDK documenta `Session` como a camada que:
1) recupera itens persistidos e **preprende** no próximo turno,
2) persiste itens novos ao final do run,
3) permite continuar a mesma conversa em runs futuros com a mesma sessão. [^openai_agents_sessions_js][^openai_agents_sessions_py]

Além disso, o SDK descreve um wrapper de sessão (`OpenAIResponsesCompactionSession`) que pode acionar compaction via `/responses/compact` automaticamente — e recomenda customizar o gatilho (por exemplo, **por tokens**, não por contagem de itens). [^openai_agents_sessions_js]

### LangGraph/LangChain — *threads* + checkpointing + store
LangGraph descreve:
- **short‑term memory** como persistência **por thread** (`thread_id`) via checkpointer;
- **long‑term memory** como store compartilhado **entre threads** (cross‑session), via `Store` interface. [^langgraph_memory][^langgraph_persistence]

**Mapeamento prático:**
- Multi‑sessão = múltiplos `session_id`/`thread_id` (um por chat).
- Sessão contínua = mesmo `session_id`/`thread_id` por muito tempo.

---

## 2) Por que “sessão contínua” precisa de estratégia diferente

### 2.1 Degradação por comprimento (não é só custo)
Há evidência consistente de que **a utilidade do contexto não cresce linearmente** com o tamanho:

- *Lost in the Middle* mostra que modelos têm viés de **primacy/recency**: usam melhor informação no começo/fim e pior no meio; e que a performance pode cair conforme o contexto cresce. [^lost_in_middle_arxiv]
- O benchmark *RULER* mostra que muitos modelos têm uma diferença entre *contexto “declarado”* e *contexto “efetivo”*, com quedas de performance à medida que o comprimento aumenta e as tarefas exigem mais do que recall superficial. [^ruler_arxiv]

**Implicação:** em sessão contínua, “encher o window” é uma estratégia frágil — você paga mais, e o modelo pode **usar pior** a informação.

### 2.2 Degradação operacional: compaction repetido acumula drift
Sessão contínua exige **compaction repetido**. Isso cria modos de falha específicos:
- **summary drift acumulado** (cada compactação muda um pouco a verdade),
- **perda de detalhes de auditoria** (o que foi dito por quem),
- **contaminação por dados não confiáveis** (tool/RAG/prompt injection que entra no sumário).

Logo, o design precisa:
- manter um `STATE_JSON` canônico,
- manter *logs/artifacts* fora do window,
- e aplicar compaction com validações e watermarks.

### 2.3 Por que reservar “headroom” (buffer)
A recomendação de *headroom* (não usar 100% do window) é suportada por duas realidades:

1) **Burstiness**: tool results/RAG podem explodir numa iteração.
2) **Limites e evolução de compaction**: o endpoint `/responses/compact` retorna itens opacos criptografados e “a lógica pode evoluir com o tempo”, então você quer margem para evitar thrash. [^openai_responses_compact_ref]

O post do Codex descreve que o produto evoluiu de compaction manual para o endpoint `/responses/compact` e que o sistema aciona compaction automaticamente quando passa um limite (`auto_compact_limit`). [^openai_codex_unrolling]

---

## 3) Modelo SOTA: *watermarks* (alvo sustentável + teto duro)

Em vez de “um único limite”, use **dois limites**:

- **Teto duro** (*hard cap*): nunca ultrapassar (evita overflow e comportamento errático).
- **Alvo sustentável** (*steady‑state target*): nível em que você quer operar na maior parte do tempo.

### Nomenclatura recomendada
- `W_model` = janela teórica do modelo (capability).
- `W_hard` = cap operacional de input (o seu limite total para *context assembly*).
- `W_steady` = alvo sustentável de input para sessão contínua.

> **Heurística SOTA:** em sessão contínua, escolha `W_steady` entre **55% e 70%** de `W_model` (comece em **60%**) e calibre com observabilidade.

### Exemplo com seus números
Se `W_model = 400k`:
- Multi‑sessão: `W_hard = 350k` (≈ 87,5%) pode ser aceitável porque o risco de “acumular degradação por compaction” é menor.
- Sessão contínua: `W_steady ≈ 240k` (60% de 400k) como alvo sustentável; `W_hard` continua 350k como buffer para bursts.

> **Nota importante (evita confusão de base):** você pode definir “60%” sobre `W_model` **ou** sobre `W_hard`.
>
> - 60% de `W_model` (400k) = 240k
> - 60% de `W_hard` (350k) = 210k
>
> Em geral, para operação diária, faz mais sentido definir `W_steady` como fração do **cap real que você usa** (`W_hard`).
> Use a métrica `context_fill_ratio` e ajuste com dados.

**Interpretação:**
- 240k = “tamanho típico” do contexto por turno.
- 350k = “tamanho máximo permitido” quando houver necessidade (tool/RAG bursts).

### Como isso vira configuração de budgets
Você pode implementar isso de duas formas (equivalentes):

**Opção A — Dois perfis (recomendado)**
- `continuous_steady_*` (utilização ~0.60)
- `continuous_burst_*` (utilização ~0.85–0.90)

O orquestrador alterna conforme sinais (ex.: tool burst, RAG heavy).

**Opção B — Um perfil com `utilization_target_ratio` + buffer não usado**
O budget manager calcula os budgets como:

`Y_total_input = (W_model - reserve_output - safety_margin) * utilization_target_ratio`

E deixa o resto como headroom.

---

## 4) Estratégias de compaction específicas para sessão contínua

### 4.1 “Episódios” dentro da sessão contínua
Trate a sessão contínua como uma sequência de **episódios** (capítulos):
- cada episódio tem um objetivo local,
- termina com checkpoint,
- e o detalhe é arquivado fora do window.

**Checkpoint (fim de episódio) gera:**
1) `STATE_JSON` atualizado (decisões/constraints/todos)
2) `EPISODE_SUMMARY` (S2)
3) `ARTIFACT_POINTERS` (URIs/hashes)
4) `EVIDENCE_LOG` (IDs/citações usadas)

### 4.2 Compaction por *watermarks* (GC‑like)
Use *watermarks* como garbage collector:

- Se `tokens_used <= W_steady`: não compacte (evita drift).
- Se `W_steady < tokens_used <= W_hard`: compacte **só fatias voláteis** (tool dumps, RAG obsoleto, histórico antigo).
- Se `tokens_used > W_hard`: modo emergência (hard restart / forced compaction + drop agressivo).

### 4.3 Preferir “delegate” para tarefas expansivas
Para preservar a thread principal:
- delegue tarefas tool/RAG‑heavy a subagentes (modo **delegate**),
- devolva apenas output tipado + pointers.

Isso reduz o crescimento do histórico do orquestrador e minimiza “context rot”.

---

## 5) Observabilidade: como saber se a sessão contínua está degradando

Métricas mínimas (por sessão e por turno):
- `context_tokens_total` e `context_fill_ratio = total / W_model`
- tokens por slice (system/skills/state/history/tools/rag)
- `compaction_events_per_100_turns`
- `summary_drift_incidents` (detecção por diffs em constraints/decisions)
- `lost_constraints_rate` (testes de trajetória)
- `rehydrate_pointer_rate` (quantos pointers foram reabertos)

> Sessão contínua “saudável” costuma ter: fill ratio estável, compaction menos frequente porém mais cirúrgico, e drift quase zero.

---

## 6) Nota de confiança e limitações

- O *range* 55%–70% (default 60%) é uma **heurística operacional**, não um “padrão oficial” dos vendors.
- Modelos e releases mudam; por isso:
  - trate `W_steady` como **knob**,
  - rode A/B com métricas de retenção e latência,
  - e ajuste por workload (tool‑heavy → menor `W_steady`).

A evidência de degradação com contexto longo é bem suportada por literatura (*Lost in the Middle*, *RULER*), mas a “melhor fração” depende do seu tráfego e dos modelos. [^lost_in_middle_arxiv][^ruler_arxiv]

---

## Referências
[^openai_agents_sessions_js]: OpenAI Agents SDK (JS), “Sessions”, **date not found**, https://openai.github.io/openai-agents-js/guides/sessions
[^openai_agents_sessions_py]: OpenAI Agents SDK (Python), “Sessions”, **date not found**, https://openai.github.io/openai-agents-python/sessions/
[^langgraph_memory]: LangGraph Docs, “Memory”, **date not found**, https://docs.langchain.com/oss/javascript/langgraph/add-memory
[^langgraph_persistence]: LangGraph Docs, “Persistence”, **date not found**, https://docs.langchain.com/oss/javascript/langgraph/persistence
[^lost_in_middle_arxiv]: Liu et al., “Lost in the Middle: How Language Models Use Long Contexts”, arXiv:2307.03172, **Submitted 2023-07-06; last revised 2023-11-20**, https://arxiv.org/abs/2307.03172
[^ruler_arxiv]: Hsieh et al., “RULER: What's the Real Context Size of Your Long-Context Language Models?”, arXiv:2404.06654, **Submitted 2024-04-09; last revised 2024-08-06**, https://arxiv.org/abs/2404.06654
[^openai_responses_compact_ref]: OpenAI API Reference, “Compact a response (POST /v1/responses/compact)”, **date not found**, https://platform.openai.com/docs/api-reference/responses/compact
[^openai_codex_unrolling]: OpenAI, “Unrolling the Codex agent loop”, **2026-01-23**, https://openai.com/index/unrolling-the-codex-agent-loop/
