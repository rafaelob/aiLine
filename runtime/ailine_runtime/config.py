from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AiLineConfig:
    # NOTE: Runtime local. Em producao use secret manager.
    anthropic_api_key: str | None = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY")
    )

    # Runtime models
    planner_model: str = field(
        default_factory=lambda: os.getenv(
            "AILINE_PLANNER_MODEL", "anthropic:claude-opus-4-6"
        )
    )
    executor_model: str = field(
        default_factory=lambda: os.getenv(
            "AILINE_EXECUTOR_MODEL", "google-gla:gemini-3-flash-preview"
        ),
    )
    qg_model: str = field(
        default_factory=lambda: os.getenv(
            "AILINE_QG_MODEL", "anthropic:claude-sonnet-4-5"
        )
    )
    tutor_model: str = field(
        default_factory=lambda: os.getenv(
            "AILINE_TUTOR_MODEL", "anthropic:claude-sonnet-4-5"
        )
    )

    # Effort costuma ser controlado via Claude Code settings/env; mantemos uma copia para o Planner (DeepAgents).
    # low|medium|high|max
    planner_effort: str = field(
        default_factory=lambda: os.getenv("AILINE_PLANNER_EFFORT", "high")
    )

    # Refinement loop
    max_refinement_iters: int = field(
        default_factory=lambda: int(os.getenv("AILINE_MAX_REFINEMENT_ITERS", "2"))
    )

    # Local store dir (materiais + planos persistidos no MVP)
    local_store_dir: str = field(
        default_factory=lambda: os.getenv("AILINE_LOCAL_STORE", ".local_store")
    )

    # DeepAgents skills (runtime)
    # Formato: caminhos separados por virgula. Ex.: "../.claude/skills,../skills"
    # Se vazio -> usa defaults (.claude/skills e skills/ no repo root).
    skill_sources_env: str | None = field(
        default_factory=lambda: os.getenv("AILINE_SKILL_SOURCES")
    )
    planner_use_skills: bool = field(
        default_factory=lambda: os.getenv("AILINE_PLANNER_USE_SKILLS", "1") == "1"
    )
    persona_use_skills: bool = field(
        default_factory=lambda: os.getenv("AILINE_PERSONA_USE_SKILLS", "1") == "1"
    )

    # Exports
    enable_exports: bool = field(
        default_factory=lambda: os.getenv("AILINE_ENABLE_EXPORTS", "1") == "1"
    )
    default_variants: str = field(
        default_factory=lambda: os.getenv(
            "AILINE_DEFAULT_VARIANTS",
            # lista boa para demo (cobre TEA/TDAH, visual, auditiva, cognitiva)
            "standard_html,low_distraction_html,large_print_html,high_contrast_html,"
            "dyslexia_friendly_html,screen_reader_html,visual_schedule_html,student_plain_text,audio_script",
        )
    )

    def skill_source_paths(self) -> list[str]:
        """Paths de skills para DeepAgents.

        DeepAgents aceita `skills=[...paths...]` e carrega skills sob demanda (progressive disclosure),
        reduzindo tokens na inicializacao.
        """
        from .skills.paths import parse_skill_source_paths

        return parse_skill_source_paths(self.skill_sources_env)


def get_config() -> AiLineConfig:
    return AiLineConfig()
