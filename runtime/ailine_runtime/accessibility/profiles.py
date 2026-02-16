from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from ..domain.entities.accessibility import SupportIntensity


class AccessibilityNeeds(BaseModel):
    """Checklist rápido de necessidades (sem diagnóstico).

    Notas:
    - No MVP, tratamos isto como *preferências e necessidades funcionais* (não diagnósticos).
    - Em produção, isso é dado sensível; evite PII e controle acesso.
    """

    # Focos pedidos no hackathon (core)
    autism: bool = Field(
        default=False,
        description="TEA / previsibilidade, comunicação clara e sensorial.",
    )
    adhd: bool = Field(
        default=False,
        description="TDAH / atenção, organização, tempo e autorregulação.",
    )
    learning: bool = Field(
        default=False,
        description="Dificuldades de aprendizagem (ex.: dislexia/defasagem).",
    )
    hearing: bool = Field(
        default=False,
        description="Deficiencia auditiva / precisa de legendas/transcricao, redundancia visual.",
    )
    visual: bool = Field(
        default=False,
        description="Deficiencia visual/baixa visao / estrutura semantica, alt text, large print, TTS.",
    )

    # Extras úteis para "englobar tudo" (opcionais no MVP)
    speech_language: bool = Field(
        default=False,
        description=(
            "Dificuldades de fala/linguagem (ou comunicacao alternativa). "
            "Pode exigir AAC/pictogramas e respostas alternativas."
        ),
    )
    motor: bool = Field(
        default=False,
        description="Dificuldades motoras (escrita/fine motor). Pode exigir alternativas de input/entrega.",
    )

    other: list[str] = Field(
        default_factory=list, description="Outras necessidades (curtas, sem PII)."
    )


class UiPreferences(BaseModel):
    """Preferências de UI/consumo (plataforma + exports)."""

    low_distraction: bool = Field(
        default=False,
        description="Reduz ruido visual/animacoes; layout simples (cognitive-friendly).",
    )
    large_print: bool = Field(default=False, description="Fonte maior + espaçamento.")
    high_contrast: bool = Field(default=False, description="Contraste reforçado.")
    dyslexia_friendly: bool = Field(
        default=False, description="Ajustes de tipografia/espacamento para leitura."
    )
    reduce_motion: bool = Field(
        default=True,
        description="Respeitar prefers-reduced-motion e evitar transições chamativas.",
    )


class AutismSupportSettings(BaseModel):
    intensity: SupportIntensity = Field(
        default="medium",
        description="Intensidade de suportes de previsibilidade e sensorial.",
    )
    sensory_sensitivity: SupportIntensity = Field(
        default="medium",
        description="Sensibilidade sensorial (luz/som/ruído).",
    )
    require_visual_schedule: bool = Field(
        default=True, description="Gerar agenda/rotina e cronograma visual da aula."
    )
    require_transition_scripts: bool = Field(
        default=True,
        description="Incluir scripts de transição (ex.: 'Agora vamos...').",
    )
    break_every_minutes: int | None = Field(
        default=10,
        ge=3,
        le=30,
        description="Sugerir pausa/regulacao a cada N minutos (se aplicavel).",
    )
    avoid_figurative_language: bool = Field(
        default=True,
        description="Evitar metáforas/ambiguidade em instruções críticas.",
    )


class ADHDSupportSettings(BaseModel):
    intensity: SupportIntensity = Field(
        default="medium", description="Intensidade de suportes de atenção/organização."
    )
    focus_window_minutes: int = Field(
        default=8, ge=3, le=20, description="Janela de foco típica para chunking (min)."
    )
    movement_break_every_minutes: int | None = Field(
        default=12,
        ge=5,
        le=30,
        description="Pausa de movimento a cada N minutos (se aplicavel).",
    )
    require_checkpoints: bool = Field(
        default=True,
        description="Incluir checkpoints do tipo 'feito' e checagem rápida.",
    )
    require_timer_prompts: bool = Field(
        default=True, description="Incluir prompts de timer/tempo restante por etapa."
    )


