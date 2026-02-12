# 09 — Modelo de Dados (PostgreSQL) com foco em acessibilidade

## 1) Objetivo
Persistir:
- materiais,
- planos,
- execuções (runs),
- logs e evidências para auditoria e demo,
- **perfis de acessibilidade** (com cuidado, pois é dado sensível).

---

## 2) Tabelas (MVP)

### `materials`
- `id` (uuid)
- `owner_id`
- `source_type` (upload | url | paste)
- `source_ref`
- `content_text` (opcional, se armazenar)
- `content_hash`
- `metadata` (jsonb: disciplina, ano, idioma, tipo_midia)
- `created_at`

### `plans`
- `id` (uuid)
- `owner_id`
- `title`
- `standard` (BNCC | US)
- `grade`
- `topic`
- `plan_json` (jsonb)  ← artefato final (inclui variantes e relatório)
- `version`
- `created_at`

### `plan_runs`
- `id` (uuid)
- `plan_id` (nullable no início)
- `owner_id`
- `status` (queued | running | failed | done)
- `current_step`
- `input_json` (jsonb: prompt + materiais + perfil acessibilidade)
- `created_at`
- `updated_at`

### `run_events`
- `id` (uuid)
- `run_id`
- `ts`
- `type` (step | tool_call | tool_result | validation | error)
- `payload` (jsonb)
> Observação: **não** salvar PII em payload; ver doc 11.

---

## 3) Novas entidades para acessibilidade (MVP+)
### `class_accessibility_profiles` (opcional no MVP; pode ficar embutido em input_json)
- `id` (uuid)
- `owner_id`
- `name` (ex.: “Turma 5º ano — manhã”)
- `profile_json` (jsonb):
  - flags: autism/adhd/learning/visual/hearing
  - preferências: low_distraction, large_print, etc.
- `created_at`

### `learner_profiles` (anônimo / sem nome real)
- `id` (uuid)
- `owner_id`
- `class_profile_id` (nullable)
- `label` (ex.: “Aluno A — baixa visão”)
- `needs_json` (jsonb):
  - necessidades e preferências (sem diagnóstico formal)
  - assistive_tech (ex.: screen reader, captions)
  - triggers (opcional e genérico; evitar detalhes sensíveis)
- `created_at`

### `plan_variants` (separar do plan_json quando crescer)
- `id` (uuid)
- `plan_id`
- `variant_type` (standard_html | low_distraction_html | large_print_html | audio_script | ...)
- `content` (text/jsonb)
- `created_at`

### `media_assets` (placeholder)
- `id` (uuid)
- `plan_id`
- `type` (captions | transcript | audio_description | image_alt_pack)
- `uri` (text) ou `content` (text)
- `metadata` (jsonb)
- `created_at`

---

## 4) Nota de privacidade (importante)
Perfis de acessibilidade podem implicar vulnerabilidades:
- separar do log de eventos,
- criptografar em repouso,
- controlar acesso por role,
- permitir deleção/retention curta,
- evitar nomes reais no MVP (usar labels).


---

## Extensão: Tutor Agents + Materiais + Sessões (pós-MVP ou MVP com Postgres)

### Tabela `materials`
Armazena documentos/textos do professor (depois de ingestão).

Campos sugeridos:
- `id` (uuid, pk)
- `teacher_id` (uuid)
- `subject` (text)
- `title` (text)
- `tags` (text[])
- `content_text` (text)  *(ou pointer para blob store)*
- `created_at` (timestamptz)

(Em produção) campos para RAG:
- `embedding` (vector)
- `chunk_id`, `chunk_text`, `source_uri`, etc.

### Tabela `tutor_agents`
Config do tutor por aluno/grupo.

Campos:
- `id` (uuid, pk)
- `teacher_id` (uuid)
- `subject` (text)
- `grade` (text)
- `standard` (text)
- `style` (text)
- `tone` (text)
- `student_profile_json` (jsonb)  *(sem PII; necessidades funcionais)*
- `materials_scope_json` (jsonb)  *(tags/material_ids)*
- `persona_json` (jsonb)  *(system prompt + contrato de resposta)*
- `human_review_required` (bool)
- `human_review_reasons` (text[])
- `created_at` (timestamptz)

### Tabela `tutor_sessions`
Sessões de chat com histórico curto (para UI e continuidade).

Campos:
- `id` (uuid, pk)
- `tutor_id` (uuid, fk -> tutor_agents)
- `created_at` (timestamptz)
- `messages_json` (jsonb)  *(lista role/content/created_at)*

Observação LGPD:
- Tratar `student_profile_json` e `messages_json` como dado sensível/pessoal.
- Minimizar retenção e permitir deleção por professor/escola.
