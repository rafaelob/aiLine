# 25 — Manifesto: “o que tem neste zip” (sem omissões)

Este documento é um **mapa de tudo que existe no repo** e como cada peça se conecta.

> ✅ = implementado no runtime (MVP)  
> 🟨 = parcialmente (scaffold/stub)  
> ❌ = apenas documentado (roadmap)

---

## A) Objetivo do produto (AiLine)
**AiLine = Adaptive Inclusive Learning — Individual Needs in Education**

Entrega principal:
- Planejamento de aula/trilha com **acessibilidade de verdade** (TEA, TDAH, dificuldades de aprendizagem, auditiva, visual)
- Tutor Agents por aluno/disciplina com materiais do professor (RAG)

Docs: `docs/00..04`, `docs/08`, `docs/16`, `docs/24`

---

## B) Runtime (código executável)

### B1) API FastAPI (✅)
Arquivo: `runtime/ailine_runtime/api_app.py`

Endpoints:
- ✅ `/materials` (POST/GET)
- ✅ `/plans/generate` (POST)
- ✅ `/tutors` (POST)
- ✅ `/tutors/{id}` (GET)
- ✅ `/tutors/{id}/sessions` (POST)
- ✅ `/tutors/{id}/chat` (POST)

---

### B2) Workflow Planner→Gate→Executor (✅)
Arquivo: `runtime/ailine_runtime/workflow_langgraph.py`

- ✅ Planner: `planner_deepagents.py`
- ✅ Quality Gate determinístico: `accessibility/validator.py`
- ✅ Executor com tools (MCP in-process): `executor_agent_sdk.py`
- ✅ Refinement loop: `AILINE_MAX_REFINEMENT_ITERS`

---

### B3) Tools (MCP) (✅/🟨)
Arquivo: `runtime/ailine_runtime/tools/registry.py`

- ✅ `rag_search` (busca em store local) → `materials/store.py`
- 🟨 `curriculum_lookup` (stub) — retorna vazio e “note”
- ✅ `accessibility_checklist` (validação determinística)
- ✅ `export_variant` (gera HTML/text exports)
- ✅ `save_plan` (persistência local)

---

### B4) Materiais do professor (store local) (✅)
Arquivo: `runtime/ailine_runtime/materials/store.py`

- ✅ persistência em `.local_store/materials/*.json`
- 🟨 busca lexical simples (tokens) — roadmap: embeddings + pgvector

---

### B5) Acessibilidade (✅)
Arquivos:
- `runtime/ailine_runtime/accessibility/profiles.py`
- `runtime/ailine_runtime/accessibility/validator.py`
- `runtime/ailine_runtime/accessibility/exports.py`

Entrega:
- ✅ `ClassAccessibilityProfile` + `LearnerProfile`
- ✅ score/checklist/warnings/recommendations
- ✅ flags de revisão humana
- ✅ exports (low distraction, large print, screen reader, visual schedule, etc)

---

### B6) Tutor Agents (✅)
Arquivos:
- `runtime/ailine_runtime/tutoring/models.py` (schemas)
- `runtime/ailine_runtime/tutoring/playbooks.py` (playbook inclusivo)
- `runtime/ailine_runtime/tutoring/builder.py` (cria tutor spec + auto_persona)
- `runtime/ailine_runtime/tutoring/session.py` (chat com contrato JSON + RAG)
- `runtime/ailine_runtime/tutoring/__init__.py`

---

### B7) Skills no runtime (✅)
- ✅ Planner carrega skills via DeepAgents `skills=[...]`
- ✅ Persona builder também (opcional)
- ❌ Executor/Tutor via “Skill tool” (não habilitado no MVP; roadmap)

Código:
- `runtime/ailine_runtime/skills/paths.py`
- `runtime/ailine_runtime/planner_deepagents.py`
- `runtime/ailine_runtime/tutoring/builder.py`

---

## C) Skills (para Claude Code e para o runtime)

Diretórios:
- `.claude/skills/*` (source of truth)
- `skills/*` (espelho)

Skills incluídas:
- lesson-planner
- study-plan-personalizer
- socratic-tutor
- accessibility-adaptor
- accessibility-coach
- curriculum-bncc-align
- curriculum-us-align
- curriculum-mapper
- quiz-generator
- rubric-writer
- tutor-agent-builder

---

## D) Documentação (docs/00..24 + este doc)
- ✅ visão/escopo, arquitetura, flows, RAG, currículo, acessibilidade, dados, API, segurança, MVP plan, costing, observability, demo, roadmap
- 🟨 provider routing (documentado; runtime foca Anthropic)

---

## E) Testes (✅)
- `runtime/tests/test_validator.py`
- `runtime/tests/test_exports.py`

---

## F) Licença (✅)
- `LICENSE` (MIT)

---

## G) O que NÃO está no MVP (para não enganar juiz)
- ❌ Frontend pronto (só proposta)
- ❌ Autenticação / multi-tenant real (teacher_id vem do body no MVP)
- ❌ RAG por embeddings (chunking é simples)
- ❌ Curriculum lookup real (stub)
- ❌ Banco Postgres/pgvector (documentado)
