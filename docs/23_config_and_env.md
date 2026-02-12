# 23 — Configuração e Variáveis de Ambiente (AiLine)

> Veja também `.env.example`.

---

## 1) Variáveis mínimas (runtime)
### Anthropic
- `ANTHROPIC_API_KEY` = sua chave

### Models
- `AILINE_PLANNER_MODEL` = `claude-opus-4-6` (padrão)
- `AILINE_EXECUTOR_MODEL` = `claude-opus-4-6` (padrão)

### Refinement loop
- `AILINE_MAX_REFINEMENT_ITERS` = `2` (padrão)

### Store local (MVP)
- `AILINE_LOCAL_STORE` = `.local_store`
  - guarda:
    - materiais do professor (`materials/`)
    - tutores (`tutors/`)
    - sessões (`sessions/`)
    - planos persistidos (`<plan_id>.json`)

---

## 2) Skills (dev + runtime)
### Dev (Claude Code)
- Skills são carregadas de `.claude/skills/`.

### Runtime (DeepAgents)
- `AILINE_SKILL_SOURCES` (opcional)
  - vazio → defaults: `<repo>/.claude/skills` e `<repo>/skills` (se existirem)
  - exemplo rodando a partir de `runtime/`:
    - `AILINE_SKILL_SOURCES="../.claude/skills,../skills"`
- `AILINE_PLANNER_USE_SKILLS` = `1` (default) / `0`
- `AILINE_PERSONA_USE_SKILLS` = `1` (default) / `0`

> Observação: no runtime, a **restrição real** de ferramentas vem de `allowed_tools` (SDK) e da tool layer do LangChain/DeepAgents.
> Não confie em “self-policing” do modelo.

---

## 3) Exports acessíveis (opcional, mas recomendado)
- `AILINE_ENABLE_EXPORTS` = `1`
- `AILINE_DEFAULT_VARIANTS` (lista CSV)
  - default do pack já é boa para demo:
    - `standard_html,low_distraction_html,large_print_html,high_contrast_html,dyslexia_friendly_html,screen_reader_html,visual_schedule_html,student_plain_text,audio_script`

---

## 4) Claude Code settings (para dev)
O Agent SDK usa o Claude Code CLI (bundled ou system install).
Para dev com Claude Code:
- `.claude/settings.json` (preferências e hooks)
- `.claude/skills/*` (skills de trabalho)

---

## 5) Dicas para CI (hackathon)
- Rode `pytest` no `runtime/`
- Não commite `.local_store/`
