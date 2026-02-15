from __future__ import annotations

import json
from html import escape
from typing import Any


def _css_for_variant(variant: str) -> str:
    # Keep CSS minimal for hackathon; in product this becomes a proper design system.
    base = (
        ":root { color-scheme: light dark; }\n"
        "body { max-width: 920px; margin: 0 auto; padding: 1.25rem;"
        " line-height: 1.6; font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }\n"
        "a { text-decoration: underline; }\n"
        "h1,h2,h3 { line-height: 1.2; }\n"
        "li { margin-bottom: 0.25rem; }\n"
        ".muted { opacity: 0.85; }\n"
        ".card { border: 1px solid rgba(127,127,127,0.35);"
        " border-radius: 12px; padding: 0.9rem 1rem; margin: 0.8rem 0; }\n"
        ".kpi { display: inline-block; padding: 0.1rem 0.45rem;"
        " border-radius: 999px; border: 1px solid rgba(127,127,127,0.35); }\n"
        ":focus { outline: 3px solid currentColor; outline-offset: 2px; }\n"
        "@media (prefers-reduced-motion: reduce) {\n"
        "  * { animation: none !important; transition: none !important;"
        " scroll-behavior: auto !important; }\n"
        "}\n"
    )

    if variant == "low_distraction_html":
        return (
            base
            + """
            body { max-width: 760px; }
            .card { border-style: dashed; }
            """
        )

    if variant == "large_print_html":
        return (
            base
            + """
            body { font-size: 20px; line-height: 1.85; }
            li { margin-bottom: 0.4rem; }
            """
        )

    if variant == "high_contrast_html":
        return (
            base
            + """
            body { background: #000; color: #fff; }
            a { color: #0ff; }
            .card { border-color: #fff; }
            """
        )

    if variant == "dyslexia_friendly_html":
        return (
            base
            + """
            body { letter-spacing: 0.02em; word-spacing: 0.06em; }
            p, li { max-width: 72ch; }
            """
        )

    if variant == "screen_reader_html":
        return (
            base + "\n.skip-link { position: absolute; left: -999px; top: -999px; }\n"
            ".skip-link:focus { left: 1rem; top: 1rem; background: #ff0;"
            " color: #000; padding: 0.5rem 0.75rem; border-radius: 8px; }\n"
        )

    if variant == "visual_schedule_html":
        return (
            base
            + """
            .schedule-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 0.75rem; }
            .schedule-card { border: 1px solid rgba(127,127,127,0.35); border-radius: 12px; padding: 0.9rem; }
            .schedule-title { font-weight: 700; margin: 0 0 0.25rem 0; }
            .schedule-meta { font-size: 0.95rem; opacity: 0.9; }
            """
        )

    return base


def _safe(text: Any) -> str:
    return escape(str(text)) if text is not None else ""


def _plan_steps(plan: dict[str, Any]) -> list[dict[str, Any]]:
    steps = plan.get("steps") or []
    return [s for s in steps if isinstance(s, dict)]


def render_visual_schedule_json(plan: dict[str, Any]) -> str:
    """Agenda/cronograma em JSON (útil para TEA/TDAH e UI com cards)."""
    cards: list[dict[str, Any]] = []
    for i, s in enumerate(_plan_steps(plan), start=1):
        cards.append(
            {
                "order": i,
                "title": s.get("title", f"Etapa {i}"),
                "minutes": s.get("minutes"),
                "goal": (
                    (s.get("assessment") or [""])[0]
                    if isinstance(s.get("assessment"), list) and s.get("assessment")
                    else ""
                ),
                "instructions_preview": (s.get("instructions") or [])[:2],
            }
        )
    return json.dumps({"visual_schedule": cards}, ensure_ascii=False, indent=2)


