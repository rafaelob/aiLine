# 01 — Visão e Escopo (neurodiversidade e acessibilidade como feature principal)

## 1) Visão
Professores gastam tempo demais **formatando**, adaptando e “reexplicando” aulas e tempo de menos **planejando** e acompanhando aprendizagem.

O AiLine é um copiloto que:
- lê materiais reais (apostilas, listas, slides, links),
- propõe **planos de aula** alinhados ao currículo (BNCC/US),
- gera **Student Plan** (versão aluno: linguagem simples + passos curtos + glossário),
- gera **variantes acessíveis** e exports (low distraction, screen reader, visual schedule, etc.),
- mantém o professor no controle (aprovação + edição + justificativas + checklist + flags de revisão humana).

**Princípio central:** acessibilidade não é “um modo”; é uma *propriedade do plano* e do produto.

---

## 2) O problema que queremos resolver (impacto)
Na prática, o professor enfrenta duas dores:
1) **Planejamento**: estruturar objetivos, atividades e avaliação com materiais fragmentados.
2) **Inclusão**: adaptar para necessidades reais sem “reinventar a roda” toda vez.

O AiLine resolve com:
- **UDL (Universal Design for Learning)** como baseline,
- **COGA** (acessibilidade cognitiva) para reduzir carga e aumentar previsibilidade,
- **WCAG/eMAG** para garantir que UI e exports sejam acessíveis.

---

## 3) Escopo do MVP para o hackathon

### Entrada
- Materiais do professor (PDF/Doc/Markdown; no MVP, upload ou texto colado).
- Série/ano, tema, duração.
- Currículo: **BNCC** (BR) ou “US standards” (simplificado).
- **Perfil de acessibilidade da turma**:
  - checkboxes (TEA/TDAH/aprendizagem/auditiva/visual),
  - preferências de UI/consumo (baixa distração, large print, alto contraste),
  - opcional: perfis anônimos por estudante/grupo.

### Saída (o que o demo precisa mostrar)
- Plano estruturado (JSON + render UI).
- **Student Plan** (versão aluno).
- **Relatório determinístico de acessibilidade**:
  - score + checklist + recomendações,
  - “human review required” quando aplicável (ex.: Libras/Braille-ready).
- Exports visíveis:
  - low distraction / large print / screen reader / visual schedule / áudio.

### Fora de escopo do MVP (por tempo)
- Diagnóstico ou recomendação clínica.
- Integrações complexas (LMS, autenticação, multi-tenant).
- Pipeline completo de Libras e Braille (mas o produto marca revisão humana).

---

## 4) Por que isso vence hackathon
- **Impacto**: inclusão real (não “prompt bonito”).
- **Opus 4.6 Use**: planejamento longo + refinamento com gate determinístico.
- **Depth & Execution**: arquitetura clara, logs, score, exports.
- **Demo**: outputs visuais (visual schedule + screen reader) impressionam.
