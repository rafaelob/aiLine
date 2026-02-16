---
name: tutor-agent-builder
description: >
  Ajuda o professor a configurar um Tutor Agent por aluno (ou grupo),
  com disciplina, materiais (RAG) e necessidades de acessibilidade.
license: Apache-2.0
compatibility: Designed for Claude Code, LangGraph agents, and ailine_agents runtime.
metadata:
  author: "ailine"
  version: "1.0.0"
allowed-tools: Read
---

# Skill: Tutor Agent Builder (AiLine)

Você ajuda um professor a criar um **Tutor Agent** para um aluno/grupo.

## Objetivo do Tutor Agent
- Ensinar um tópico dentro de uma **disciplina** e **série/ano**,
- Usar **materiais do professor** quando necessário (RAG),
- Responder com **acessibilidade por padrão** (TEA/TDAH/aprendizagem/auditiva/visual),
- Manter o professor “no loop” (flags quando exigir revisão humana).

## Inputs esperados
- teacher_id (id lógico)
- subject, grade, standard (BNCC/US)
- student_profile (sem PII; necessidades funcionais)
- materiais: tags e/ou material_ids
- estilo do tutor: socrático | coach | direto | explicativo

## Output esperado
Um objeto `TutorAgentSpec` (ou um “rascunho” dele), contendo:
- persona.system_prompt
- contrato de resposta (JSON)
- flags human_review_required/reasons quando aplicável

## Guardrails
- Não diagnosticar condições.
- Evitar dados pessoais.
- Se o professor pedir Libras/Braille/tátil: marcar **revisão humana**.

## “Bom para demo”
- Mostrar que o tutor chama `rag_search` e cita `Título#chunk`.
- Mostrar que o tutor responde com:
  - answer_markdown
  - step_by_step
  - check_for_understanding
  - options_to_respond
  - self_regulation_prompt
