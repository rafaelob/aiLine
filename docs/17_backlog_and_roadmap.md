# 17 — Backlog e Roadmap (pós-hackathon) com acessibilidade como eixo

## 1) Pós-hackathon imediato (1–2 semanas)
- Melhorar templates por disciplina/série (BNCC por área)
- UI de diffs (teacher vs student vs exports) com highlight de mudanças
- Export melhor:
  - Docx com estilos semânticos
  - HTML com design system + print styles
- “Library” de perfis e adaptações (sem PII; presets por turma)
- Persistência real em Postgres (multi-tenant básico)

---

## 2) Acessibilidade (1–2 meses)
### 2.1) Conteúdo e instrução (UDL/COGA)
- Calibração de nível de leitura (Português) e controle explícito de complexidade
- Geração automática de exemplos graduais (modeling → guided practice → independent)
- Banco de “micro-acomodações” por necessidade (TEA/TDAH/deficiências) para consistência
- Opções de avaliação/expressão:
  - oral, desenho, manipulação, MCQ, apresentação

### 2.2) UI e QA (WCAG/eMAG)
- Auditoria contínua WCAG (axe/pa11y no CI)
- Design system acessível (foco, contraste, estados, motion)
- “Reading Mode” e “Focus Mode” por usuário/aluno

### 2.3) Mídia acessível
- Pipeline de legenda/transcrição automática (com revisão humana)
- Geração de descrições de imagens (alt text) com aprovação do professor
- Suporte a AAC (comunicação alternativa):
  - pictogramas / pranchas / cartões de comunicação
- Suporte a Libras:
  - integração com intérprete/avatar/serviço e materiais bilíngues

### 2.4) Visual / Braille / Tátil
- Export Braille-ready (BRF) com revisão humana
- Pipeline para material tátil (parcerias/serviços)
- Suporte a descrições de gráficos e tabelas complexas

---

## 3) Integrações (1–2 meses)
- Google Classroom / LMS (export/import)
- Repositório de materiais por escola (multi-tenant)
- Autenticação + RBAC + consentimento + trilha de auditoria

---

## 4) Avançado (3+ meses)
- Personalização por histórico do aluno **sem PII** (preferências e performance agregada)
- Métricas de aprendizagem e recomendações (com transparência)
- Evals contínuos com datasets reais e casos de acessibilidade
- “Teacher-in-the-loop studio”:
  - editar planos com suporte de IA
  - revalidar score após edição


---

## Novo épico: Tutor Agents (por aluno) + Progress Tracking
- [ ] UI para “criar tutor” com presets (TEA/TDAH/auditiva/visual)
- [ ] Upload/ingestão de PDFs/slides para materiais
- [ ] RAG com pgvector + citações formais
- [ ] Métricas por aluno (progresso, tópicos difíceis)
- [ ] Modo responsável: parental/guardian + limites de conteúdo
