# Guia de melhores práticas para **Gerenciamento de Contexto** e **Memória** em Sistemas Agênticos (LLM Agents)

> Foco: **implementação** (produção), com padrões inspirados em **Claude Code (Anthropic)**, **Codex (OpenAI)**, e nos guias anexos (OpenAI/Anthropic/Google + roadmap/MCP/RAG).  
> Linguagem: **PT‑BR**.  
> Objetivo: maximizar **qualidade** e **confiabilidade** com **custos previsíveis** (token budget), evitando *context rot*, *prompt soup* e *tool/output bloat*.

---

## Sumário

1. [Modelo mental: pool → curadoria → janela do próximo turno](#1-modelo-mental-pool--curadoria--janela-do-próximo-turno)  
2. [Padrões “copiáveis” de Claude Code e Codex](#2-padrões-copiáveis-de-claude-code-e-codex)  
3. [Context Stack e precedência](#3-context-stack-e-precedência)  
4. [Modelo de orçamento **X/Y** (separação: núcleo vs tools/RAG)](#4-modelo-de-orçamento-xy-separação-núcleo-vs-toolsrag)  
5. [System prompt: Goldilocks (mínimo que especifica tudo)](#5-system-prompt-goldilocks-mínimo-que-especifica-tudo)  
6. [Histórico (pares user/assistant) + sumarização incremental](#6-histórico-pares-userassistant--sumarização-incremental)  
7. [Tools, MCP e Tool Results: contrato, discovery e controle de explosão](#7-tools-mcp-e-tool-results-contrato-discovery-e-controle-de-explosão)  
8. [RAG: recuperação, compressão, evidência e atribuição](#8-rag-recuperação-compressão-evidência-e-atribuição)  
9. [Skills: modularização + progressive disclosure](#9-skills-modularização--progressive-disclosure)  
10. [Memória para personalização: política, camadas e governança](#10-memória-para-personalização-política-camadas-e-governança)  
11. [Memória em grafo e GraphRAG: quando/como usar](#11-memória-em-grafo-e-graphrag-quando-e-como-usar)  
12. [Blueprint implementável: componentes, pseudo‑código e checklists](#12-blueprint-implementável-componentes-pseudo-código-e-checklists)  
13. [Templates prontos (copiar/colar)](#13-templates-prontos-copiarcolar)  
14. [Anti‑padrões e correções rápidas](#14-anti-padrões-e-correções-rápidas)  
15. [Fontes (anexos) usadas como referência](#15-fontes-anexos-usadas-como-referência)

---

## 1) Modelo mental: pool → curadoria → janela do próximo turno

Pense em “contexto” como um **pool** (instruções, histórico, memórias, docs, ferramentas, evidências) do qual você **curadoria** um subconjunto para caber na janela do **próximo turno**.  
Isso implica:

- Contexto é **orçamento** (token budget), não depósito ilimitado.  
- O agente deve otimizar **sinal por token**: mais evidência útil, menos ruído.  
- Memória é o que fica **fora** da janela (DB/arquivos/grafo) e só entra quando **recuperado**.

A curadoria (context assembly) é uma etapa explícita da orquestração, e precisa ser tratada como *pipeline* com métricas, testes e “guardrails”.

---

## 2) Padrões “copiáveis” de Claude Code e Codex

### 2.1 Claude Code (Anthropic): memória hierárquica + carregamento sob demanda

Padrões que valem ouro:

- **Memória do projeto e do usuário** separadas (governança):  
  - Projeto: `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/rules/*.md`  
  - Usuário: `~/.claude/CLAUDE.md`  
  - Local (gitignored): `CLAUDE.local.md`
- **Hierarquia e precedência**: mais específico vence (ex.: regras por pasta via `paths`).
- **Progressive disclosure**: memória/arquivos adicionais carregam conforme o agente “entra” em diretórios/escopos.
- **Tool bloat control**: descrições MCP grandes podem ser “deferidas” e descobertas via busca (não carregue tudo upfront).
- **Tool output bloat control**: outputs enormes podem ser persistidos fora (arquivo) e só um *handle/summary* volta ao contexto.

### 2.2 Codex (OpenAI): instruções por arquivo (AGENTS.md) + compaction

Padrões principais:

- **AGENTS.md** com precedência root→cwd:  
  - Global: `~/.codex/AGENTS.md`  
  - Projeto: `AGENTS.md` em cada diretório do root ao cwd, com maior precedência para os mais próximos do cwd.
- **Compaction/summarization** como primitiva: resumir histórico antigo em “summary state” para manter coerência e liberar orçamento.
- **Skills** com *progressive disclosure*: carregar metadados e só carregar o corpo completo da skill quando ela for acionada.

---

## 3) Context Stack e precedência

Use uma pilha de camadas com contrato de precedência explícito:

1. **System prompt** (constituição, guardrails, formato global)  
2. **Developer prompt** (políticas do produto/tenant; tool policy; estilo)  
3. **Instruções duráveis por escopo** (AGENTS.md / CLAUDE.md / rules por path)  
4. **Skills ativas** (apenas as acionadas)  
5. **Memória recuperada** (perfil do usuário, decisões do projeto, grafo etc.)  
6. **RAG/Docs recuperados** (evidências com citação)  
7. **Histórico recente** (últimos N turns íntegros)  
8. **Estado do turno** (plano atual, budgets, critérios de aceitação, pendências)

**Regra**: camadas mais específicas (escopo menor/mais recente/mais próxima do cwd) sobrescrevem as genéricas, exceto guardrails de system.

---

## 4) Modelo de orçamento **X/Y** (separação: núcleo vs tools/RAG)

Você descreveu exatamente um padrão de produção que eu recomendo formalizar como **dois tetos**:

- **Cap total de orquestração**: `Y` tokens (tudo que vai na janela do modelo naquele turno)  
- **Cap do núcleo conversacional/instrucional**: `X` tokens, onde entram:
  - system prompt + developer prompt
  - regras por escopo (AGENTS/CLAUDE/rules)
  - skills ativas
  - pares de mensagens (user/assistant) e mensagens da orquestração
  - resumo(s) do histórico antigo

A diferença **`(Y - X)`** vira uma **reserva explícita** para:
- schemas e descrições de tools (ou discovery)
- tool results (resumidos)
- RAG evidência
- memórias recuperadas (vetor/grafo)

> Intuição: `X` protege a “coerência do agente” e da conversa; `Y-X` protege a capacidade de executar ferramentas e trazer evidências sem quebrar o turno.

### 4.1 Invariantes (regras duras)

1) **Nunca** exceder `Y`.  
2) **Sempre** manter o núcleo ≤ `X`.  
3) **Nunca** jogar tool results brutos grandes “dentro” do núcleo. Tool outputs pertencem ao envelope de tools/RAG.

### 4.2 Tiers de prioridade (núcleo X)

Dentro de `X`, trate tudo como itens priorizados:

**Tier 0 (não-negociável)**  
- System prompt (compacto)  
- Developer prompt (compacto)  
- Regras críticas de segurança/contrato de saída

**Tier 1 (alto valor, baixo ruído)**  
- Resumo do histórico antigo (“Rolling Summary”)  
- Últimos `N` turns íntegros (ou os mais recentes até caber)  
- Estado do turno: objetivo, constraints, definição de pronto

**Tier 2 (sob demanda)**  
- Instruções por path (AGENTS/CLAUDE/rules) relevantes para o diretório/feature atual  
- Skills: somente as acionadas

**Tier 3 (reduzível)**  
- “Chatter” e trechos redundantes do histórico  
- Descrições longas e exemplos extensos (migre para docs/skills sob demanda)

### 4.3 Estratégia de sumarização (quando X estoura)

**Regra**: ao exceder `X`, **não** comprima “qualquer coisa”: comprima **apenas** o histórico mais antigo (turns), mantendo uma **âncora** de turns recentes.

Algoritmo recomendado (determinístico):

1) Defina `N_keep` (ex.: manter últimos 8–20 turns íntegros)  
2) Calcule tokens do núcleo (sem tools): `core_tokens`  
3) Se `core_tokens > X`:
   - pegue turns antigos (do mais antigo para o mais novo, antes do bloco “recent”)  
   - mova-os para um buffer de compressão  
   - gere um **Rolling Summary** (ver template)  
   - substitua o bloco antigo pelo resumo (uma única mensagem sintética)  
   - repita até `core_tokens <= X`

**Características do Rolling Summary**:
- objetivo atual + histórico relevante
- decisões tomadas e justificativas
- constraints e preferências do usuário
- “estado do mundo” (artefatos criados, links/handles)
- pendências e próximos passos

> Observação importante: se você mantiver “notas duráveis” versionadas (DECISIONS/NOTES/TODO), o Rolling Summary pode ficar bem menor, porque o resumo só aponta para esses artefatos (handles).

### 4.4 Estratégia para tools/RAG (reserva Y-X)

Defina: `tool_budget = Y - X`.

Antes de chamar ferramentas, rode um **preflight**:

- estime tokens de:
  - schemas (ou descriptors) das tools necessárias
  - memória recuperada (vetor/grafo) que você planeja inserir
  - evidências RAG (quotes curtos)
  - resultados esperados (idealmente: só summary)

Se `tool_tokens > tool_budget`, aplique reduções (em ordem):

1) **Discovery** em vez de carregar schemas completos (tool search / registry compact)  
2) **Diminuir top_k** de RAG e reduzir tamanho de chunks (ou usar compressor)  
3) **Trocar tool output bruto** por `handle + summary` (persistir fora)  
4) **Paginar** ou “projetar schema” (retornar apenas campos necessários)  
5) **Programmatic tool calling** (processar resultados fora do modelo e retornar só a síntese)

### 4.5 Exemplo (com seus números típicos)

- `X = 200k` (núcleo: system+skills+histórico+orquestração)  
- `Y = 350k` (total por turno)  
- `tool_budget = 150k` (tools/RAG/memórias recuperadas)

Isso é bom para orquestrações pesadas (múltiplas tools + RAG), desde que você:
- não traga tool outputs brutos gigantes,
- e mantenha RAG como “evidência curta” (quotes + atribuição).

### 4.6 Calibração prática de X e Y

Heurísticas úteis:

- Quanto maior a variância de tool outputs, maior deve ser `Y-X`.  
- Se você faz muita engenharia de prompt (muitas skills/regras), aumente `X` **apenas** se você não consegue modularizar.  
- Para agentes de código: prefira `X` menor e investir em arquivos de projeto (AGENTS/CLAUDE) e notas duráveis, reduzindo a necessidade de “memória dentro da janela”.

---

## 5) System prompt: Goldilocks (mínimo que especifica tudo)

System prompt deve ser **estável**, **curto** e **executável** (comportamento verificável).  
Evite “prompts constitucionais quilométricos”. Use “skeleton + links/handles” para o resto.

### Template (recomendado)

```xml
<role>
  Você é um agente <papel> que ajuda <tipo de usuário> a atingir <objetivo>.
</role>

<guardrails>
  - Limites de segurança/ética (bullets curtos).
  - Se não houver evidência suficiente: use tools/RAG ou declare incerteza.
  - Não assuma sucesso sem tool result.
</guardrails>

<capabilities>
  - Ferramentas disponíveis (alto nível; sem despejar schemas).
  - Use discovery quando necessário.
</capabilities>

<process>
  - Planeje em passos curtos.
  - Execute com tools quando apropriado.
  - Verifique antes de concluir.
</process>

<response_format>
  - Estrutura esperada.
  - Regras de citação/atribuição quando usar RAG.
</response_format>
```

---

## 6) Histórico (pares user/assistant) + sumarização incremental

### 6.1 Turn como unidade de corte

Trate **turn** como: `user message + tool calls + tool results + assistant/orchestrator outputs`.  
Trimming/compaction deve operar por turn para não quebrar dependências.

### 6.2 Rolling Summary + “âncora” de turns recentes

- Mantenha últimos `N_keep` turns íntegros.  
- Todo o resto vira Rolling Summary, atualizado incrementalmente.  
- Para tarefas longas, adicione um “Decision Log” fora do contexto (arquivo/DB).

---

## 7) Tools, MCP e Tool Results: contrato, discovery e controle de explosão

### 7.1 Tools como contrato

Tools precisam de:
- inputs/outputs tipados (preferir JSON)  
- timeouts, retries, rate limit  
- redaction e least privilege  
- logs e traces  
- testes de trajetória (agent eval) com tool mocks

### 7.2 Tool registry grande: discovery por demanda

Não injete dezenas de tools no contexto. Use:
- um catálogo compacto (nomes + 1 linha)  
- uma tool `tool.search()` para descobrir e então carregar schema completo só da tool escolhida

### 7.3 Tool results grandes: “handle + summary”

Regra: tool result bruto não deve “tomar” sua janela.  
Padrão recomendado:

- persistir o bruto em arquivo/DB
- inserir no contexto:
  - *status*
  - 3–7 fatos
  - link/handle para o bruto

---

## 8) RAG: recuperação, compressão, evidência e atribuição

### 8.1 Pipeline mínimo robusto

1) Query rewrite (opcional)  
2) Recuperação ANN (top_k alto)  
3) Re-rank (top_k menor)  
4) Compressão (quotes curtos)  
5) Resposta com atribuição + gaps

