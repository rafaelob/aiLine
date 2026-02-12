# 24 — Tutor Agents (por aluno) + Materiais do Professor (RAG) — Inclusão por padrão

> Objetivo: permitir que o professor crie **um agente tutor por aluno (ou grupo)** já configurado com:
> - disciplina + série/ano,
> - materiais/documentos do professor,
> - necessidades funcionais de acessibilidade (TEA, TDAH, dificuldades de aprendizagem, auditiva, visual),
> - estilo de tutoria (socrático/coach/direto).

Este recurso é o “modo laboratório” do AiLine — e é perfeito para demo porque:
- mostra **agência real com tools** (RAG),
- mostra **personalização** (por aluno),
- mostra **inclusão** (formato e scaffolding),
- e mantém o professor “no loop” (flags de revisão humana).

---

## 1) O que é um Tutor Agent no AiLine

Um Tutor Agent é um artefato persistido que inclui:

- `teacher_id`
- `subject`, `grade`, `standard` (BNCC|US)
- `student_profile` (sem PII; necessidades funcionais, preferências, acomodações)
- `materials_scope` (quais materiais do professor o tutor pode usar)
- `persona` (system prompt e contrato de resposta)

No runtime (MVP), isso está modelado em:

- `runtime/ailine_runtime/tutoring/models.py`
- `runtime/ailine_runtime/tutoring/builder.py`

---

## 2) Materiais do professor (MVP) + RAG de verdade (sem pgvector)

Para ter demo funcionando **sem infraestrutura**, mantemos um store local:

```
.local_store/
  materials/{teacher_id}/{subject_slug}/{material_id}.json
```

Cada material guarda:
- título, disciplina, tags
- conteúdo (texto)
- data de criação

A busca do `rag_search` usa uma heurística simples (token overlap em chunks).
Em produção, substitua por:
- ingestão de PDFs/slides
- embeddings
- Postgres + pgvector ou um index vetorial

Arquivos relevantes:
- `runtime/ailine_runtime/materials/store.py`
- `runtime/ailine_runtime/tools/registry.py` (`rag_search_handler`)

---

## 3) Contrato de resposta do Tutor (para UI e acessibilidade)

O tutor responde em **JSON estruturado** (`TutorTurnOutput`) com:

- `answer_markdown` (texto principal)
- `step_by_step` (micro-passos)
- `check_for_understanding` (1–3 perguntas)
- `options_to_respond` (oral/desenho/múltipla escolha/etc)
- `self_regulation_prompt` (pausa/autorregulação)
- `citations` (quando usar RAG; ex.: `Apostila Frações#2`)
- `teacher_note` e `flags` (ex.: revisão humana)

Isso permite:
- UI consistente,
- “modo baixa distração”,
- export para TTS,
- e auditoria do que foi usado como evidência.

---

## 4) Acessibilidade no Tutor: como “englobamos tudo”

O Tutor inclui um playbook operacional (UDL + COGA + adaptações por necessidade):

- TEA: mini-agenda, transições explícitas, linguagem literal, opções A/B, pausas
- TDAH: chunking, checkpoints, pausas de movimento, timers
- Dificuldades de aprendizagem: exemplo primeiro, glossário, frases curtas, alternativas de resposta
- Auditiva: texto como canal principal, legendas/transcrição para mídia
- Visual: headings/listas, alt text, large print, audio script

Arquivo:
- `runtime/ailine_runtime/tutoring/playbooks.py`

---

## 5) API (MVP) — endpoints para demo

Arquivo:
- `runtime/ailine_runtime/api_app.py`

Endpoints:
- `POST /materials` — adiciona material (texto)
- `GET /materials` — lista materiais
- `POST /tutors` — cria Tutor Agent
- `GET /tutors/{tutor_id}`
- `POST /tutors/{tutor_id}/sessions` — cria sessão
- `POST /tutors/{tutor_id}/chat` — conversa

**Importante:** este MVP não tem auth.
Em produção:
- autenticação professor/aluno
- autorização por `teacher_id`
- controle de acesso a materiais e sessões
- logging e redaction de dados sensíveis

---

## 6) Como isso se conecta às funcionalidades “iniciais” do AiLine

O tutor é “o mesmo produto” com outro modo:

- usa os mesmos materiais (RAG)
- pode usar os mesmos alinhamentos curriculares (BNCC/US)
- pode gerar quizzes/atividades/rubricas (skills existentes)
- compartilha o mesmo princípio de acessibilidade first-class

Skills já existentes (Claude Code):
- `socratic-tutor`
- `quiz-generator`
- `study-plan-personalizer`
- `curriculum-*-align`
- `accessibility-adaptor`

---

## 7) Roadmap (pós-hackathon)

- Ingestão de PDFs/slides + OCR quando necessário
- Index vetorial (pgvector) + citações formais
- Modo “parent/guardian” e relatórios
- Avaliações calibradas e rastreio de progresso
- AAC/pictogramas e suporte Libras (com revisão humana)
