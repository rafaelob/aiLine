"""Tests for ailine_runtime.accessibility.exports — targeting >=98% coverage."""

from __future__ import annotations

import json

from ailine_runtime.accessibility.exports import (
    _css_for_variant,
    _plan_steps,
    _safe,
    render_audio_script,
    render_export,
    render_plan_html,
    render_student_plain_text,
    render_visual_schedule_json,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _sample_plan() -> dict:
    """Full plan with all optional sections populated."""
    return {
        "title": "Plano Exemplo",
        "grade": "5 ano",
        "objectives": [{"text": "Objetivo 1"}, "Objetivo direto (str)"],
        "steps": [
            {
                "minutes": 5,
                "title": "Etapa 1",
                "instructions": ["Faca X.", "Faca Y."],
                "activities": ["Atividade A", "Atividade B"],
                "assessment": ["Ok 1", "Ok 2"],
            },
            {
                "minutes": 10,
                "title": "Etapa 2",
                "instructions": ["Faca Z."],
                "activities": [],
                "assessment": [],
            },
        ],
        "student_plan": {
            "summary": ["Resumo 1.", "Resumo 2."],
            "steps": [
                {"title": "Etapa aluno 1", "instructions": ["Instrucao aluno 1"]},
                {"title": "Etapa aluno 2", "instructions": ["Instrucao aluno 2"]},
            ],
            "glossary": ["termo1: definicao1", "termo2: definicao2"],
        },
        "accessibility_pack_draft": {
            "media_requirements": ["Imagens com alt text"],
            "ui_recommendations": ["Baixa distracao"],
        },
    }


def _minimal_plan() -> dict:
    """Minimal plan: just title and steps, no extras."""
    return {
        "title": "Minimo",
        "steps": [
            {"minutes": 3, "title": "Passo 1", "instructions": ["Faca algo."]},
        ],
    }


# ---------------------------------------------------------------------------
# _css_for_variant
# ---------------------------------------------------------------------------

class TestCssForVariant:

    def test_standard_html_returns_base_only(self):
        css = _css_for_variant("standard_html")
        assert "color-scheme" in css
        # Should NOT contain any variant-specific rules
        assert "max-width: 760px" not in css
        assert "font-size: 20px" not in css
        assert "background: #000" not in css

    def test_low_distraction_html(self):
        css = _css_for_variant("low_distraction_html")
        assert "max-width: 760px" in css
        assert "border-style: dashed" in css

    def test_large_print_html(self):
        css = _css_for_variant("large_print_html")
        assert "font-size: 20px" in css
        assert "line-height: 1.85" in css

    def test_high_contrast_html(self):
        css = _css_for_variant("high_contrast_html")
        assert "background: #000" in css
        assert "color: #fff" in css
        assert "color: #0ff" in css

    def test_dyslexia_friendly_html(self):
        css = _css_for_variant("dyslexia_friendly_html")
        assert "letter-spacing: 0.02em" in css
        assert "word-spacing: 0.06em" in css
        assert "max-width: 72ch" in css

    def test_screen_reader_html(self):
        css = _css_for_variant("screen_reader_html")
        assert ".skip-link" in css

    def test_visual_schedule_html(self):
        css = _css_for_variant("visual_schedule_html")
        assert ".schedule-grid" in css
        assert "grid-template-columns" in css
        assert ".schedule-card" in css
        assert ".schedule-title" in css
        assert ".schedule-meta" in css

    def test_unknown_variant_returns_base(self):
        css = _css_for_variant("something_unknown")
        assert "color-scheme" in css
        # Same as base, no extras
        assert ".schedule-grid" not in css


# ---------------------------------------------------------------------------
# _safe
# ---------------------------------------------------------------------------

class TestSafe:

    def test_escapes_html(self):
        assert _safe("<script>") == "&lt;script&gt;"

    def test_none_returns_empty(self):
        assert _safe(None) == ""

    def test_non_string_converted(self):
        assert _safe(42) == "42"


# ---------------------------------------------------------------------------
# _plan_steps
# ---------------------------------------------------------------------------

class TestPlanSteps:

    def test_returns_dicts_only(self):
        plan = {"steps": [{"title": "A"}, "not a dict", 42, {"title": "B"}]}
        result = _plan_steps(plan)
        assert len(result) == 2
        assert result[0]["title"] == "A"
        assert result[1]["title"] == "B"

    def test_missing_steps_key(self):
        assert _plan_steps({}) == []

    def test_none_steps(self):
        assert _plan_steps({"steps": None}) == []


# ---------------------------------------------------------------------------
# render_visual_schedule_json
# ---------------------------------------------------------------------------

class TestRenderVisualScheduleJson:

    def test_basic_structure(self):
        plan = _sample_plan()
        raw = render_visual_schedule_json(plan)
        data = json.loads(raw)
        assert "visual_schedule" in data
        cards = data["visual_schedule"]
        assert len(cards) == 2
        assert cards[0]["order"] == 1
        assert cards[0]["title"] == "Etapa 1"
        assert cards[0]["minutes"] == 5
        assert isinstance(cards[0]["instructions_preview"], list)

    def test_goal_from_assessment(self):
        plan = {
            "steps": [
                {
                    "title": "S1",
                    "minutes": 5,
                    "instructions": [],
                    "assessment": ["Checagem 1", "Checagem 2"],
                }
            ]
        }
        raw = render_visual_schedule_json(plan)
        data = json.loads(raw)
        assert data["visual_schedule"][0]["goal"] == "Checagem 1"

    def test_goal_empty_when_no_assessment(self):
        plan = {"steps": [{"title": "S1", "minutes": 5, "instructions": []}]}
        raw = render_visual_schedule_json(plan)
        data = json.loads(raw)
        assert data["visual_schedule"][0]["goal"] == ""

    def test_default_title_when_missing(self):
        plan = {"steps": [{"minutes": 5, "instructions": []}]}
        raw = render_visual_schedule_json(plan)
        data = json.loads(raw)
        assert "Etapa 1" in data["visual_schedule"][0]["title"]


# ---------------------------------------------------------------------------
# render_plan_html
# ---------------------------------------------------------------------------

class TestRenderPlanHtml:

    def test_standard_html_has_basic_structure(self):
        html = render_plan_html(_sample_plan())
        assert "<!doctype html>" in html
        assert "lang='pt-br'" in html
        assert "Plano Exemplo" in html
        assert "5 ano" in html

    def test_screen_reader_has_skip_link(self):
        html = render_plan_html(_sample_plan(), "screen_reader_html")
        assert "skip-link" in html
        assert "Pular para o conte" in html
        assert "role='main'" in html

    def test_visual_schedule_html_renders_schedule_grid(self):
        html = render_plan_html(_sample_plan(), "visual_schedule_html")
        assert "schedule-grid" in html
        assert "schedule-card" in html
        assert "schedule-title" in html
        assert "schedule-meta" in html
        # Should have both steps as schedule cards
        assert "Etapa 1" in html
        assert "Etapa 2" in html

    def test_visual_schedule_html_with_instructions_preview(self):
        plan = _sample_plan()
        # Ensure steps have instructions for the preview ol
        html = render_plan_html(plan, "visual_schedule_html")
        assert "<ol>" in html

    def test_visual_schedule_html_step_without_instructions(self):
        plan = {
            "title": "Test",
            "steps": [{"title": "Passo", "minutes": 5}],
        }
        html = render_plan_html(plan, "visual_schedule_html")
        assert "schedule-card" in html
        # No <ol> inside the schedule card because no instructions preview
        # But the standard section below will still render

    def test_low_distraction_html(self):
        html = render_plan_html(_sample_plan(), "low_distraction_html")
        assert "max-width: 760px" in html

    def test_large_print_html(self):
        html = render_plan_html(_sample_plan(), "large_print_html")
        assert "font-size: 20px" in html

    def test_high_contrast_html(self):
        html = render_plan_html(_sample_plan(), "high_contrast_html")
        assert "background: #000" in html

    def test_dyslexia_friendly_html(self):
        html = render_plan_html(_sample_plan(), "dyslexia_friendly_html")
        assert "letter-spacing" in html

    def test_student_plan_summary_rendered(self):
        html = render_plan_html(_sample_plan())
        assert "Resumo 1." in html
        assert "Resumo 2." in html

    def test_student_plan_steps_only(self):
        plan = _sample_plan()
        plan["student_plan"] = {"steps": [{"title": "A"}]}
        html = render_plan_html(plan)
        assert "aluno (resumo)" in html.lower()

    def test_objectives_rendered(self):
        html = render_plan_html(_sample_plan())
        assert "Objetivo 1" in html
        assert "Objetivo direto (str)" in html

    def test_activities_rendered(self):
        html = render_plan_html(_sample_plan())
        assert "Atividade A" in html
        assert "Atividade B" in html
        assert "Atividades" in html

    def test_assessment_rendered(self):
        html = render_plan_html(_sample_plan())
        assert "Ok 1" in html
        assert "Ok 2" in html

    def test_accessibility_pack_rendered(self):
        html = render_plan_html(_sample_plan())
        assert "Acessibilidade" in html
        assert "Imagens com alt text" in html
        assert "Baixa distracao" in html

    def test_no_grade_no_grade_paragraph(self):
        plan = _minimal_plan()
        html = render_plan_html(plan)
        assert "rie/ano" not in html

    def test_no_objectives(self):
        plan = _minimal_plan()
        html = render_plan_html(plan)
        assert "Objetivos" not in html

    def test_no_accessibility_pack(self):
        plan = _minimal_plan()
        html = render_plan_html(plan)
        assert "Acessibilidade</h2>" not in html

    def test_no_student_plan(self):
        plan = _minimal_plan()
        html = render_plan_html(plan)
        assert "aluno (resumo)" not in html.lower()

    def test_step_without_instructions_still_renders(self):
        plan = {
            "title": "Test",
            "steps": [{"title": "S", "minutes": 3}],
        }
        html = render_plan_html(plan)
        assert "Passo a passo" not in html  # no instructions = no instructions section

    def test_step_without_activities(self):
        plan = {
            "title": "Test",
            "steps": [
                {"title": "S", "minutes": 3, "instructions": ["Do X."]}
            ],
        }
        html = render_plan_html(plan)
        assert "Atividades" not in html

    def test_step_without_assessment(self):
        plan = {
            "title": "Test",
            "steps": [
                {"title": "S", "minutes": 3, "instructions": ["Do X."]}
            ],
        }
        html = render_plan_html(plan)
        assert "checagem" not in html.lower()

    def test_accessibility_pack_key(self):
        """accessibility_pack (not _draft) should also be rendered."""
        plan = _minimal_plan()
        plan["accessibility_pack"] = {
            "media_requirements": ["legenda obrigatoria"],
            "ui_recommendations": [],
        }
        html = render_plan_html(plan)
        assert "legenda obrigatoria" in html

    def test_accessibility_pack_empty_media_and_ui(self):
        plan = _minimal_plan()
        plan["accessibility_pack"] = {
            "media_requirements": [],
            "ui_recommendations": [],
        }
        html = render_plan_html(plan)
        assert "Acessibilidade" in html
        # No sub-sections since lists are empty
        assert "Requisitos de m" not in html

    def test_html_escaping(self):
        plan = {
            "title": "<script>alert(1)</script>",
            "steps": [{"title": "ok", "minutes": 1, "instructions": ["<b>bold</b>"]}],
        }
        html = render_plan_html(plan)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html


# ---------------------------------------------------------------------------
# render_audio_script
# ---------------------------------------------------------------------------

class TestRenderAudioScript:

    def test_basic_output(self):
        text = render_audio_script(_sample_plan())
        assert "Plano Exemplo" in text
        assert "Etapa 1" in text
        assert "Etapa 2" in text
        assert "Faca X." in text
        assert "Faca Z." in text

    def test_student_plan_summary_included(self):
        text = render_audio_script(_sample_plan())
        assert "Resumo (vers" in text
        assert "Resumo 1." in text

    def test_no_student_plan(self):
        plan = _minimal_plan()
        text = render_audio_script(plan)
        assert "Resumo" not in text
        assert "Minimo" in text

    def test_assessment_checagem(self):
        text = render_audio_script(_sample_plan())
        assert "Checagem" in text
        assert "Ok 1" in text

    def test_step_without_assessment(self):
        plan = _minimal_plan()
        text = render_audio_script(plan)
        assert "Checagem" not in text

    def test_steps_and_instructions_numbered(self):
        text = render_audio_script(_sample_plan())
        assert "Etapa 1:" in text
        assert "Passo 1:" in text
        assert "Etapa 2:" in text

    def test_student_plan_with_empty_summary(self):
        plan = _sample_plan()
        plan["student_plan"] = {"summary": []}
        text = render_audio_script(plan)
        # No "Resumo" section since summary is empty / falsy
        assert "Resumo (vers" not in text

    def test_assessment_limited_to_three(self):
        plan = {
            "title": "Test",
            "steps": [
                {
                    "title": "S1",
                    "minutes": 5,
                    "instructions": ["A"],
                    "assessment": ["a1", "a2", "a3", "a4", "a5"],
                }
            ],
        }
        text = render_audio_script(plan)
        # Only first 3 assessments
        assert "a1" in text
        assert "a3" in text
        assert "a4" not in text


# ---------------------------------------------------------------------------
# render_student_plain_text
# ---------------------------------------------------------------------------

class TestRenderStudentPlainText:

    def test_with_student_plan(self):
        text = render_student_plain_text(_sample_plan())
        assert "Plano Exemplo" in text
        assert "Resumo 1." in text
        assert "Resumo 2." in text
        assert "Etapa 1:" in text
        assert "Instrucao aluno 1" in text
        assert "Etapa 2:" in text
        assert "Instrucao aluno 2" in text
        assert "termo1: definicao1" in text
        assert "termo2: definicao2" in text

    def test_student_plan_without_glossary(self):
        plan = _sample_plan()
        plan["student_plan"]["glossary"] = []
        text = render_student_plain_text(plan)
        assert "rio" not in text  # "Glossario" should not appear

    def test_student_plan_non_dict_step_skipped(self):
        plan = _sample_plan()
        plan["student_plan"]["steps"] = [
            "not a dict",
            {"title": "Real", "instructions": ["Do it"]},
        ]
        text = render_student_plain_text(plan)
        # The non-dict step is skipped, so "Etapa 1" corresponds to the real dict
        assert "Real" in text

    def test_fallback_to_student_friendly_summary(self):
        plan = {
            "title": "Plano Fallback",
            "steps": [{"title": "S1", "instructions": ["A"]}],
            "student_friendly_summary": ["Linha 1", "Linha 2"],
        }
        text = render_student_plain_text(plan)
        assert "Plano Fallback" in text
        assert "Linha 1" in text
        assert "Linha 2" in text

    def test_fallback_no_summary_at_all(self):
        plan = {
            "title": "Plano Vazio",
            "steps": [{"title": "S1", "instructions": ["A"]}],
        }
        text = render_student_plain_text(plan)
        assert "Plano Vazio" in text
        assert "sem vers" in text

    def test_student_plan_with_summary_only(self):
        plan = {
            "title": "T",
            "steps": [],
            "student_plan": {"summary": ["Linha A"]},
        }
        text = render_student_plain_text(plan)
        assert "Linha A" in text

    def test_student_plan_with_steps_only(self):
        plan = {
            "title": "T",
            "steps": [],
            "student_plan": {
                "steps": [{"title": "E1", "instructions": ["I1"]}],
            },
        }
        text = render_student_plain_text(plan)
        assert "E1" in text
        assert "I1" in text

    def test_student_plan_step_without_instructions(self):
        plan = {
            "title": "T",
            "steps": [],
            "student_plan": {
                "summary": ["s"],
                "steps": [{"title": "E1"}],
            },
        }
        text = render_student_plain_text(plan)
        assert "E1" in text


# ---------------------------------------------------------------------------
# render_export (dispatcher)
# ---------------------------------------------------------------------------

class TestRenderExport:

    def test_audio_script_variant(self):
        text = render_export(_sample_plan(), "audio_script")
        assert "Plano Exemplo" in text
        assert "Etapa 1" in text

    def test_visual_schedule_json_variant(self):
        raw = render_export(_sample_plan(), "visual_schedule_json")
        data = json.loads(raw)
        assert "visual_schedule" in data

    def test_student_plain_text_variant(self):
        text = render_export(_sample_plan(), "student_plain_text")
        assert "Plano Exemplo" in text

    def test_standard_html_variant(self):
        html = render_export(_sample_plan(), "standard_html")
        assert "<!doctype html>" in html

    def test_screen_reader_html_variant(self):
        html = render_export(_sample_plan(), "screen_reader_html")
        assert "skip-link" in html

    def test_unknown_variant_falls_through_to_html(self):
        html = render_export(_sample_plan(), "nonexistent_variant")
        assert "<!doctype html>" in html
