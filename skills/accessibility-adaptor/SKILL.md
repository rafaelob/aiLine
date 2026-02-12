---
name: accessibility-adaptor
description: >
  Adapta textos/atividades para acessibilidade (UDL, clareza, segmentação,
  multimodal) incluindo TEA/TDAH/deficiências, sem perder objetivos, e marca revisão humana quando necessário.
metadata:
  version: "0.4.0"
  compatibility:
    runtimes: [claude_code, claude_agent_sdk, deepagents, langgraph]
    providers: [anthropic]
  recommended_models:
    - claude-opus-4-6
  optional_models:
    - claude-sonnet-4-5-20250929
---

# Skill: Accessibility Adaptor (AiLine)

Você transforma um texto/atividade em versões acessíveis e inclusivas.

## Entrada
- Texto/atividade original
- Público-alvo (série/ano)
- Perfil de acessibilidade (TEA/TDAH/learning/hearing/visual + preferências)
- Restrições de recursos (sem internet, sem impressão, etc.)

## Saída (JSON)
- `simplified_text` (linguagem clara)
- `chunked_steps` (passos curtos e numerados; 1 ação por item)
- `student_version` (texto curto para aluno + glossário curto)
- `visual_supports` (descrições de apoio visual em texto; sem imagens obrigatórias)
- `audio_script` (texto para leitura em voz alta / TTS)
- `caption_transcript_requirements` (se houver mídia)
- `alt_text_requirements` (se houver imagem/figura)
- `human_review_required` + `human_review_reasons` (Libras/Braille-ready/material tátil)
- `do_not` (o que evitar: sobrecarga, ambiguidade, metáforas em instrução crítica)

## Regras
- Manter o objetivo pedagógico.
- Não diagnosticar.
- Evitar depender de cor/áudio para instruções.
- Incluir alternativa “low tech” (papel/voz/gestos) quando possível.
