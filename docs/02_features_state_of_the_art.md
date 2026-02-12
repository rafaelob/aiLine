# 02 — Features (state of the art) e como viram “pontos” no hackathon
Este doc lista features que **parecem produto**, mas que na prática são demonstrações de capacidade do runtime (e pontuam em **Impact** + **Opus 4.6 Use** + **Demo**).

---

## 1) Acessibilidade “first-class” (neurodiversidade + sensorial + acesso)
### O que é
Para cada plano, o AiLine gera um **Accessibility Pack** e uma **versão aluno** (Student Plan):

- **Teacher Plan** (planejamento completo)
- **Student Plan**: linguagem simples + passos curtos + glossário + opções de resposta
- **Relatório determinístico** (score + checklist + warnings + recomendações)
- **Human review flags** quando necessário (ex.: Libras / Braille-ready / material tátil)

### Por que pontua
- Impacto imediato (inclusão real para TEA/TDAH/dificuldades/deficiências).
- Profundidade: adapta estrutura, tempo, transições, mídia, avaliação e formato — não só “simplifica texto”.

---

## 2) Multi-exports que provam “uso de capacidade”
O demo fica muito mais “impressionável” quando o output não é só um JSON:

Exports default (tudo gerado via tool `export_variant`):
- `low_distraction_html` (reduz ruído e animações)
- `large_print_html` (baixa visão)
- `screen_reader_html` (skip link + landmarks)
- `high_contrast_html` (alto contraste)
- `dyslexia_friendly_html` (espaçamento/legibilidade)
- `visual_schedule_html` (agenda em cards — ótimo p/ TEA e crianças)
- `student_plain_text` (WhatsApp/print/TTS)
- `audio_script` (texto para TTS)

Por que isso ajuda no julgamento:
- 30% é demo: juiz *vê* a diferença imediatamente.
- Mostra “produto”: variantes parecem features de uma plataforma real.

---

## 3) Planning + Decomposition (Planner)
**Implementação:** DeepAgents com Opus 4.6.

**No demo aparece como:**
- TODO list: objetivos → sequência → avaliação → acessibilidade → evidências → exports.
- “Rascunho estruturado” que já inclui:
  - student_plan,
  - accessibility_pack_draft,
  - pedidos de evidência (RAG/currículo).

---

## 4) Quality Gate com score e refinamento automático
**Implementação:** validador determinístico (`accessibility_checklist`) + loop no LangGraph.

Checagens que vendem:
- instruções curtas e numeradas,
- chunking por tempo (janela de foco para TDAH/aprendizagem),
- checkpoints de “feito”,
- agenda/transições/pausas (TEA),
- requisitos de mídia (legenda/transcrição/alt text),
- estimativa de carga cognitiva + score.

**No demo:** você mostra um “fail” (ou score baixo) e o sistema refinando até subir.

---

## 5) Acessibilidade da própria UI (WCAG/eMAG/COGA)
Mesmo com front simples, faça o mínimo bem:
- navegação por teclado + foco visível,
- sem depender de cor para significado,
- toggles: reduzir movimento / alta legibilidade / contraste,
- textos de erro e estados claros (previsibilidade).

**Extra (se der tempo):** rodar `axe/pa11y` no CI e exibir um “badge”/relatório no demo.

---

## 6) “Amplify Human Judgment” (tema do hackathon)
AiLine não toma decisão pedagógica sozinho; ele:
- sugere adaptações **com justificativa**,
- marca onde precisa de **revisão humana**,
- oferece variantes e checagens para o professor escolher.

Isso encaixa diretamente no Problem Statement 3 (Amplify Human Judgment).