### 8.2 Formato recomendado do resultado de RAG (em contexto)

```json
{
  "query": "...",
  "top_evidence": [
    {
      "source_id": "doc:XYZ",
      "title": "...",
      "date": "YYYY-MM-DD",
      "relevance": 0.83,
      "quote": "trecho curto",
      "notes": "interpretação mínima"
    }
  ],
  "coverage_gaps": ["..."],
  "next_actions": ["..."]
}
```

---

## 9) Skills: modularização + progressive disclosure

### 9.1 O que é uma skill (de verdade)

Skill = instrução reutilizável + gatilhos + ferramentas permitidas + formato de saída + exemplos mínimos.

### 9.2 Progressive disclosure (essencial)

- Carregue **metadados** das skills no núcleo (barato)  
- Carregue o corpo do `SKILL.md` **somente quando** a skill for acionada

---

## 10) Memória para personalização: política, camadas e governança

### 10.1 Camadas de memória

- **Short-term**: Rolling Summary (na janela, sob `X`)  
- **Durable notes**: DECISIONS/NOTES/TODO (fora da janela, versionado)  
- **User profile**: preferências estáveis (consentidas)  
- **Vector memory**: recall semântico (fuzzy)  
- **Graph memory**: relações e multi-hop (dependências)  
- **Ledger/audit**: rastreabilidade (especialmente tools destrutivas)

