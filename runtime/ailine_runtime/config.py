from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AiLineConfig:
    # NOTE: Runtime local. Em produção use secret manager.
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")

    # Runtime models
    planner_model: str = os.getenv("AILINE_PLANNER_MODEL", "claude-opus-4-6")
    executor_model: str = os.getenv("AILINE_EXECUTOR_MODEL", "claude-opus-4-6")

    # Effort costuma ser controlado via Claude Code settings/env; mantemos uma cópia para o Planner (DeepAgents).
    planner_effort: str = os.getenv("AILINE_PLANNER_EFFORT", "high")  # low|medium|high|max

    # Refinement loop
    max_refinement_iters: int = int(os.getenv("AILINE_MAX_REFINEMENT_ITERS", "2"))

    # Local store dir (materiais + planos persistidos no MVP)
    local_store_dir: str = os.getenv("AILINE_LOCAL_STORE", ".local_store")

    # DeepAgents skills (runtime)
    # Formato: caminhos separados por vírgula. Ex.: "../.claude/skills,../skills"
    # Se vazio → usa defaults (.claude/skills e skills/ no repo root).
    skill_sources_env: str | None = os.getenv("AILINE_SKILL_SOURCES")
    planner_use_skills: bool = os.getenv("AILINE_PLANNER_USE_SKILLS", "1") == "1"
    persona_use_skills: bool = os.getenv("AILINE_PERSONA_USE_SKILLS", "1") == "1"

    # Exports
    enable_exports: bool = os.getenv("AILINE_ENABLE_EXPORTS", "1") == "1"
    default_variants: str = os.getenv(
        "AILINE_DEFAULT_VARIANTS",
        # lista boa para demo (cobre TEA/TDAH, visual, auditiva, cognitiva)
        "standard_html,low_distraction_html,large_print_html,high_contrast_html,"
        "dyslexia_friendly_html,screen_reader_html,visual_schedule_html,student_plain_text,audio_script",
    )

    def skill_source_paths(self) -> list[str]:
        """Paths de skills para DeepAgents.

        DeepAgents aceita `skills=[...paths...]` e carrega skills sob demanda (progressive disclosure),
        reduzindo tokens na inicialização.
        """
        from .skills.paths import parse_skill_source_paths

        return parse_skill_source_paths(self.skill_sources_env)


def get_config() -> AiLineConfig:
    return AiLineConfig()