class LearningSupportSettings(BaseModel):
    intensity: SupportIntensity = Field(
        default="medium",
        description="Intensidade de scaffolding (linguagem clara, exemplos, etc.).",
    )
    target_reading_level: Literal["simple", "standard"] = Field(
        default="simple",
        description="Nível alvo da versão aluno.",
    )
    require_examples_first: bool = Field(
        default=True, description="Exemplo antes de abstração quando possível."
    )
    require_glossary: bool = Field(
        default=True, description="Gerar glossário de termos difíceis (curto)."
    )
    allow_alternative_outputs: bool = Field(
        default=True,
        description="Permitir respostas alternativas (oral/desenho/multipla escolha).",
    )


class HearingSupportSettings(BaseModel):
    intensity: SupportIntensity = Field(
        default="medium", description="Intensidade de suportes auditivos."
    )
    require_captions: bool = Field(
        default=True, description="Vídeo/áudio exige legendas."
    )
    require_transcript: bool = Field(
        default=True, description="Áudio exige transcrição."
    )
    sign_language: Literal["none", "libras", "asl", "other"] = Field(
        default="none",
        description="Preferencia por lingua de sinais.",
    )
    speaker_identification: bool = Field(
        default=True,
        description="Quando houver dialogo, identificar falante no texto/legenda.",
    )


class VisualSupportSettings(BaseModel):
    intensity: SupportIntensity = Field(
        default="medium", description="Intensidade de suportes visuais."
    )
    require_alt_text: bool = Field(
        default=True, description="Imagens/figuras exigem texto alternativo."
    )
    require_audio_description: bool = Field(
        default=False,
        description="Midia visual relevante exige descricao (quando possivel).",
    )
    require_screen_reader_structure: bool = Field(
        default=True,
        description="Exports com headings/landmarks compativeis com leitores de tela.",
    )
    require_large_print: bool = Field(
        default=True, description="Gerar variante large print."
    )
    braille_ready: bool = Field(
        default=False,
        description="Se true: requer revisão humana e pipeline para BRF/Braille-ready.",
    )


class SupportSettings(BaseModel):
    autism: AutismSupportSettings = Field(
        default_factory=lambda: AutismSupportSettings()
    )
    adhd: ADHDSupportSettings = Field(default_factory=lambda: ADHDSupportSettings())
    learning: LearningSupportSettings = Field(
        default_factory=lambda: LearningSupportSettings()
    )
    hearing: HearingSupportSettings = Field(
        default_factory=lambda: HearingSupportSettings()
    )
    visual: VisualSupportSettings = Field(
        default_factory=lambda: VisualSupportSettings()
    )


class ClassAccessibilityProfile(BaseModel):
    """Perfil de acessibilidade por turma.

    Dica MVP:
    - preferir checkboxes + poucas opções. O resto fica em defaults.
    """

    needs: AccessibilityNeeds = Field(default_factory=lambda: AccessibilityNeeds())
    ui_prefs: UiPreferences = Field(default_factory=lambda: UiPreferences())

    # Ajustes finos (opcionais no MVP; úteis para "englobar tudo")
    supports: SupportSettings = Field(default_factory=lambda: SupportSettings())

    notes: str | None = Field(
        default=None, description="Observações curtas (evitar PII)."
    )


class AnonymousLearnerProfile(BaseModel):
    """Perfil anônimo por estudante/grupo (evitar nome real no MVP)."""

    label: str = Field(..., description="Ex.: 'Aluno A — baixa visão'")
    needs_json: dict[str, Any] = Field(
        default_factory=dict,
        description="Preferencias/necessidades sem diagnostico formal.",
    )