### 10.2 Política de escrita (quando gravar)

Grave memória persistente apenas se for:
- estável e recorrente
- útil em conversas futuras
- não sensível (ou com consentimento)
- com proveniência + TTL/freshness

---

## 11) Memória em grafo e GraphRAG: quando e como usar

### 11.1 Quando grafo ganha

- perguntas multi-hop (“o que depende do quê?”)
- rastrear decisões e impacto
- entidades e relações (usuário ↔ projeto ↔ componente ↔ tool)

### 11.2 Modelo simples (recomendado)

**Nós**: User, Project, Repo, Component, Decision, Artifact, Tool, Preference  
**Arestas**: WORKS_ON, DEPENDS_ON, DECIDED_IN, USES, PREFERS

Campos obrigatórios em nós/arestas:
- `source`, `timestamp`, `confidence`, `ttl_days`

### 11.3 Recuperação do grafo (para contexto)

1) entity linking do input  
2) seed set (nós)  
3) expansão 1–2 hops com limites  
4) sumarização do subgrafo (“graph slice”) para inserir no `tool_budget`

---

## 12) Blueprint implementável: componentes, pseudo‑código e checklists

### 12.1 Componentes

- `TokenCounter(model)`  
- `ContextAssembler(X, Y)`  
- `Summarizer(rolling_summary_spec)`  
- `ToolContextManager(tool_budget, discovery, storage)`  
- `MemoryManager(vector_store, graph_store, policy)`  
- `DurableNotesStore` (files/DB)  
- `EvalSuite` (context regression + tool trajectory)

