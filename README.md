# AiLine — Runtime agentico para planejar e adaptar aulas com acessibilidade “de verdade”

**AiLine = Adaptive Inclusive Learning — Individual Needs in Education**
**Opus 4.6 + DeepAgents (Planner) + Claude Agent SDK (Executor) + LangGraph (workflow)**

Este repositório é um **pack de documentação + scaffolding de runtime** para construir o AiLine durante o hackathon **Built with Opus 4.6: a Claude Code Hackathon**.

## O que é o AiLine (MVP com foco em inclusão)
AiLine transforma materiais reais de sala de aula (apostilas, PDFs, slides, links) em:

- **Planos de aula e trilhas de estudo** alinhadas ao currículo (**BNCC/US**),
- Um **Student Plan** (versão aluno) com linguagem simples, passos curtos, glossário e opções de resposta,
- Um **Accessibility Pack** por plano, com adaptações para:
  - **Autismo (TEA)** (previsibilidade, transições, sensorial),
  - **TDAH** (chunking, timers, pausas, checkpoints),
  - **Dificuldades de aprendizagem** (scaffolding, exemplos, glossário, alternativas),
  - **Deficiência auditiva** (legendas/transcrições, redundância visual),
  - **Deficiência visual/baixa visão** (estrutura semântica, alt text, large print, TTS),
- Um **Relatório determinístico de acessibilidade** (score, checklist, warnings, recomendações e “human review flags”).

> A ideia não é “substituir o professor”. É **amplificar o julgamento pedagógico**: o professor aprova, edita e decide — o agente faz o trabalho pesado de síntese, estrutura, variações e checagens.

---

## 1) O ponto central do hackathon (runtime, não dev)
Como dev, você já vai usar o **Claude Code** para desenvolver. Para pontuar no evento, o que importa no runtime é:

- **Opus 4.6 como cérebro principal** (planeja → valida → refina → executa),
- **Agência real com tools** (MCP tools + logs + outputs estruturados),
- Um demo que prova **Impacto** (inclusão) e **Execução** (pipeline confiável com Quality Gate).

---

## 2) Arquitetura recomendada (Planner + Quality Gate + Executor)

### Planner (DeepAgents + Opus 4.6)
- Decompõe a tarefa, monta um `StudyPlanDraft` estruturado.
- Já entrega:
  - plano (steps),
  - **student_plan** (versão aluno),
  - **accessibility_pack_draft** (adaptações + requisitos de mídia + pontos de revisão humana).

### Quality Gate (determinístico)
- Aplica checklist e heurísticas:
  - passos e instruções curtas,
  - chunking e checkpoints (TDAH/aprendizagem),
  - transições/pausas/agenda (TEA),
  - requisitos de mídia (captions/transcript/alt text),
  - estimativa de carga cognitiva e score.
- Se score ficar baixo, o workflow injeta feedback e pede refinamento (até `N` iterações).

### Executor (Claude Agent SDK + Opus 4.6 + MCP tools)
- Roda o relatório determinístico (`accessibility_checklist`),
- Gera exports com `export_variant` (por default):
  - `standard_html`
  - `low_distraction_html`
  - `large_print_html`
  - `high_contrast_html`
  - `dyslexia_friendly_html`
  - `screen_reader_html` (skip link + landmarks)
  - `visual_schedule_html` (cards)
  - `student_plain_text` (texto simples)
  - `audio_script` (TTS)
- Persiste tudo com `save_plan`.

---

## 3) Onde está tudo
- `docs/` — documentação completa (visão, features, arquitetura, dados, API, acessibilidade, demo).
- `runtime/` — runtime executável (Planner DeepAgents + Quality Gate + Executor Agent SDK + workflow LangGraph).
- `.claude/` — settings + **skills** para usar Claude Code no desenvolvimento.
- `skills/` — espelho open-source das skills (útil para leitura e também para o runtime).

> Runtime: o Planner/Persona (DeepAgents) carrega skills via `skills=[...]` quando habilitado (ver `.env.example`).


---

## 4) Quickstart (runtime local)
Este repo é um pack hackathon (docs + runtime MVP). Para rodar a API local:

```bash
cd runtime
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .
```

Sete sua chave (runtime local/CI):
```bash
export ANTHROPIC_API_KEY="..."
# (opcional) skills no runtime
# export AILINE_SKILL_SOURCES="../.claude/skills,../skills"
```

---

## 5) Como vender o demo em 3 minutos
Veja `docs/16_demo_script.md`.

Resumo da narrativa:
1) Input real (materiais + perfil de acessibilidade).
2) Pipeline visível (Planner → Quality Gate (score) → Refinement → Executor (tools)).
3) Output “wow”: plano + **student plan** + **exports** + relatório com score e recomendações.



## Tutor Agents (agentes de tutoria por aluno/disciplinas)
Além de gerar planos de aula, o AiLine inclui scaffolding para o professor **criar um Tutor Agent por aluno** (ou grupo) — configurado por:

- **Disciplina + série/ano** (ex.: Matemática — 5º ano),
- **Materiais do professor** (documentos/textos adicionados ao store local; em produção → RAG/pgvector),
- **Necessidades funcionais de acessibilidade** (TEA, TDAH, dificuldades de aprendizagem, auditiva, visual),
- Estilo (socrático/coach/direto) e tom.

O tutor responde com **saída estruturada (JSON)** para a UI: resposta + passo-a-passo + checagem de compreensão + opções de resposta + citações dos materiais (quando usados).

## Rodar o runtime (API FastAPI) — MVP para demo
> **Nota:** este pack é scaffolding. Em produção, troque o store local por Postgres/pgvector e adicione autenticação.

Pré-requisitos:
- Python 3.11+
- `ANTHROPIC_API_KEY` (para Opus 4.6)

Com `uv` (recomendado):
```bash
cd runtime
uv sync
export ANTHROPIC_API_KEY="..."
python -m ailine_runtime
```

Endpoints principais:
- `POST /materials` — adiciona material (texto) do professor
- `POST /plans/generate` — Planner → Gate → Executor (gera plano + acessibilidade + exports)
- `POST /tutors` — cria Tutor Agent (por aluno/necessidades/disciplinas)
- `POST /tutors/{tutor_id}/sessions` — cria sessão de tutoria
- `POST /tutors/{tutor_id}/chat` — conversa (tutor usa `rag_search` nos materiais)

## Licença
Este projeto está sob **MIT License** (ver `LICENSE`).
