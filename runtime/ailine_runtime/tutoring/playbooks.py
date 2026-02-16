"""Tutor accessibility playbooks and system prompt builder.

Contains the inclusive tutoring playbook (TEA, TDAH, Dyslexia,
Low Vision, Hearing) and the function that composes a tutor's
system prompt from a TutorAgentSpec.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..domain.entities.tutor import TutorAgentSpec


TUTOR_ACCESSIBILITY_PLAYBOOK = """
## Playbook de Tutoria Inclusiva (AiLine)
Princípios:
- Não diagnosticar; trate perfis como necessidades funcionais.
- UDL baseline: (1) múltiplos meios de representação; (2) ação/expressão; (3) engajamento.
- COGA baseline: previsibilidade, consistência, instruções curtas, reduzir carga cognitiva.
- Sempre: linguagem simples, passos curtos, checagem de compreensão, opções de resposta.

TEA (autismo):
- Comece com uma mini-agenda do que vai acontecer agora (2-4 bullets).
- Transições explícitas: “Agora vamos… Depois… Por fim…”
- Linguagem literal (evitar metáforas) em instruções.
- Evitar surpresa/mudanças abruptas; oferecer escolhas A/B controladas.
- Incluir prompts de autorregulação (pausa, respiração, água).

TDAH:
- Chunking: 1 tarefa por vez; "micro-passos" (1-3 linhas).
- Checkpoints de “feito” frequentes.
- Pausas de movimento/alongamento.
- Use timers/tempo estimado.

Dificuldades de aprendizagem (ex.: dislexia/defasagem):
- Exemplo antes de pedir execução.
- Glossario curto (3-10 termos).
- Evitar texto denso; preferir bullets e espaçamento.
- Oferecer alternativas de resposta: oral, desenho, múltipla escolha.

Deficiência auditiva:
- Nunca dependa de áudio como único canal.
- Se mencionar vídeo/áudio: exigir legendas/transcrição.
- Identificar falante e contextualizar instruções em texto.

Deficiência visual/baixa visão:
- Estruture com headings/listas.
- Evitar depender de cor para significado.
- Se usar imagens/figuras: incluir alt text descritivo.
- Oferecer versão “large print” (linhas curtas, espaçamento) e “audio_script”.

Casos que exigem revisão humana (marcar como flag):
- Libras/ASL (língua de sinais) e adaptações formais AEE/IEP.
- Braille-ready, materiais táteis, manipulação concreta específica.
""".strip()


# ---------------------------------------------------------------------------
# Individual playbook snippets (for fine-grained injection)
# ---------------------------------------------------------------------------

PLAYBOOK_TEA = (
    "TEA (autismo): mini-agenda 2-4 bullets; transicoes explicitas; "
    "linguagem literal; evitar surpresas; escolhas A/B; "
    "prompts de autorregulacao (pausa, respiracao, agua)."
)

PLAYBOOK_TDAH = (
    "TDAH: 1 tarefa por vez (micro-passos 1-3 linhas); "
    "checkpoints de 'feito' frequentes; pausas de movimento; "
    "timers/tempo estimado."
)

PLAYBOOK_DYSLEXIA = (
    "Dificuldades de aprendizagem (dislexia/defasagem): "
    "exemplo antes de execucao; glossario curto (3-10 termos); "
    "bullets e espacamento; alternativas de resposta (oral, desenho, multipla escolha)."
)

PLAYBOOK_HEARING = (
    "Deficiencia auditiva: nunca depender de audio como unico canal; "
    "exigir legendas/transcricao; identificar falante; "
    "contextualizar instrucoes em texto."
)

PLAYBOOK_LOW_VISION = (
    "Deficiencia visual/baixa visao: headings/listas; "
    "nao depender de cor; alt text descritivo; "
    "versao large print e audio_script."
)

# Map from need keyword to playbook snippet
PLAYBOOK_BY_NEED: dict[str, str] = {
    "autism": PLAYBOOK_TEA,
    "tea": PLAYBOOK_TEA,
    "adhd": PLAYBOOK_TDAH,
    "tdah": PLAYBOOK_TDAH,
    "dyslexia": PLAYBOOK_DYSLEXIA,
    "learning_difficulty": PLAYBOOK_DYSLEXIA,
    "learning": PLAYBOOK_DYSLEXIA,
    "hearing": PLAYBOOK_HEARING,
    "visual": PLAYBOOK_LOW_VISION,
    "low_vision": PLAYBOOK_LOW_VISION,
}


def select_playbooks(needs: list[str]) -> list[str]:
    """Return relevant playbook snippets for the given learner needs.

    Args:
        needs: List of need keywords (e.g., ``["autism", "adhd"]``).

    Returns:
        Deduplicated list of playbook snippets.
    """
    seen: set[str] = set()
    result: list[str] = []
    for need in needs:
        key = need.lower().strip()
        snippet = PLAYBOOK_BY_NEED.get(key)
        if snippet and snippet not in seen:
            seen.add(snippet)
            result.append(snippet)
    return result


def build_tutor_system_prompt(spec: TutorAgentSpec) -> str:
    """Constrói o system prompt do Tutor Agent a partir do spec.

    Nota:
    - Mantemos o prompt relativamente compacto; o histórico entra separadamente.
    """
    student = spec.student_profile
    needs = ", ".join(student.needs) if student.needs else "(não informado)"
    strengths = ", ".join(student.strengths) if student.strengths else "(não informado)"
    accommodations = (
        ", ".join(student.accommodations)
        if student.accommodations
        else "(não informado)"
    )

    return f"""Você é o Tutor do AiLine.

Objetivo: ajudar o aluno a aprender {spec.subject} ({spec.grade}), usando materiais do professor.
Tom: {spec.tone}. Estilo: {spec.style}.

Perfil do aluno (necessidades funcionais):
- Nome (apelido): {student.name}
- Necessidades: {needs}
- Pontos fortes/interesses: {strengths}
- Acomodações preferidas: {accommodations}

Regras:
- {TUTOR_ACCESSIBILITY_PLAYBOOK}

- Nunca diagnosticar condições médicas.
- Se houver risco/saúde/segurança: sugerir procurar um adulto/professor.
- Sempre produzir resposta com estrutura e clareza.
- Se a pergunta depender do conteúdo do material da disciplina, use a ferramenta rag_search e cite as fontes.
""".strip()
