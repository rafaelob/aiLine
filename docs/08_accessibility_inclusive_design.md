# 08 — Acessibilidade e Design Instrucional Inclusivo (TEA, TDAH, dificuldades, auditiva e visual)

> Meta do AiLine: tornar **planejamento inclusivo** uma *propriedade do output* (plano + variantes + relatório),
> e não uma checkbox “no fim”.

Este doc descreve como a plataforma incorpora acessibilidade para:
- **Autismo (TEA)** (sensório + previsibilidade)
- **TDAH** (atenção + funções executivas)
- **Dificuldades de aprendizagem** (linguagem + scaffolding)
- **Deficiência auditiva** (redundância e acesso ao áudio)
- **Deficiência visual/baixa visão** (estrutura semântica + alt text + legibilidade)
- e também como “englobar tudo” com princípios universais (UDL/COGA/WCAG).

---

## 1) Princípios (o que guia o runtime)

### 1.1) UDL como baseline (todo mundo ganha)
- **Representação**: texto + visual + exemplos + demonstrações.
- **Ação/expressão**: opções de resposta (oral, desenho, MCQ, manipulação, etc.).
- **Engajamento**: escolhas controladas, metas curtas, feedback rápido, previsibilidade.

### 1.2) Acessibilidade cognitiva (COGA)
- reduzir carga cognitiva,
- previsibilidade (agenda + transições),
- linguagem simples,
- listas curtas,
- evitar “surpresas” e ambiguidade.

### 1.3) Acessibilidade digital (WCAG/eMAG)
Não basta o conteúdo ser inclusivo: o produto também.
- navegação por teclado,
- foco visível,
- contraste,
- sem depender de cor,
- headings/landmarks para leitor de tela,
- conteúdo multimídia com suporte (legendas/transcrições/descrições).

> Importante: o AiLine **não diagnostica** nem substitui AEE/IEP. Ele oferece suportes pedagógicos e formatos acessíveis.

---

## 2) Modelo de entrada (perfil de acessibilidade)
O MVP deve aceitar:
- `needs` (checkboxes): TEA, TDAH, aprendizagem, auditiva, visual (+ extras opcionais)
- `ui_prefs`: baixa distração, large print, alto contraste, dislexia-friendly, reduzir movimento
- `supports` (opcional): ajustes finos com defaults (janela de foco, necessidade de agenda visual, etc.)
- `notes` (curto e sem PII)

**Por quê esse design funciona no hackathon**
- é simples para UI (checkbox),
- é suficiente para o runtime gerar variantes “visíveis” no demo,
- abre espaço para evolução pós-hackathon (perfis por estudante sem PII).

---

## 3) O que o runtime deve produzir (saídas obrigatórias)
Para **pontuar alto**, o AiLine precisa entregar, por run:

### 3.1) Teacher Plan (plano completo)
- objetivos,
- sequência com tempo por etapa,
- instruções numeradas,
- atividades e avaliação.

### 3.2) Student Plan (versão aluno)
- resumo em linguagem simples,
- passos curtos,
- check-for-understanding (1–3 itens),
- opções de resposta,
- glossário curto (quando necessário).

### 3.3) Accessibility Pack + relatório determinístico
- adaptações aplicadas (por necessidade),
- requisitos de mídia (captions/transcript/alt text/audiodescrição),
- recomendações de UI/consumo,
- **score + checklist + recomendações** (Quality Gate),
- flags de **human review required** (quando necessário: Libras, Braille-ready, material tátil).

### 3.4) Exports acessíveis (para demo e produto)
Mínimo recomendado:
- `low_distraction_html`
- `large_print_html`
- `screen_reader_html`
- `visual_schedule_html`
- `student_plain_text`
- `audio_script`

---

## 4) Playbooks por necessidade (o que realmente muda no conteúdo)

### 4.1) Autismo (TEA) — previsibilidade e sensorial
**Objetivo**: reduzir ansiedade por incerteza; aumentar clareza; evitar sobrecarga.

**O AiLine deve adicionar:**
- **Agenda/roteiro** no início (“Hoje vamos: 1) … 2) … 3) …”).
- **Transições explícitas** entre atividades (scripts curtos: “Agora vamos guardar…, depois…”).
- **Pausas de regulação** (respiração, água, alongamento, canto calmo).
- **Escolhas controladas** (A/B) para dar autonomia sem caos.
- **Instruções literais** (evitar metáforas em passos críticos).
- **Sinais visuais de progresso** (cronograma visual; checkboxes de “feito”).

**Evitar (do_not):**
- mudanças de regra no meio sem aviso,
- instruções ambíguas (“faça de um jeito legal”),
- longos períodos sem feedback.

**Na plataforma (UI):**
- modo **baixa distração** por padrão,
- cronograma em cards (visual schedule),
- mensagens consistentes e previsíveis.

