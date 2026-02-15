# 00 — Hackathon Answer (submissão)

## Nome do projeto
**AiLine = Adaptive Inclusive Learning — Individual Needs in Education**

_Subtítulo:_ Adaptive Inclusive Lesson Planner (Claude Opus 4.6 + Pydantic AI + LangGraph)

## Descrição curta (100–200 palavras)
AiLine transforma materiais reais de sala de aula (apostilas, PDFs, slides e links) em planos de aula alinhados ao currículo (BNCC/CCSS/NGSS) — com **acessibilidade como feature central**, não como "modo".

O runtime gera um pacote completo por aula: **plano do professor**, **Student Plan** (versão aluno em linguagem simples, passos curtos, glossário e opções de resposta) e um **Accessibility Pack** com adaptações para **autismo (TEA)**, **TDAH**, dificuldades de aprendizagem, **deficiência auditiva** (legendas/transcrições + redundância visual + Libras via VLibras) e **deficiência visual/baixa visão** (estrutura semântica, alt text, large print e TTS). Um **Quality Gate determinístico** calcula score (0-100) e checklist de inclusão, sinaliza "human review required" e força refinamento antes do output final.

Arquitetura hexagonal (Ports-and-Adapters): 4 **agentes tipados** (Planner, Executor, QualityGate, Tutor) com **Pydantic AI 1.58** orquestrados por **LangGraph** em pipeline paralelo, usando **Claude Opus 4.6** como modelo principal. **SmartRouter** multi-LLM (Anthropic/OpenAI/Gemini) seleciona o modelo ideal por complexidade. 14 tipos de SSE com replay Redis e garantia terminal. 9 temas WCAG AAA, 3 idiomas, 10 variantes de export. Glass Box: toda decisão de IA é visível, pontuada e auditável. **145 features. 3,087 testes. 60 ADRs. Construído em uma semana.**

## Repositório / código
- (link do GitHub)

## Demo (vídeo)
- (link do Loom/YouTube)
