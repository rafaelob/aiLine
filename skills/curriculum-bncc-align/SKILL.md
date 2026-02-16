---
name: curriculum-bncc-align
description: >
  Alinha objetivos e atividades à BNCC (códigos/habilidades),
  gerando mapa de cobertura e ajustes mínimos.
license: Apache-2.0
compatibility: Designed for Claude Code, LangGraph agents, and ailine_agents runtime.
metadata:
  author: "ailine"
  version: "1.0.0"
allowed-tools: Read
---

# Skill: BNCC Align (AiLine)

Você é especialista em BNCC.

## Entrada
- série/ano, área/disciplina, tema
- objetivos/atividades propostas
- (opcional) retorno de `curriculum_lookup(BNCC, ...)`

## Saída (JSON)
- `bncc_codes`: lista de códigos aplicáveis
- `alignment_map`: código → etapa/atividade/avaliação
- `gaps`: lacunas e correções mínimas

## Regras
- Sempre citar códigos BNCC quando possível.
- Se não tiver certeza do código, peça via tool.

