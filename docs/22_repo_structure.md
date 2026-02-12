# 22 — Estrutura de Repositório (proposta)

> Este pack é docs-first. A estrutura abaixo é a recomendação para implementar o runtime.

```
ailine/
  README.md
  LICENSE
  .claude/
    settings.json
    skills/
      lesson-planner/SKILL.md
      rubric-writer/SKILL.md
      accessibility-coach/SKILL.md
      curriculum-mapper/SKILL.md

  docs/
    00_hackathon_answer.md
    01_vision_and_scope.md
    02_features_state_of_the_art.md
    03_user_journeys_and_flows.md
    04_agents_and_langgraph_architecture.md
    ...
    08_accessibility_inclusive_design.md
    10_api_and_frontend.md
    11_security_privacy_compliance.md
    12_mvp_plan_d1_d3.md
    14_observability_evals_and_guardrails.md
    16_demo_script.md
    17_backlog_and_roadmap.md
    18_appendix_sources.md
    21_prompt_packs_and_templates.md
    22_repo_structure.md

  runtime/
    pyproject.toml
    ailine_runtime/
      config.py
      workflow_langgraph.py
      planner_deepagents.py
      executor_agent_sdk.py
      tools/
        registry.py
        adapters_langchain.py
        adapters_agent_sdk.py
      accessibility/
        profiles.py     # perfil (needs/ui_prefs/supports) + prompt builder + flags de revisão humana
        validator.py    # Quality Gate determinístico: score, checklist, recomendações
        exports.py      # exports: low_distraction, screen_reader, visual_schedule, etc
```

Notas:
- `accessibility/` guarda regras determinísticas (Quality Gate) e geração de variantes (exports).
- A pasta `.claude/skills` é opcional no MVP, mas é ótima para padronizar comportamento e acelerar o dev com Claude Code.


### Novos módulos (runtime)
- `runtime/ailine_runtime/materials/` — store local + busca simples (MVP RAG)
- `runtime/ailine_runtime/tutoring/` — criação de Tutor Agents + sessões de chat (Claude Agent SDK)
- `runtime/ailine_runtime/api_app.py` — API FastAPI (MVP para demo)
