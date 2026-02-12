# 03 — Jornadas do Usuário e Fluxos (MVP)

## 1) Professor (fluxo principal)
### 1.1) “Gerar Plano a partir de Materiais” (com acessibilidade)
1) Professor faz upload / cola texto / fornece links dos materiais.
2) Seleciona: série/ano, duração, tema, objetivo macro, currículo (BNCC/US).
3) Define **perfil de acessibilidade da turma** (sem diagnóstico):
   - checklist rápido (TEA / TDAH / dificuldades de aprendizagem / auditiva / visual),
   - preferências de UI/consumo (baixa distração, large print, alto contraste, etc.),
   - opcional: perfis anônimos (ex.: “Aluno A — baixa visão”, “Aluno B — TEA sensorial”).
4) Clica “Gerar”.
5) Backend cria um `Run` e inicia pipeline:
   - **Planner** (DeepAgents + Opus 4.6): rascunho estruturado + **student_plan** + **accessibility_pack_draft**
   - **Quality Gate**: score + checklist + recomendações (determinístico)
   - (Opcional) Refinamento automático: o Planner recebe feedback e melhora o draft
   - **Executor** (Claude Agent SDK + MCP): relatório determinístico + exports + save
6) UI mostra:
   - progresso (etapas),
   - tool calls relevantes,
   - score/checklist e correções,
   - tabs com o output final.

### 1.2) “Revisar e aprovar” (humano no loop)
1) Professor abre o plano final.
2) Revisa:
   - objetivos e sequência,
   - ritmo/tempo,
   - adaptações por perfil,
   - pontos marcados como **human review required** (ex.: Libras/Braille-ready).
3) Ajusta (no MVP pode ser “editar no front”, ou “copiar e editar”).

### 1.3) “Exportar para usar em sala”
O professor exporta:
- HTML padrão,
- **low distraction**,
- **large print**,
- **screen reader**,
- **visual schedule** (cards),
- texto simples (student_plain_text),
- script de áudio (TTS).

---

## 2) Professor (fluxo de revisão de acessibilidade)
### 2.1) “Relatório de Acessibilidade”
1) Professor abre o relatório do run.
2) Vê:
   - score total e por categoria (estrutura / cognitivo / previsibilidade / mídia),
   - checklist aplicado (pass/fail),
   - riscos e warnings (“vídeo sem legenda?”, “passos longos demais?”, “sem pausas?”),
   - recomendações (“quebrar etapas longas”, “adicionar agenda e transições”),
   - flags de revisão humana (quando aplicável).

**Meta do MVP:** facilitar “aprovação consciente”, não automatizar decisões pedagógicas.

---

## 3) Aluno (fluxo opcional do MVP)
### 3.1) “Versão aluno” (Student Plan)
O aluno recebe:
- resumo em linguagem simples,
- passos curtos e numerados,
- check for understanding,
- opções de resposta (oral/desenho/MCQ),
- glossário curto,
- menos texto por tela.

### 3.2) “Modo acessível” (preferências por estudante/turma)
No produto, o aluno (ou professor) ativa:
- baixa distração / reduzir movimento,
- fonte maior / espaçamento,
- alto contraste,
- leitura em voz alta (TTS),
- cronograma visual (cards com duração).

> No MVP: isso pode aparecer como tabs/toggles no front do demo.

---

## 4) AEE / coordenação pedagógica (fluxo de revisão humana)
Mesmo em MVP, é importante mostrar que o sistema sabe **quando parar**.

### 4.1) “Human review required”
Se o perfil pedir:
- Libras / língua de sinais (material bilíngue, intérprete),
- Braille-ready / material tátil,
- adequações formais de AEE/IEP,

o relatório marca **human_review_required** com razões. O professor decide:
- seguir com adaptações automáticas (baixa/ média),
- ou encaminhar para AEE/coordenação antes de aplicar.

---

## 5) Casos “combinados” (realidade de sala)
Turmas reais misturam necessidades (ex.: TEA + TDAH + baixa visão).
No MVP, a estratégia é:
- gerar **duas variantes** quando houver conflito (ex.: “apoio visual rico” vs “baixa distração”),
- sempre garantir primeiro “acesso ao conteúdo” (visual/auditivo), depois “carga cognitiva”, depois “sensorial”.


### 1.2) “Criar Tutor Agent por aluno” (tutoria personalizada)
1) Professor escolhe um aluno (ou grupo) e define um **perfil funcional** (sem diagnóstico/PII):
   - necessidades (TEA/TDAH/aprendizagem/auditiva/visual),
   - preferências (passos curtos, agenda visual, texto > áudio),
   - pontos fortes/interesses (para engajamento).
2) Seleciona disciplina + série/ano + currículo (BNCC/US).
3) Seleciona materiais que o tutor pode usar (por tags, por disciplina ou por IDs).
4) Escolhe estilo: **socrático** (perguntas guiadas), coach (encorajador), direto (explicativo).
5) Clica “Criar Tutor”.
6) O sistema persiste um `TutorAgentSpec` e cria sessões de tutoria sob demanda.

---

## 2) Aluno (tutoria)
### 2.1) “Conversar com meu Tutor”
1) Aluno abre a sessão de tutoria.
2) Faz uma pergunta (ex.: “como somar frações?”).
3) O tutor:
   - busca evidências nos materiais via `rag_search` quando necessário,
   - responde com passos curtos + checagem de compreensão + opções de resposta,
   - aplica adaptações (TEA/TDAH/auditiva/visual) e marca flags quando precisa de revisão humana.
4) A UI mostra:
   - resposta + passo a passo,
   - “check for understanding”,
   - citações (materiais usados),
   - e recomendações de pausa/autorregulação.
