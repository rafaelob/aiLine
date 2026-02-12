# 12 — Plano de MVP (D1 → D3) focado no hackathon (com acessibilidade forte)

> Objetivo: sair com um demo de 3 min que aguenta julgamento assíncrono.
> Acessibilidade aqui é “feature core”, então entra no vertical slice desde o Dia 1.

---

## Dia 1 (D1) — Vertical slice com Student Plan + Accessibility Profile
**Meta:** pipeline completo rodando (mesmo com mocks), já aceitando perfil de acessibilidade e gerando student_plan.

Checklist:
- [ ] `Run` + persistência mínima (arquivo/DB) + logs de eventos
- [ ] Endpoint `POST /plans/generate` recebe `class_accessibility_profile`
- [ ] Orchestrator LangGraph: Planner → Gate/Score → (Refine) → Executor → Save
- [ ] Schema do `StudyPlanDraft` inclui:
  - `student_plan` (resumo + steps simples)
  - `accessibility_pack_draft` (adaptações + requisitos de mídia + human review flags)
- [ ] Quality Gate mínimo:
  - steps + instructions (hard fail)
  - chunking (TDAH/aprendizagem)
  - transições/agenda/pausas (TEA)
  - requisitos de mídia (auditiva/visual)
  - score + checklist + recomendações
- [ ] UI: wizard simples + run viewer

---

## Dia 2 (D2) — Exports “wow” + relatório vendável
**Meta:** produzir artefatos acessíveis e mostrar lado a lado no front.

Checklist:
- [ ] Executor gera relatório `accessibility_checklist` (score, warnings, recomendações)
- [ ] Exports (via `export_variant`):
  - `low_distraction_html`
  - `large_print_html`
  - `screen_reader_html`
  - `visual_schedule_html`
  - `student_plain_text`
  - `audio_script`
- [ ] Front:
  - tabs “Plano / Student Plan / Relatório / Exports”
  - badge de “human review required” quando aplicável
- [ ] Observabilidade:
  - tool calls exibidos no run viewer
  - mostrar score subindo após refinamento

---

## Dia 3 (D3) — Polimento de demo + caso forte (inclusão real)
**Meta:** demo filmável em 3 minutos com caso realista de inclusão.

Checklist:
- [ ] Montar caso:
  - turma com TEA + TDAH + baixa visão + deficiência auditiva (legenda/transcrição)
- [ ] Preparar materiais:
  - 3–5 curtos + 1 longo (para justificar Opus 4.6)
- [ ] Garantir 1 iteração de refinamento:
  - score inicial < 80 → correção automática → score sobe
- [ ] Ajustar UI a11y mínima:
  - teclado, foco visível, contraste aceitável, sem dependência de cor
- [ ] Gravar demo + escrever submissão (100–200 palavras)

---

## Notas táticas (para pontuar)
- 30% é demo: **exports visuais** (visual schedule + screen reader) valem ouro.
- “Amplify human judgment”: destaque o relatório + human review flags.
- Mostre o pipeline como produto: stepper + logs + score.