def render_plan_html(plan: dict[str, Any], variant: str = "standard_html") -> str:
    """Renderização mínima para demo, com variantes de acessibilidade.

    Variants suportados:
      - standard_html
      - low_distraction_html
      - large_print_html
      - high_contrast_html
      - dyslexia_friendly_html
      - screen_reader_html (skip link + landmarks)
      - visual_schedule_html (cards)
    """
    title = plan.get("title", "Plano de Aula")
    grade = plan.get("grade", "")
    objectives = plan.get("objectives", [])
    steps = _plan_steps(plan)

    css = _css_for_variant(variant)

    # screen reader landmarks
    skip = ""
    main_open = "<main id='main' role='main'>"
    if variant == "screen_reader_html":
        skip = "<a class='skip-link' href='#main'>Pular para o conteúdo principal</a>"

    parts: list[str] = []
    parts.append("<!doctype html><html lang='pt-br'><head><meta charset='utf-8'/>")
    parts.append(f"<title>{_safe(title)}</title><meta name='viewport' content='width=device-width, initial-scale=1'/>")
    parts.append(f"<style>{css}</style></head><body>")
    parts.append(skip)
    parts.append(main_open)
    parts.append(f"<h1>{_safe(title)}</h1>")
    if grade:
        parts.append(f"<p class='muted'><strong>Série/ano:</strong> {_safe(grade)}</p>")

    # Student-facing summary if present
    student_plan = plan.get("student_plan")
    if isinstance(student_plan, dict) and (student_plan.get("summary") or student_plan.get("steps")):
        parts.append("<section aria-label='Versão aluno (resumo)'>")
        parts.append("<h2>Versão aluno (resumo)</h2>")
        for line in student_plan.get("summary") or []:
            parts.append(f"<p>{_safe(line)}</p>")
        parts.append("</section>")

    if objectives:
        parts.append("<section aria-label='Objetivos'><h2>Objetivos</h2><ul>")
        for o in objectives:
            txt = o.get("text") if isinstance(o, dict) else str(o)
            parts.append(f"<li>{_safe(txt)}</li>")
        parts.append("</ul></section>")

    # Visual schedule variant
    if variant == "visual_schedule_html":
        parts.append("<section aria-label='Cronograma visual'><h2>Cronograma visual</h2>")
        parts.append("<div class='schedule-grid'>")
        for idx, s in enumerate(steps, start=1):
            parts.append("<div class='schedule-card'>")
            parts.append(f"<div class='schedule-title'>{idx}. {_safe(s.get('title', 'Etapa'))}</div>")
            parts.append(
                f"<div class='schedule-meta'><span class='kpi'>{_safe(s.get('minutes', '?'))} min</span></div>"
            )
            preview = (s.get("instructions") or [])[:2]
            if preview:
                parts.append("<ol>")
                for line in preview:
                    parts.append(f"<li>{_safe(line)}</li>")
                parts.append("</ol>")
            parts.append("</div>")
        parts.append("</div></section>")

    # Standard step-by-step
    parts.append("<section aria-label='Sequência'><h2>Sequência</h2>")
    for idx, s in enumerate(steps, start=1):
        parts.append("<div class='card'>")
        parts.append(f"<h3>{idx}. {_safe(s.get('title', 'Etapa'))}</h3>")
        parts.append(f"<p><strong>Duração:</strong> {_safe(s.get('minutes', '?'))} min</p>")
        instr = s.get("instructions") or []
        if instr:
            parts.append("<h4>Passo a passo</h4><ol>")
            for line in instr:
                parts.append(f"<li>{_safe(line)}</li>")
            parts.append("</ol>")
        acts = s.get("activities") or []
        if acts:
            parts.append("<h4>Atividades</h4><ul>")
            for a in acts:
                parts.append(f"<li>{_safe(a)}</li>")
            parts.append("</ul>")
        assess = s.get("assessment") or []
        if assess:
            parts.append("<h4>Avaliação / checagem</h4><ul>")
            for a in assess:
                parts.append(f"<li>{_safe(a)}</li>")
            parts.append("</ul>")
        parts.append("</div>")
    parts.append("</section>")

    # Accessibility pack section
    ap = plan.get("accessibility_pack") or plan.get("accessibility_pack_draft")
    if isinstance(ap, dict):
        parts.append("<section aria-label='Acessibilidade'><h2>Acessibilidade</h2>")
        media_req = ap.get("media_requirements") or []
        if media_req:
            parts.append("<h3>Requisitos de mídia</h3><ul>")
            for r in media_req:
                parts.append(f"<li>{_safe(r)}</li>")
            parts.append("</ul>")
        ui_rec = ap.get("ui_recommendations") or []
        if ui_rec:
            parts.append("<h3>Recomendações de UI</h3><ul>")
            for r in ui_rec:
                parts.append(f"<li>{_safe(r)}</li>")
            parts.append("</ul>")
        parts.append("</section>")

    parts.append("</main></body></html>")
    return "".join(parts)


def render_audio_script(plan: dict[str, Any]) -> str:
    """Versão texto para TTS/leitura em voz alta."""
    title = plan.get("title", "Plano")
    steps = _plan_steps(plan)

    lines: list[str] = [f"Título: {title}."]
    student_plan = plan.get("student_plan")
    if isinstance(student_plan, dict) and student_plan.get("summary"):
        lines.append("Resumo (versão aluno):")
        for s in student_plan.get("summary") or []:
            lines.append(f"- {s}")

    for i, s in enumerate(steps, start=1):
        lines.append(f"Etapa {i}: {s.get('title', '')}. Duração aproximada: {s.get('minutes', '?')} minutos.")
        for j, inst in enumerate(s.get("instructions") or [], start=1):
            lines.append(f"Passo {j}: {inst}")

        assess = s.get("assessment") or []
        if assess:
            lines.append("Checagem rápida:")
            for a in assess[:3]:
                lines.append(f"- {a}")

    return "\n".join(lines)


def render_student_plain_text(plan: dict[str, Any]) -> str:
    """Texto simples para aluno (para impressão/WhatsApp/TTS).

    Preferimos student_plan (se houver). Caso contrário, usa student_friendly_summary.
    """
    title = plan.get("title", "Plano")
    lines: list[str] = [f"{title}", ""]

    student_plan = plan.get("student_plan")
    if isinstance(student_plan, dict) and (student_plan.get("summary") or student_plan.get("steps")):
        for s in student_plan.get("summary") or []:
            lines.append(f"- {s}")
        lines.append("")
        for i, step in enumerate(student_plan.get("steps") or [], start=1):
            if not isinstance(step, dict):
                continue
            lines.append(f"Etapa {i}: {step.get('title', '')}")
            for j, inst in enumerate(step.get("instructions") or [], start=1):
                lines.append(f"  {j}. {inst}")
            lines.append("")
        glossary = student_plan.get("glossary") or []
        if glossary:
            lines.append("Glossário (termos):")
            for g in glossary[:10]:
                lines.append(f"- {g}")
        return "\n".join(lines).strip()

    # fallback
    summary = plan.get("student_friendly_summary") or []
    if summary:
        for s in summary:
            lines.append(f"- {s}")
    else:
        lines.append("(sem versão aluno no plano)")

    return "\n".join(lines).strip()


def render_export(plan: dict[str, Any], variant: str) -> str:
    """Dispatcher único para export_variant tool."""
    if variant == "audio_script":
        return render_audio_script(plan)
    if variant == "visual_schedule_json":
        return render_visual_schedule_json(plan)
    if variant == "student_plain_text":
        return render_student_plain_text(plan)
    return render_plan_html(plan, variant=variant)
