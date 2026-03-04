# Guia completo: Contexto + Memória + Skills/MCP (X/Y)

Este playbook descreve um desenho de agente que **escala para sessões longas** sem perder controle de:
- orçamento de tokens,
- segurança (aprovações, vazamento de dados),
- qualidade (traço, evidências, decisões),
- personalização (memória durável com governança).

A ideia central é tratar a janela de contexto como **um recurso finito** e aplicar um “scheduler” explícito:

- **X = Core Budget**: “núcleo do turno” (o que sempre precisa estar presente).
- **Y = Total Budget**: teto total do turno.
- **Y − X = Tool/RAG/Memory Budget**: espaço *reservado* para ferramentas, evidência e contexto recuperado.

> Este guia foi atualizado para refletir práticas de ponta e recursos que surgiram/amadureceram nos últimos ciclos (por exemplo: **compaction server‑side**, **token counting endpoint**, **prompt caching**, **integração MCP nativa**, **skills com `SKILL.md`**, etc.).  
> Veja `docs/REFERENCIAS_OFICIAIS.md`.

---

## Como ler

1) **Comece aqui**: `01_XY_budget_model.md`  
   - decisões, fórmulas e heurísticas para escolher X e Y
   - como “pagar” tool schemas/outputs sem destruir o core

2) **Integração com o mundo real**: `03_skills_mcp_integration.md`  
   - skills (progressive disclosure)  
   - MCP (tools/resources/prompts, transportes e segurança)  
   - como não “inundar” o prompt com catálogos gigantes

3) **Memória para personalização**: `04_memory_graph.md`  
   - o que é seguro armazenar e como  
   - grafo + proveniência + TTL  
   - *write policy* e confirmação do usuário

4) **Loop de orquestração**: `05_orchestration_reference.md`  
   - onde entram budgets, compaction, RAG, tools e memória  
   - observabilidade (ledger) e testes

5) **Operação/produção**: `06_checklists.md` + `07_templates.md`

---

## Princípios de desenho

### 1) Contexto não é banco de dados
Janela de contexto é **working set**, não histórico completo.  
A sessão precisa de persistência fora do prompt (DB, arquivos, artefatos, stores).

### 2) Separar “durável” de “efêmero”
- **Durável**: políticas, regras do projeto, skills selecionadas, memória estável.
- **Efêmero**: tool outputs brutos, HTML grande, logs, etc.

### 3) “Handles” para payload grande
Outputs grandes vão para **artefatos** (arquivo/DB) e entram no prompt apenas como:
- resumo compacto,
- metadados,
- handle para referência.

### 4) “Sinal por token” como métrica
Cada bloco do contexto precisa justificar:
- por que está aqui?
- qual decisão melhora?
- qual risco reduz?

### 5) Caching e prefix‑stability
Quando houver suporte do provedor, maximize cache mantendo o prefixo estável:
- system/dev/regras/índices no começo,
- conteúdo variável no final.

---

## Onde cada componente vive

- **System + Developer**: regras e metas “não negociáveis”.
- **Durable rules**: `AGENTS.md`, `CLAUDE.md`, regras por path.
- **Skills**: catálogo mínimo + ativação sob demanda via `SKILL.md`.
- **Histórico**: apenas “âncoras” + **rolling summary** (ou compaction server‑side).
- **Tools/MCP/RAG**: sempre dentro do “tool budget” (Y−X), com compressão.
- **Memória**: store externo (vetor/grafo), com recuperação controlada e governança.

---

## Próximo passo

Vá para `01_XY_budget_model.md`.