### 12.2 Pseudo‑código (núcleo)

```python
def build_turn_context(request, state):
    X = state.core_budget
    Y = state.total_budget
    tool_budget = Y - X

    core = assemble_core(state, request)  # system+dev+rules+skills+history+rolling_summary+turn_state

    while tokens(core) > X:
        core = compress_old_turns_into_rolling_summary(core, state)

    tool_ctx_plan = plan_tool_context(request, state)
    tool_ctx = assemble_tool_context(tool_ctx_plan, state)

    while tokens(tool_ctx) > tool_budget:
        tool_ctx = reduce_tool_context(tool_ctx, state)  # discovery, top_k, quote_size, handle+summary, pagination

    final = core + tool_ctx
    assert tokens(final) <= Y

    return final
```

### 12.3 Checklists de produção

- [ ] Medir tokens por camada (telemetria)  
- [ ] Testes de regressão: “mesmo input, mesmo contexto curado”  
- [ ] Tool outputs sempre com summary + handle  
- [ ] RAG sempre com evidência curta e gaps  
- [ ] Memória persistente com TTL + proveniência  
- [ ] Rules/skills com progressive disclosure  
- [ ] Compaction/summarization determinístico (template fixo)

---

## 13) Templates prontos (copiar/colar)

### 13.1 AGENTS.md / CLAUDE.md (instruções de projeto)

