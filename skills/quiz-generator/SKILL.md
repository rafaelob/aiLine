---
name: quiz-generator
description: >
  Gera quizzes/exercícios alinhados aos objetivos, com gabarito e explicações curtas,
  incluindo variações fáceis/difíceis e adaptações quando necessário.
license: Apache-2.0
compatibility: Designed for Claude Code, LangGraph agents, and ailine_agents runtime.
metadata:
  author: "ailine"
  version: "1.0.0"
allowed-tools: Read
---

# Skill: Quiz Generator (AiLine)

Crie avaliação prática e curta, alinhada aos objetivos.

## Entrada
- objetivos
- tópico e nível
- restrições (tempo, formato)
- evidências do material (opcional)

## Saída (JSON)
- `questions`: lista com:
  - tipo (múltipla escolha / aberta / verdadeiro-falso)
  - enunciado
  - alternativas (se houver)
  - resposta correta
  - explicação curta
  - variação fácil/difícil (opcional)
- `accessibility_variants`: versões com linguagem mais clara (se necessário)

## Regras
- Não cobrar conteúdo não presente nos objetivos.
- Se usar material, cite a origem via evidência quando disponível.
- Misture 1–2 questões conceituais e 1 prática.

