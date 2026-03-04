# Memória para personalização (incluindo memória em grafo)

A “memória” do agente não é uma coisa só. Em agentes de produção, você precisa de:

- **Working memory** (efêmera): o que está no prompt agora.
- **Session memory**: estado da sessão (fora do prompt), como histórico completo e artefatos.
- **Long‑term memory** (durável): preferências, perfil, decisões estáveis, conhecimento do projeto — sempre com governança.

Este documento foca em long‑term memory e como recuperá‑la de forma controlada dentro do modelo X/Y.

---

## 1) Taxonomia prática de memória

### 1.1 O que vale armazenar
**Geralmente vale**:
- preferências estáveis (idioma, tom, formato),
- contexto do projeto (stack, restrições, padrões),
- decisões arquiteturais (com rationale),
- entidades estáveis (nomes, IDs internos, relações),
- “como o usuário gosta” de receber respostas.

**Geralmente NÃO vale**:
- detalhes transitórios de uma tarefa do dia,
- logs extensos,
- tokens/segredos,
- PII sensível sem consentimento explícito,
- estados que mudam a cada turno.

### 1.2 Memória como *produto* (governança)
Memória é “dados do usuário”, então você precisa de:
- política de retenção (TTL),
- proveniência (de onde veio),
- controle de escrita (confirmação),
- correção/remoção (direito de atualizar/expirar),
- minimização (guardar só o necessário).

---

## 2) Modelo X/Y aplicado à memória

- **Recuperação de memória** deve ser tratada como uma *tool*:
  - ela consome orçamento do turno,
  - e deve ser empacotada no **tool budget** (Y−X).

- **Memória recuperada** deve ser:
  - relevante para a tarefa,
  - compacta (resumo),
  - com proveniência (“de onde veio”).

---

## 3) Por que memória em grafo

Memória vetorial (embeddings) é ótima para “similaridade semântica”.
Memória em grafo é ótima para:
- **relações** (A usa B, A depende de C),
- **decisões** e seus vínculos,
- preferências estruturadas,
- explicabilidade (“por que o agente acha isso?”).

Na prática, o estado‑da‑arte tende a ser **híbrido**:
- vetor para recall,
- grafo para estrutura,
- ranking híbrido para precisão.

---

## 4) Esquema recomendado (nodes/edges)

### 4.1 Nós
- `User`
- `Preference` (key/value)
- `Project`
- `Decision`
- `Task` (quando vale)
- `Entity` (pessoas, serviços, repositórios)
- `Note` (texto curto, sempre com proveniência)

Cada nó deve ter:
- `source` (de onde veio),
- `timestamp`,
- `confidence`,
- `ttl_days` (opcional).

### 4.2 Arestas
- `PREFERS` (User → Preference)
- `OWNS` / `WORKS_ON` (User → Project)
- `DECIDED` (Project → Decision)
- `DEPENDS_ON` (Entity → Entity)
- `RELATED_TO` (Entity ↔ Entity)

---

## 5) Política de escrita (“write policy”)

### 5.1 Escreva só quando:
- a informação for estável,
- a utilidade futura for alta,
- o risco for baixo,
- houver consentimento (quando necessário).

### 5.2 Confirmação do usuário (recomendado)
Para evitar:
- “memória errada”,
- vazamento de dados sensíveis,
- drift por interpretação do modelo,

faça a escrita em dois passos:
1) o agente propõe um **MemoryWriteCandidate**
2) o usuário confirma (“posso salvar isso?”)

### 5.3 TTL e expiração
- preferências: TTL longo (ex.: 180–365 dias)
- decisões: TTL longo (ou sem TTL, dependendo do domínio)
- notas de tarefa: TTL curto (ex.: 7–30 dias)

---

## 6) Recuperação e sumarização de memória

### 6.1 Recuperar por “seed entities”
- derive entidades do turno (user, projeto, repositório, serviço),
- puxe subgrafo com BFS limitado (hops e max_nodes),
- summarize em um “GRAPH_MEMORY_SLICE”.

### 6.2 Resumo com alta densidade
O slice deve conter:
- entidades relevantes (com label),
- relações relevantes (com tipo),
- proveniência (source),
- e, se possível, “por que é relevante”.

---

## 7) Camadas de memória por arquivos (Claude Code como referência)

Em alguns ambientes de agente em IDE, regras e memória são organizadas em camadas:
- políticas gerenciadas (enterprise),
- memória do projeto (`CLAUDE.md`),
- memória do usuário (`~/.claude/CLAUDE.md`),
- memória local (`CLAUDE.local.md`),
- regras por path.

Essa abordagem é útil mesmo fora da IDE:
- separe “regras do projeto” em um arquivo versionado,
- separe “preferências do usuário” em store privado,
- e use segmentação/imports para não inflar o core.

Referência: Claude Code → *memory.md*  
https://github.com/anthropics/claude-code/blob/main/docs/memory.md

---

## 8) Checklist (memória)

- [ ] Política explícita de retenção (TTL)
- [ ] Proveniência em todos os itens
- [ ] Confirmação do usuário para writes
- [ ] Sem segredos por padrão
- [ ] Recuperação sob demanda e compacta (tool budget)
- [ ] Ranking híbrido (quando aplicável)
- [ ] Cap por turno para memória recuperada (tokens)

---

## Próximo passo

Veja `05_orchestration_reference.md` para colocar memória no loop do agente.
