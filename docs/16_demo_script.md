# 16 — Demo Script (3 minutos) — versão “inclusão + agência + exports”

> Objetivo: mostrar **agência** e **capacidade** do Opus 4.6 sem parecer “teatro”.
> A narrativa é: **planejar a aula + tornar acessível de verdade** (TEA/TDAH/auditiva/visual).

---

## Setup do demo (antes de gravar)
- Materiais prontos:
  - 3–5 curtos + 1 longo (para justificar Opus 4.6)
- Caso realista:
  - aula de 50 min
  - turma com:
    - 1 aluno TEA sensorial (agenda, transições, pausas)
    - 1 aluno com TDAH (chunking + checkpoints)
    - 1 aluno com baixa visão (large print + alto contraste)
    - 1 aluno com deficiência auditiva (legendas/transcrição)
  - currículo: BNCC
- Front com:
  - Wizard de input
  - Run Viewer (stepper + logs)
  - Plan Viewer com tabs (Plano / Student Plan / Relatório / Exports)

---

## Roteiro (3 min)

### 0:00 — 0:25 | Contexto e input (impacto)
“Vou gerar um plano a partir de materiais reais e já adaptar para uma turma com necessidades diferentes.”

- mostrar upload + tema + duração
- marcar checkboxes (TEA, TDAH, auditiva, visual)
- marcar toggles: baixa distração + large print

### 0:25 — 1:10 | Planner (DeepAgents + Opus 4.6)
- mostrar que ele cria o rascunho estruturado (StudyPlanDraft)
- destacar que o rascunho já inclui:
  - **student_plan** (versão aluno)
  - accessibility_pack_draft (adaptações + mídia)
  - pedidos de evidência (se houver)

### 1:10 — 1:50 | Quality Gate (score + refinamento)
- mostrar o card do Quality Gate:
  - score inicial (ex.: 72)
  - warnings (ex.: “faltou transição/pausa/legenda/alt text”)
- mostrar “refinement” automático
- mostrar score subindo (ex.: 86) e checklist ficando verde

> Isso prova agência real: o modelo responde a um gate determinístico.

### 1:50 — 2:25 | Executor (Claude Agent SDK + MCP tools)
- mostrar 1–2 tool calls:
  - `accessibility_checklist` (relatório)
  - `export_variant` (gerando visual schedule / screen reader)
- mostrar `save_plan` (persistência)

### 2:25 — 3:00 | Output “wow” (30% do score é demo)
Tabs (mostrar rápido, lado a lado):
1) **Student Plan**: passos curtos + glossário + opções de resposta
2) **Relatório**: score + checklist + recomendações + “human review required” (se aplicável)
3) **Exports**:
   - `visual_schedule_html` (cards com tempo — ótimo p/ TEA)
   - `screen_reader_html` (skip link + headings)
   - `large_print_html` / `high_contrast_html`
   - `audio_script` (TTS)

Fechamento:
“Não é um chat. É um pipeline que planeja, valida, refina e entrega variantes acessíveis com rastreabilidade — mantendo o professor no controle.”


---

## Extra (30–45s): Tutor Agent por aluno (impacto + Opus 4.6 Use)
Se sobrar tempo no vídeo, inclua um trecho curto:

1) Professor cria um Tutor Agent para “Aluno A — TEA + TDAH”, Matemática 5º ano, com tags “frações”.
2) Adiciona 1 material rápido (texto) com “frações equivalentes”.
3) Aluno pergunta: “Como somo 1/4 + 2/4?”
4) Mostrar:
   - o tutor chamando `rag_search` (e citando `Apostila#chunk`),
   - resposta com **passo-a-passo + checagem + pausa**,
   - e um “modo baixa distração” no front.

Mensagem-chave: “O mesmo motor que planeja aulas cria tutores acessíveis — por aluno e por conteúdo do professor.”
