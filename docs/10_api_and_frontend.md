# 10 — API + Frontend (MVP executável para demo)

Este pack inclui um **runtime FastAPI mínimo** (`runtime/ailine_runtime/api_app.py`) que já suporta:

- Materiais do professor (store local) + `rag_search`
- Geração de planos: **Planner → Quality Gate → Refinement → Executor**
- Tutor Agents por aluno/disciplina + sessão de chat com RAG e contrato JSON

> O objetivo aqui é demo rápido e reproduzível. Em produção, você troca store local por Postgres/pgvector, adiciona auth/tenant, e coloca filas/workers.

---

## 1) Como rodar a API (local)
```bash
cd runtime
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .

export ANTHROPIC_API_KEY="..."
python -m ailine_runtime
```

API sobe em: `http://localhost:8000`

---

## 2) Endpoints implementados (MVP)

### 2.1) Materiais
#### `POST /materials`
Adiciona um material ao store local (por professor + disciplina).
```bash
curl -X POST http://localhost:8000/materials \
  -H "Content-Type: application/json" \
  -d '{
    "teacher_id": "t_123",
    "subject": "Matemática",
    "title": "Apostila Frações - Cap 1",
    "content": "Frações equivalentes... Para somar frações com mesmo denominador...",
    "tags": ["frações","bncc:EF05MA03"]
  }'
```

#### `GET /materials?teacher_id=...&subject=...`
Lista materiais (filtros opcionais).

---

### 2.2) Geração de plano (Planner → Gate → Executor)
#### `POST /plans/generate`
Entrada mínima:
- `run_id` (string para observabilidade; no hackathon pode ser um UUID do front)
- `user_prompt`
- opcional: `teacher_id` e `subject` (para habilitar `rag_search`)
- opcional: perfis de acessibilidade (turma e alunos)

Exemplo:
```bash
curl -X POST http://localhost:8000/plans/generate \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "run_demo_001",
    "user_prompt": "Crie uma aula de 40 minutos sobre soma de frações para 5º ano com prática guiada.",
    "teacher_id": "t_123",
    "subject": "Matemática",
    "class_accessibility_profile": {
      "needs": ["autism","adhd","low_vision"],
      "ui_preferences": ["low_distraction","large_print"],
      "supports": ["visual_schedule","checkpoints","movement_breaks"]
    },
    "learner_profiles": [{
      "id": "aluno_a",
      "needs": ["autism","adhd"],
      "notes": "prefere passos curtos e previsibilidade"
    }]
  }'
```

Resposta:
- `draft` (saída estruturada do Planner)
- `validation` (score + checklist + warnings/recomendações)
- `final` (resultado do Executor: exports + persistência local via `save_plan`)

---

### 2.3) Tutor Agents (por aluno / disciplina)
#### `POST /tutors`
Cria um Tutor Agent “configurado” (persistido localmente).
```bash
curl -X POST http://localhost:8000/tutors \
  -H "Content-Type: application/json" \
  -d '{
    "teacher_id": "t_123",
    "subject": "Matemática",
    "grade": "5º ano",
    "standard": "BNCC",
    "style": "socratic",
    "tone": "calmo, paciente, encorajador",
    "student_profile": {
      "name": "Aluno A",
      "needs": ["autism","adhd"],
      "strengths": ["gosta de jogos"],
      "accommodations": ["agenda visual","checkpoints","texto > áudio"]
    },
    "tags": ["frações"],
    "auto_persona": true
  }'
```

#### `GET /tutors/{tutor_id}`
Recupera spec do tutor.

#### `POST /tutors/{tutor_id}/sessions`
Cria sessão de chat (memória curta persistida localmente).

#### `POST /tutors/{tutor_id}/chat`
Envia uma pergunta do aluno. O tutor:
- usa `rag_search` quando necessário
- responde com JSON (`TutorTurnOutput`) com campos acessíveis (passos, checagem de compreensão, opções de resposta, etc.)

---

## 3) Frontend sugerido (para 3 minutos de demo)
MVP de UI (1 página já resolve):
1) Upload/colagem de material (chama `/materials`)
2) Wizard de geração (chama `/plans/generate`)
3) Viewer do run:
   - timeline Planner → Gate → Refinement → Executor
   - card do score + checklist
4) Viewer do plano:
   - Plano | Student Plan | Relatório | Exports (tabs)
5) Tutor:
   - seletor de aluno/tutor
   - chat com respostas estruturadas

> Você não precisa de framework pesado para o demo. Um Next.js/React ou até HTML + fetch já dá.

---

## 4) O que é stub / próximo passo
- Auth/tenant (teacher_id vem do body no MVP)
- DB Postgres (substituir store local)
- RAG real (chunking melhor, embeddings, filtros por tags/standard)
