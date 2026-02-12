# 00 — Hackathon Answer (submissão)

## Nome do projeto
**AiLine = Adaptive Inclusive Learning — Individual Needs in Education**

_Subtítulo:_ Accessible Lesson Planner Runtime (Opus 4.6 + DeepAgents + Claude Agent SDK)

## Descrição curta (100–200 palavras)
AiLine transforma materiais reais de sala de aula (apostilas, PDFs, slides e links) em planos de aula alinhados ao currículo (BNCC/US) — com **acessibilidade como feature central**, não como “modo”.

O runtime gera um pacote completo por aula: **plano do professor**, **Student Plan** (versão aluno em linguagem simples, passos curtos, glossário e opções de resposta) e um **Accessibility Pack** com adaptações para **autismo (TEA)**, **TDAH**, dificuldades de aprendizagem, **deficiência auditiva** (legendas/transcrições + redundância visual) e **deficiência visual/baixa visão** (estrutura semântica, alt text, large print e TTS). Um **Quality Gate determinístico** calcula score e checklist de inclusão, sinaliza “human review required” (ex.: Libras/Braille-ready) e força refinamento antes do output final.

Arquitetura em camadas: um **Planner** com **DeepAgents** usando **Claude Opus 4.6** para decompor e planejar com consistência; e um **Executor** com o **Claude Agent SDK** + **MCP tools** para gerar relatório, exports acessíveis (low distraction, screen reader, visual schedule, etc.) e persistir resultados com logs. O demo mostra agência end-to-end com rastreabilidade e impacto imediato em sala.

## Repositório / código
- (link do GitHub)

## Demo (vídeo)
- (link do Loom/YouTube)
