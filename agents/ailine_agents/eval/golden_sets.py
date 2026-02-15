"""Golden test sets for agent evaluation.

Each golden set defines:
- scenario_id: Unique identifier
- prompt: The input to the agent
- expected_*: Structural expectations for rubric scoring
- model_config: Pinned model for reproducibility

5 scenarios per agent type: Planner, QualityGate, Tutor.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Planner golden scenarios (5)
# ---------------------------------------------------------------------------

PLANNER_GOLDEN: list[dict[str, Any]] = [
    {
        "id": "planner-001-fracoes-5ano",
        "prompt": (
            "Crie um plano de estudo de Matematica para 5o ano sobre fracoes. "
            "Padrao BNCC. Inclua 3 passos de aula com tempos. "
            "Objetivos: EF05MA03 - Comparar e ordenar fracoes."
        ),
        "expected_subject": "Matematica",
        "expected_grade": "5",
        "expected_standard": "BNCC",
        "expected_min_steps": 3,
        "expected_min_objectives": 1,
        "threshold": 70.0,
    },
    {
        "id": "planner-002-ecossistemas-7ano",
        "prompt": (
            "Crie um plano de Ciencias para 7o ano: Ecossistemas e cadeia alimentar. "
            "Padrao BNCC. Adapte para turma com 2 alunos TEA (precisam de previsibilidade) "
            "e 1 aluno com TDAH."
        ),
        "expected_subject": "Ciencias",
        "expected_grade": "7",
        "expected_standard": "BNCC",
        "expected_min_steps": 2,
        "expected_min_objectives": 1,
        "threshold": 70.0,
    },
    {
        "id": "planner-003-poesia-8ano",
        "prompt": (
            "Plano de Lingua Portuguesa, 8o ano: Poesia brasileira - figuras de linguagem. "
            "Padrao BNCC. 4 etapas: leitura, analise, producao e compartilhamento. "
            "Inclua adaptacao para aluno com deficiencia visual."
        ),
        "expected_subject": "Lingua Portuguesa",
        "expected_grade": "8",
        "expected_standard": "BNCC",
        "expected_min_steps": 4,
        "expected_min_objectives": 1,
        "threshold": 70.0,
    },
    {
        "id": "planner-004-historia-6ano",
        "prompt": (
            "Plano de Historia para 6o ano: Civilizacoes antigas (Egito e Mesopotamia). "
            "Padrao BNCC. Atividade interativa com timeline visual. "
            "Incluir glossario para alunos com dificuldade de aprendizagem."
        ),
        "expected_subject": "Historia",
        "expected_grade": "6",
        "expected_standard": "BNCC",
        "expected_min_steps": 2,
        "expected_min_objectives": 1,
        "threshold": 70.0,
    },
    {
        "id": "planner-005-geometry-4ano-us",
        "prompt": (
            "Create a Math lesson plan for 4th grade: Introduction to Angles. "
            "Common Core standard 4.MD.5. Include hands-on measurement activity. "
            "3 steps minimum."
        ),
        "expected_subject": "Math",
        "expected_grade": "4",
        "expected_standard": "US",
        "expected_min_steps": 3,
        "expected_min_objectives": 1,
        "threshold": 65.0,
    },
]


# ---------------------------------------------------------------------------
# QualityGate golden scenarios (5)
# ---------------------------------------------------------------------------

QUALITY_GATE_GOLDEN: list[dict[str, Any]] = [
    {
        "id": "qg-001-good-plan",
        "prompt": (
            "Avalie este plano de aula: Titulo: Fracoes para 5o ano. "
            "Objetivos: EF05MA03 - Comparar fracoes. "
            "Passos: 1) Introducao 15min com material concreto 2) Atividade em duplas 20min "
            "3) Avaliacao formativa 10min. "
            "Adaptacoes: visual schedule para TEA, pausas extras para TDAH."
        ),
        "expected_score_range": (65, 100),
        "expected_status": "accept",
        "threshold": 70.0,
    },
    {
        "id": "qg-002-mediocre-plan",
        "prompt": (
            "Avalie: Titulo: Ciencias. Objetivos: aprender. "
            "Passos: 1) Explicar 40min. Sem adaptacoes de acessibilidade."
        ),
        "expected_score_range": (30, 70),
        "expected_status": "must-refine",
        "threshold": 60.0,
    },
    {
        "id": "qg-003-incomplete-plan",
        "prompt": ("Avalie: Titulo: Historia. Sem objetivos. Passos: nao definidos. Grade: nao especificada."),
        "expected_score_range": (0, 50),
        "expected_status": "must-refine",
        "threshold": 50.0,
    },
    {
        "id": "qg-004-excellent-plan",
        "prompt": (
            "Avalie este plano detalhado: Titulo: Sistema Solar para 6o ano. "
            "Objetivos: EF06CI13 - Relacionar diferentes observacoes do ceu. "
            "Passos: 1) Video introdutorio 10min 2) Discussao guiada 15min "
            "3) Quiz interativo 10min 4) Maquete em grupo 25min 5) Apresentacao 10min. "
            "Adaptacoes completas: visual schedule TEA, timer TDAH, alto contraste DV, "
            "descricao de audio para cegos, instrucoes simplificadas para DA."
        ),
        "expected_score_range": (75, 100),
        "expected_status": "accept",
        "threshold": 70.0,
    },
    {
        "id": "qg-005-borderline-plan",
        "prompt": (
            "Avalie: Titulo: Matematica 3o ano - Adicao. "
            "Objetivos: EF03MA04. "
            "Passos: 1) Revisao 10min 2) Exercicios 30min. "
            "Adaptacoes: nenhuma especifica, mas instrucoes claras."
        ),
        "expected_score_range": (50, 85),
        "expected_status": "refine-if-budget",
        "threshold": 60.0,
    },
]


# ---------------------------------------------------------------------------
# Tutor golden scenarios (5)
# ---------------------------------------------------------------------------

TUTOR_GOLDEN: list[dict[str, Any]] = [
    {
        "id": "tutor-001-fracoes-basicas",
        "prompt": "Oi professor! Nao entendi fracoes. O que e 1/2?",
        "expected_keywords": ["frac", "metade", "meio", "parte", "inteiro", "dividir"],
        "direct_answer_markers": [],
        "threshold": 65.0,
    },
    {
        "id": "tutor-002-misconception",
        "prompt": "Acho que 2/4 e maior que 1/2, certo?",
        "expected_keywords": ["equival", "igual", "mesm", "simplific"],
        "direct_answer_markers": [],
        "threshold": 65.0,
    },
    {
        "id": "tutor-003-offtopic",
        "prompt": "Conta uma piada de matematica!",
        "expected_keywords": ["estud", "aprend", "aula", "matematic"],
        "direct_answer_markers": [],
        "threshold": 60.0,
    },
    {
        "id": "tutor-004-clarification",
        "prompt": "Nao entendi a explicacao sobre angulos. Pode explicar de outro jeito?",
        "expected_keywords": ["angul", "grau", "gir", "exemplo", "imagin"],
        "direct_answer_markers": [],
        "threshold": 60.0,
    },
    {
        "id": "tutor-005-greeting",
        "prompt": "Ola! Bom dia!",
        "expected_keywords": ["ola", "bom", "dia", "ajud", "aprender"],
        "direct_answer_markers": [],
        "threshold": 55.0,
    },
]
