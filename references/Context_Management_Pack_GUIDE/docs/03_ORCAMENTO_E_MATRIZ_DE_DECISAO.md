# 03 — Orçamento de Contexto e Matriz de Decisão (workload → estratégia)

## Por que orçamento por tokens (e não “N turnos”)

“Guardar os últimos 10/20/30 turnos” falha porque:
- Turnos têm tamanhos variáveis (um tool dump pode valer 200 turnos).
- O que importa é **custo de atenção** e prioridade — não contagem de mensagens.
- Em janelas grandes (ex.: 200k–350k), o risco é “context rot” (diminuição de utilidade do meio do contexto), então volume sem curadoria pode piorar.[^anthropic_context_engineering]

**Regra SOTA:** o histórico entra como **fonte**, não como “verdade”. O pipeline decide o que entra por **budget + prioridade + relevância**.

---

## Modelo de orçamento: do XY ao “budget vector”

O playbook upstream que você trouxe formaliza uma ideia importante: separar orçamento em **X (core invariável)** e **Y (janela total)**.

Aqui nós generalizamos para um **vetor de budgets por slice**, mantendo a intuição XY:

- `Y_total_input` = orçamento total para **input** (janela do modelo menos reserva para output e margem de segurança).
- `X_core` = fatias invariantes/semivariantes (system/dev/policies, registry de skills/tools, state).
- `Y_dynamic` = fatias voláteis (histórico recency, RAG, tool results).

> **SOTA:** XY é o “macro”. O que te dá flexibilidade real é o **micro**: budget por slice + perfis.

### Fórmula base (independente do vendor)
1. Descubra `window_tokens` do modelo (capability).
2. Defina:
   - `reserve_output_tokens` (para resposta)
   - `safety_margin_tokens` (para evitar overflow por variações)
3. Compute:
   - `Y_total_input = window_tokens - reserve_output_tokens - safety_margin_tokens`

Em OpenAI, existe endpoint para contar tokens de um input antes de chamar o modelo (`POST /v1/responses/input_tokens`), útil para o ledger e para validação preventiva.[^openai_token_counting]

---

## Modo de sessão: multi‑sessão vs sessão contínua (impacta *quando* e *quanto* compactar)

Na prática, existem dois “topos” de conversa/orquestração:

- **Multi‑sessão (episódica):** cada chat/ticket/thread abre uma nova sessão e reidrata apenas memória durável e artefatos necessários.
- **Sessão contínua (thread única longa):** a mesma sessão permanece viva por muito tempo e acumula histórico + outputs.

**Por que isso importa:** em sessão contínua, você tem maior risco de:
- degradação por contexto muito longo (*long-context brittleness*),
- drift por compaction repetido,
- e explosões de tool/RAG que forçam “thrash” de compaction.

**Recomendação SOTA:** usar orçamento por *watermarks* (alvo sustentável + teto duro) e alternar entre perfis **steady/burst**.

➡️ Veja `docs/03A_SESSOES_MULTI_VS_CONTINUA.md` para:
- heurística inicial (ex.: operar em ~60% do window em sessão contínua),
- desenho de perfis steady/burst,
- e métricas para detectar degradação.

---

## Matriz de decisão: workload → estratégia de contexto

Abaixo, um mapa prático. **Não existe uma única estratégia**: você escolhe por objetivo/custo/risco.

### Estratégias base (biblioteca)

**S0 — Baseline: Recency + sumário prefixo**
- Mantém recency window por tokens + um sumário do prefixo.
- Bom para chat moderado, baixo tool/RAG.

**S1 — Estado estruturado + recency mínima**
- Mantém `STATE_JSON` (decisões/constraints/todos) como fonte de verdade.
- Reduz dependência do transcript.

**S2 — Tool/RAG first-class (Evidence + Tool digests + pointers)**
- Tool results e RAG entram como **digests** e pointers, não dumps.
- Ideal para tool-heavy e long-horizon.

**S3 — Retrieval-backed history (“history as corpus”)**
- O transcript completo vive fora da janela; a janela recebe apenas:
  - recency mínima
  - sumários
  - retrieval de turnos relevantes (por embedding/keyword)
- Útil para conversas muito longas.

**S4 — Vendor compaction**
- Usa compaction quando suportado para reduzir histórico e manter estado essencial.
- OpenAI: `/responses/compact` retorna janela canônica com item opaco.[^openai_compaction]
- Anthropic: compaction no ecossistema Claude.[^anthropic_compaction]