def human_review_flags(
    class_profile: ClassAccessibilityProfile | None,
) -> tuple[bool, list[str]]:
    """Indica quando é necessário revisão humana (AEE/IEP/apoios especializados)."""
    if not class_profile:
        return False, []

    reasons: list[str] = []
    n = class_profile.needs
    s = class_profile.supports

    # Libras / língua de sinais: geralmente exige profissional e/ou material específico
    if n.hearing and s.hearing.sign_language in ("libras", "asl", "other"):
        reasons.append(
            "Preferencia por lingua de sinais indicada -- exige revisao humana (interprete/material bilingue)."
        )

    # Braille/tátil: exige pipeline especializado
    if n.visual and s.visual.braille_ready:
        reasons.append(
            "Braille-ready indicado — exige revisão humana e pipeline especializado (BRF/material tátil)."
        )

    # Outros gatilhos do MVP
    if n.other:
        reasons.append(
            "Necessidades adicionais listadas — revisão humana recomendada para adequação fina."
        )

    return bool(reasons), reasons


def profile_to_prompt(
    class_profile: ClassAccessibilityProfile | None,
    learners: list[AnonymousLearnerProfile] | None = None,
) -> str:
    """Converte o perfil em texto curto para injetar no prompt do Planner/Executor."""
    if not class_profile and not learners:
        return ""

    lines: list[str] = []
    lines.append("## PERFIL DE ACESSIBILIDADE (resumo, sem diagnóstico)")
    if class_profile:
        n = class_profile.needs
        prefs = class_profile.ui_prefs
        s = class_profile.supports

        lines.append(
            "- necessidades (checkbox): "
            f"TEA={n.autism}, TDAH={n.adhd}, aprendizagem={n.learning}, auditiva={n.hearing}, visual={n.visual}, "
            f"fala/linguagem={n.speech_language}, motora={n.motor}"
        )

        lines.append(
            "- prefs UI: "
            f"baixa_distracao={prefs.low_distraction}, "
            f"large_print={prefs.large_print}, "
            f"alto_contraste={prefs.high_contrast}, "
            f"dislexia_friendly={prefs.dyslexia_friendly}, "
            f"reduzir_movimento={prefs.reduce_motion}"
        )

        # Highlights úteis para o agente (sem virar um livro)
        if n.autism:
            lines.append(
                f"- TEA: sensorial={s.autism.sensory_sensitivity}, agenda_visual={s.autism.require_visual_schedule}, "
                f"transicoes={s.autism.require_transition_scripts}, pausa_cada={s.autism.break_every_minutes}min"
            )
        if n.adhd:
            lines.append(
                f"- TDAH: foco~{s.adhd.focus_window_minutes}min, checkpoints={s.adhd.require_checkpoints}, "
                f"pausa_movimento_cada={s.adhd.movement_break_every_minutes}min"
            )
        if n.learning:
            lines.append(
                f"- Aprendizagem: leitura={s.learning.target_reading_level}, glossario={s.learning.require_glossary}, "
                f"exemplos_antes={s.learning.require_examples_first}"
            )
        if n.hearing:
            lines.append(
                f"- Auditiva: captions={s.hearing.require_captions}, transcript={s.hearing.require_transcript}, "
                f"lingua_sinais={s.hearing.sign_language}"
            )
        if n.visual:
            lines.append(
                f"- Visual: alt_text={s.visual.require_alt_text}, "
                f"screen_reader={s.visual.require_screen_reader_structure}, "
                f"large_print={s.visual.require_large_print}, "
                f"braille_ready={s.visual.braille_ready}"
            )

        if class_profile.notes:
            lines.append(f"- notas: {class_profile.notes}")

        needs_human, reasons = human_review_flags(class_profile)
        if needs_human:
            lines.append("- atenção: exigir revisão humana:")
            for r in reasons:
                lines.append(f"  - {r}")

    if learners:
        lines.append("- perfis anônimos (max 8):")
        for lp in learners[:8]:
            snippet = str(lp.needs_json)[:240]
            lines.append(f"  - {lp.label}: {snippet}")

    lines.append(
        "Regras: não diagnosticar; sugerir adaptações pedagógicas e alternativas de formato; manter linguagem clara; "
        "instruções curtas (1 ação por item); quando houver áudio/vídeo/imagens, exigir requisitos de acessibilidade."
    )
    return "\n".join(lines)
