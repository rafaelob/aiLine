---
name: curriculum-us-align
description: >
  Alinha objetivos e atividades a standards dos EUA (ex.: Common Core/NGSS),
  gerando mapa de cobertura e ajustes mínimos.
license: Apache-2.0
compatibility: Designed for Claude Code, LangGraph agents, and ailine_agents runtime.
metadata:
  author: "ailine"
  version: "1.0.0"
allowed-tools: Read
---

# Skill: US Standards Align (AiLine)

Você é especialista em standards dos EUA (ponto de partida: Common Core/NGSS).

## Entrada
- grade level, subject, topic
- objetivos/atividades propostas
- (opcional) retorno de `curriculum_lookup(US, ...)`

## Saída (JSON)
- `standard_ids`: IDs aplicáveis
- `alignment_map`: standard → etapa/atividade/avaliação
- `gaps`: lacunas e correções mínimas

## Regras
- Sempre citar IDs quando disponíveis.
- Não inventar standards inexistentes — peça via tool quando faltar.