```md
# Objetivo do projeto
...

# Convenções
- ...

# Regras de segurança/compliance
- ...

# Fluxos comuns
- ...

# Escalação
- ...
```

### 13.2 SKILL.md

```md
---
name: "triage_bug_report"
description: "Triage de bug: reproduzir, coletar logs, sugerir fix/next steps."
activation:
  - when: "user reports bug"
tools:
  allow: ["repo.search", "logs.query"]
outputs:
  format: "markdown"
---

# Objetivo
...

# Passos
1) ...
2) ...

# Quando NÃO usar
...
```

### 13.3 Rolling Summary (formato recomendado)

```md
## ROLLING_SUMMARY
- Goal: ...
- Constraints: ...
- Decisions:
  - ...
- Current state:
  - Artifacts/handles: ...
- Open issues:
  - ...
- Next steps:
  - ...
```

### 13.4 Tool Result Summary

```md
## TOOL_RESULT_SUMMARY
- Tool: <name>
- Status: success|error
- Key facts:
  - ...
- Artifacts:
  - <handle/path/url>
- Next action:
  - ...
```

### 13.5 Memory Write Candidate (para governança)

```json
{
  "type": "memory_write_candidate",
  "scope": "user|project|org",
  "payload": {
    "fact": "...",
    "category": "preference|decision|workflow|entity_relation",
    "source": "chat:...#turn...",
    "confidence": 0.8,
    "ttl_days": 180
  },
  "requires_user_confirmation": true
}
```

---

## 14) Anti‑padrões e correções rápidas

- **Prompt soup** → reduza system; mova detalhes para skills + files por path  
- **Tool stuffing** (50 tools na janela) → discovery + catálogo compacto  
- **Tool output bruto** → handle+summary; paginar/projetar campos  
- **RAG dumping** → re-rank + quotes curtos + gaps  
- **Memória stale** → TTL + compaction + proveniência  
- **Loops** → stop criteria + budgets + “no progress detector”

---

## 15) Fontes (anexos) usadas como referência

- `Guide_Effective_Context_Engineering_Anthropic.md`  
- `Guide_Effective_Agents_Anthropic.md`  
- `guide_effective_tools_mcp_anthropic.md`  
- `context_engineering_openai.md`  
- `guide_OpenAI_Agents.txt`  
- `Google_Guide_Agents.md`  
- `AGENTS_MCP_RAG_MEMORY_CONTEXT_ROADMAP.txt`  
- `model_context_protocol_extensive_guide.md`  
- `Agentic_Design_Patterns.md`  

---

### Notas finais (pragmáticas)

1) Se você fizer **orçamento explícito X/Y**, metade dos “problemas mágicos” de agentes some.  
2) Se você separar *núcleo* de *tools/RAG*, você ganha previsibilidade e consegue evoluir sem “quebrar” o agente.  
3) A chave é: **progressive disclosure + summaries determinísticos + handles para dados grandes**.
