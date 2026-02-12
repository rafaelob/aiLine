# 04 — Arquitetura de Agentes (LangGraph + DeepAgents + Claude Agent SDK)
> Objetivo: um runtime que pareça “produto de verdade” e não um script.
> A arquitetura aqui é desenhada para pontuar em **Opus 4.6 Use** e ter um demo forte.

---

## 1) Visão geral (3 camadas)

### Camada A — Workflow (LangGraph)
- Define o **estado** de uma execução (“Run”) e suas transições:
  - ingestão → planejamento → validação/score → refinamento → execução → persistência → finalização
- Benefícios:
  - execução durável,
  - reentrância (retomar run),
  - instrumentação (run_events),
  - loop controlado (refinement_iters).

### Camada B — Planner (DeepAgents + Opus 4.6)
O Planner é o “motor de planejamento” e entrega um `StudyPlanDraft` estruturado:
- objetivos,
- steps com instruções curtas e numeradas,
- **student_plan** (versão aluno),
- **accessibility_pack_draft** (adaptações + requisitos de mídia + pontos de revisão humana),
- `evidence_requests` (pedidos de evidência para RAG/currículo).

**Dica para pontuar:** injete um playbook de acessibilidade (UDL/COGA) + perfil da turma no prompt (sem PII).

### Camada C — Executor (Claude Agent SDK + Opus 4.6 + MCP)
O Executor “fecha o pacote” com governança de tools:
- roda o relatório determinístico (`accessibility_checklist`),
- gera variantes/export (`export_variant`),
- persiste tudo (`save_plan`),
- retorna `plan_id` + resumo curto para a UI.

---

## 2) Por que “Planner + Executor”?
- DeepAgents é forte para **planejar e decompor** tarefas longas (consistência).
- Claude Agent SDK é forte para **executar com tools e governança**:
  - whitelist (`allowed_tools`)
  - `permission_mode`
  - MCP servers
- LangGraph dá:
  - durabilidade e logs,
  - refinamento determinístico,
  - streaming de eventos (opcional).

---

## 3) Estado do workflow (RunState)
Campos principais:
- `run_id`
- `user_prompt`
- `class_accessibility_profile` + `learner_profiles` (dados sensíveis; sem PII)
- `draft` (StudyPlanDraft)
- `validation` (status + score + checklist + recomendações + flags)
- `final` (resultado do Executor)
- `refine_iter`

---

## 4) Quality Gate (determinístico) com score
O Quality Gate não é “mágica do modelo”. É código determinístico:

### 4.1) Regras mínimas (hard fail)
- precisa ter `steps`
- cada step precisa ter `instructions` (lista)

### 4.2) Heurísticas que vendem (soft)
- **carga cognitiva** (frases longas, densidade, etc.)
- **chunking** por janela de foco (TDAH/aprendizagem)
- **checkpoints** (critério de “feito”)
- **transições / agenda / pausas** (TEA)
- **mídia**:
  - auditiva: captions/transcript
  - visual: alt text + estrutura para leitor de tela

### 4.3) Refinement loop
Se:
- status = fail, ou
- score < 80 (config),

o workflow injeta feedback no prompt e chama o Planner novamente (até `max_refinement_iters`).

---

## 5) Tooling e governança (MCP)
Ferramentas do runtime (whitelist):
- `rag_search` (stub MVP)
- `curriculum_lookup` (stub MVP)
- `accessibility_checklist` (score + checklist + recomendações + human review flags)
- `export_variant` (gerador de exports)
- `save_plan` (persistência local MVP)

---

## 6) Onde a “capacidade do Opus 4.6” aparece de verdade
O demo que pontua é aquele em que o Opus 4.6:
- planeja com consistência (estrutura longa e coerente),
- aplica acessibilidade como restrição real,
- refina após um gate determinístico (agência),
- usa tools e produz múltiplos artefatos “produtizáveis”.


## 6) Tutor Agents (modo tutoria) — arquitetura de runtime
Além do fluxo de geração de planos, o AiLine inclui um **modo de tutoria**:

### Componentes
- **TutorAgentSpec** (persistido): disciplina + série/ano + perfil do aluno + escopo de materiais + persona.
- **TutorSession** (persistida): histórico curto, para UI e continuidade.
- **Tutor Runtime**: Claude Agent SDK + MCP tools (whitelist mínima: `rag_search`, `curriculum_lookup`).

### Por que usamos Claude Agent SDK aqui?
- Para manter **tool use** consistente (MCP) e com controles (`allowed_tools`, `permission_mode`).
- Para alinhar com o “Built with Claude Code” sem depender de um endpoint de “Claude Code API”.

### Onde está no código
- `runtime/ailine_runtime/tutoring/*`
- `runtime/ailine_runtime/materials/store.py` (materiais + busca)
- `runtime/ailine_runtime/api_app.py` (endpoints)
