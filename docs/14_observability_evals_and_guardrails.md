# 14 — Observabilidade, Evals e Guardrails (incluindo acessibilidade)

## 1) Objetivo
Transformar um pipeline agentico em algo:
- **debugável**
- **explicável**
- **apresentável** (demo)
- e que prove **inclusão** (relatório e checklist)

---

## 2) O que logar (mínimo)
Por `run_id`:
- etapas (step) e timestamps
- tool calls: name, args (sanitizado), resultado (resumo)
- validação: status + score + checklist + errors/warnings
- custo: tokens e $ estimado (se disponível)
- artefatos: draft/final JSON hashes
- **métricas de acessibilidade** (MVP):
  - `score_total`
  - `category_scores` (structure/cognitive/predictability/media)
  - `cognitive_bucket` (low/medium/high)
  - `human_review_required`
  - `variants_generated` (lista)
  - `refine_iter_count`

Armazenar em:
- `plan_runs`
- `run_events`
- `plan_artifacts` (exports / plan_json)

---

## 3) Evals (MVP)
### 3.1) Golden prompts
- 5 prompts fixos com perfis diferentes:
  - TEA sensorial
  - TDAH
  - baixa visão
  - deficiência auditiva
  - combinação (TEA+TDAH+baixa visão+auditiva)

Checar propriedades estáveis:
- schema válido,
- presença de `student_plan`,
- presença de `accessibility_pack_draft`,
- relatório com `score`,
- checklist sem itens críticos faltando.

### 3.2) Evals de regressão de acessibilidade
- Falhas críticas:
  - sem steps/instructions (hard fail)
- Falhas “soft”:
  - score < 70
  - falta de media requirements quando hearing/visual

---

## 4) Guardrails
- Whitelist de tools (Agent SDK)
- Redação/anonimização de logs (perfis são dados sensíveis)
- Bloqueio de export que inclua perfis detalhados por default
- Size limits (evitar outputs gigantes)
- “Human review required” como princípio: o agente marca onde não tem certeza (Libras/Braille-ready)

---

## 5) UI a11y checks (se der tempo)
- rodar `axe`/`pa11y` no front do demo,
- guardar relatório como artifact do CI,
- opcional: exibir “A11y check passed” no demo.

---

## 6) Debug rápido (o que mostrar no demo)
- card do Quality Gate com score + checklist
- 1–2 tool calls (curriculum_lookup + export_variant)
- tab “Exports” com visual schedule + screen reader