**S5 — Multi-agent partitioning (dual handoff: transfer vs delegate)**
- Manager retém core + state + objective.
- Workers recebem context packs específicos (sem duplicar tudo).
- **Dual handoff**: 
  - **Delegate-first** (agents-as-tools): payload tipado + output estruturado.
  - **Transfer** (handoff de controle): histórico filtrado + `STATE_JSON`.
- Handoffs estruturados e shared memory retrieval-backed.

> Ver `docs/10A_DUAL_HANDOFF_TRANSFER_VS_DELEGATE.md` para contrato e critérios.

---

### Decision matrix (resumida)

> Use como “chooser”. Perfis concretos em `docs/04_PROFILES_DE_ORCAMENTO.md`.

| Workload | Recomendação | Benefícios | Riscos / falhas | Custo/latência |
|---|---|---|---|---|
| **Single-agent, tool-light, curto** | S0 + S1 | simples, robusto | sumário drift; perder nuance | baixo |
| **Single-agent, tool-heavy** | S2 + S1 | reduz bloat de tool results; mais determinismo | summarization errada de tool results; pointer inválido | médio (summaries) |
| **RAG-heavy (pesquisa/citações)** | S2 (Evidence Pack) + S3 | fidelidade, auditabilidade | retriever ruim; citações incompletas | médio–alto (retrieval+rerank) |
| **Long-horizon (dias/semanas)** | S1 + S3 + S4 (se disponível) | escala de histórico; restart seguro | drift acumulado; stale memory | médio (compaction) |
| **High-stakes (financeiro/saúde/segurança)** | S1 + S2 + gates (human-in-the-loop) | rastreio, controle | over-constraint; mais latência | alto (gates+auditoria) |
| **Multi-agent, tool-heavy** | S5 + S2 + shared state retrieval | evita duplicação; paralelismo | handoff ruim; inconsistência de estado | médio–alto |
| **Janela pequena (≤ 32k)** | S1 + S3 + agressivo em digests | caber no orçamento | perda de detalhe | médio |
| **Janela grande (≥ 200k)** | S2 + S1 + caching + compaction | reduz context rot; custo controlado | complacência (“caber ≠ útil”) | médio |

---

## Failure modes principais (e como mitigar)

1. **Summary drift** (sumário muda constraints)  
   Mitigação: sumário **estruturado**, com campos imutáveis (DECISIONS/CONSTRAINTS). Valide com checks de consistência.

2. **Lost constraints** (o agente esquece requisito antigo)  
   Mitigação: `STATE_JSON` como fonte de verdade + testes de trajetória (“regressão”).

3. **Context poisoning / prompt injection via RAG/tools**  
   Mitigação: “untrusted boundary” + instruções explícitas + allowlists/approvals (MCP) + stripping de instruções em dados.[^mcp_spec][^openai_agent_safety]

4. **Tool bloat** (tool results saturam Y_dynamic)  
   Mitigação: output shaping + digests + pointers + limites por tool + paginação.

5. **RAG bloat** (retriever devolve muita coisa)  
   Mitigação: dois estágios (recall → rerank), MMR/diversidade, snippet packing e quotas por fonte.

---

## Guia rápido para o seu cenário 350k (200k core + 150k tools)

Você pode suportar **múltiplos perfis** com a mesma infra:

- **Profile “tool_heavy_350k”**: reduz system+skills, aumenta tool results e RAG  
- **Profile “chatty_350k”**: aumenta recency/histórico (mas mantém tool budgets baixos)  
- **Profile “high_stakes_350k”**: aumenta evidence pack + logs, reduz recency irrelevante  

O importante é que todos os perfis:
- usem **token ledger por slice**,
- tenham **gates de overflow** (pré‑contagem),[^openai_token_counting]
- e instrumentem decisões do assembler (por que cada slice entrou).

---

## Referências
[^anthropic_context_engineering]: Anthropic Engineering, “Effective context engineering for AI agents”, **Published Sep 29, 2025**, https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
[^openai_token_counting]: OpenAI API Docs, “Counting tokens”, **date not found**, https://developers.openai.com/api/docs/guides/token-counting
[^openai_compaction]: OpenAI API Docs, “Compaction”, **date not found**, https://developers.openai.com/api/docs/guides/compaction
[^anthropic_compaction]: Claude API Docs, “Compaction”, **date not found**, https://platform.claude.com/docs/en/build-with-claude/compaction
[^mcp_spec]: Model Context Protocol, “Specification (Version 2025-06-18)”, **2025-06-18**, https://modelcontextprotocol.io/specification/2025-06-18
[^openai_agent_safety]: OpenAI API Docs, “Safety in building agents”, **date not found**, https://developers.openai.com/api/docs/guides/agent-builder-safety