---

### 4.2) TDAH — funções executivas (atenção, planejamento, memória de trabalho)
**Objetivo**: reduzir carga de organização; aumentar foco e feedback.

**O AiLine deve adicionar:**
- **Chunking**: etapas de 5–10 min (ou janela configurável).
- **Timer prompts**: “faltam 2 min para terminar”.
- **Checkpoints**: “marque ✓ quando…”.
- **Pausas de movimento** a cada ~10–15 min.
- **Checklist de materiais** (para não travar).
- **Instruções com 1 ação por item** e ordem clara.

**Opções de resposta:**
- verbal/oral,
- seleção (MCQ),
- desenho/organização visual.

**Na plataforma:**
- foco visível e sem animações,
- modo baixa distração,
- progresso por cards.

---

### 4.3) Dificuldades de aprendizagem (ex.: dislexia, defasagem)
**Objetivo**: melhorar compreensão e reduzir barreira linguística/abstração.

**O AiLine deve adicionar:**
- **Exemplo antes de execução** (modelo curto).
- **Glossário** de termos difíceis (3–10 termos).
- **Frases curtas** e vocabulário simples no Student Plan.
- **Suporte visual** (quando não conflitar com baixa distração).
- **Prática guiada** antes da prática independente.
- **Alternativas de avaliação** (oral, desenho, manipulação, MCQ).

**Na plataforma:**
- opção dislexia-friendly (espaçamento, line-height),
- controlar “texto por tela” (progressive disclosure).

---

### 4.4) Deficiência auditiva — acesso ao áudio
**Objetivo**: não depender do canal auditivo.

**O AiLine deve exigir:**
- vídeo/áudio → **legendas** e/ou **transcrição**
- instruções críticas sempre em **texto**
- quando houver diálogo: **identificação de falante**

**Se houver preferência por Libras**
- marcar **human review required**:
  - material bilíngue / intérprete / revisão humana.

**Na plataforma:**
- player com captions,
- exibir transcrição sincronizada (pós-hackathon),
- redundância visual para avisos (não só som).

---

### 4.5) Deficiência visual / baixa visão — estrutura e legibilidade
**Objetivo**: permitir acesso com leitor de tela, baixa visão e/ou TTS.

**O AiLine deve exigir:**
- **estrutura semântica** (headings/listas/landmarks)
- imagens/figuras → **alt text**
- `large_print` e, quando relevante, `high_contrast`
- evitar depender de cor (“clique no botão verde”)

**Se houver Braille-ready / material tátil**
- marcar **human review required**:
  - pipeline especializado (BRF/material tátil) não é automático no MVP.

**Na plataforma:**
- foco visível,
- atalhos (skip link),
- labels e aria quando necessário.

---

## 5) Conflitos e combinações (como englobar tudo sem piorar)
Na vida real, necessidades podem conflitar.

Regras práticas (runtime):
1) **Acesso ao conteúdo** (auditiva/visual) vem primeiro.
2) Depois **carga cognitiva** (passos curtos, chunking).
3) Depois **sensorial** (baixa distração).
4) Quando houver conflito, gere **duas variantes** e deixe o professor escolher.

Exemplo de conflito:
- “Precisa de mais apoio visual” vs “baixa distração”.
Solução:
- `visual_schedule_html` (cards simples) + `low_distraction_html` (sem extras).

---

## 6) Quality Gate determinístico (o que checar)
O validador deve produzir:
- `status` (pass/fail)
- `score` (0–100)
- checklist + warnings + recomendações
- human_review_required + razões

Checklist mínimo recomendado:
- `has_steps`
- `has_instructions`
- `instructions_short`
- `chunked_for_attention`
- `has_checkpoints`
- `has_breaks`
- `has_transitions`
- `has_media_requirements`
- `captions_or_transcript` (quando auditiva)
- `alt_text` (quando visual)

---

## 7) Métricas e Evals (para mostrar seriedade)
- score por run,
- bucket de carga cognitiva (low/medium/high),
- taxa de “refinement needed”,
- cobertura de exports por perfil.

Evals simples:
- prompts “golden” para TEA, TDAH, baixa visão, auditiva e combinado,
- validação de schema + checklist.

UI checks (se der tempo):
- `axe/pa11y` no CI.

---

## 8) Limites e responsabilidade (importante para segurança)
- Não diagnosticar.
- Não afirmar recomendações clínicas.
- Sinalizar quando é necessário AEE/IEP/revisão humana.
- Evitar armazenar PII; perfis são dados sensíveis.

---

## 9) Referências (índice)
Ver `docs/18_appendix_sources.md` para fontes de:
- WCAG/COGA,
- UDL (CAST),
- guias de design inclusivo,
- bases para export e UI a11y.
