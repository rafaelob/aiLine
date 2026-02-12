# 21 — Prompt Packs e Templates (Planner + Executor) — com acessibilidade forte

> Meta: padronizar outputs e reduzir “surpresas”.
> Aqui você coloca textos que o Claude Code vai reaproveitar (consistência = demo melhor).

---

## 1) Template do Planner (DeepAgents)

### Instrução base (Planner)
- Você é especialista em didática, planejamento e inclusão.
- Gere um `StudyPlanDraft` **estruturado** e completo.
- Antes de escrever: faça um TODO list mental (objetivos → sequência → avaliação → acessibilidade → evidências → exports).
- Aplique UDL e COGA como baseline.
- Se houver `class_accessibility_profile`, gere **adaptações explícitas** por necessidade.
- Sempre gere **student_plan** (versão aluno) com:
  - linguagem simples,
  - passos curtos,
  - glossário curto,
  - opções de resposta.

### Checklist que o Planner deve cumprir
- Instruções numeradas e curtas (1 ação por item).
- Blocos de tempo pequenos (5–10 min), com checkpoints.
- Transições explícitas entre atividades.
- Pausas/intervalos planejados quando TEA/TDAH presentes.
- Requisitos de mídia:
  - vídeo/áudio → legenda/transcrição
  - imagens/figuras → alt text
- Marcar onde precisa de **revisão humana** (Libras/Braille-ready/material tátil).

---

## 2) Template do Executor (Claude Agent SDK)

### Instrução base (Executor)
- Recebe o draft em JSON.
- Se faltar evidência: use `rag_search` e `curriculum_lookup`.
- Rode `accessibility_checklist` (determinístico) e inclua no output.
- Gere exports via `export_variant`:
  - `low_distraction_html`
  - `large_print_html`
  - `screen_reader_html`
  - `visual_schedule_html`
  - `student_plain_text`
  - `audio_script`
  - (opcional) `high_contrast_html`, `dyslexia_friendly_html`
- Chame `save_plan` com `plan_json` que inclui:
  - plan (draft/final)
  - accessibility_report (score, checklist, warnings, recomendações, human review)
  - exports (variant->content)
- Retorne `plan_id` + score + 3 bullets:
  - impacto / inclusão,
  - acessibilidade entregue,
  - alinhamento curricular.

---

## 3) “Playbook” de acessibilidade (compacto)
Use no prompt (ou como doc embed) para consistência:

- TEA: agenda + transições + pausas + literalidade + previsibilidade.
- TDAH: chunking + timer + checkpoints + pausas de movimento.
- Aprendizagem: exemplo antes + glossário + frases curtas + alternativas.
- Auditiva: captions/transcript + instrução crítica em texto.
- Visual: headings/landmarks + alt text + large print + alto contraste.
- Human review: Libras e Braille-ready/material tátil.

---

## 4) Como usar isso no Claude Code
- Crie comandos / snippets ou use Skills (`.claude/skills`) para padronizar.
- Ex.: skill `accessibility-coach` revisa e gera variantes com checklist.
