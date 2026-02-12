# 15 — Skills: desenvolvimento (Claude Code) vs runtime (DeepAgents/Agent SDK)

## 1) TL;DR (o que vale para o hackathon)
No AiLine, **Skills existem em dois “mundos”**:

1) **Dev (Claude Code / CLI):** você usa skills para acelerar e padronizar o desenvolvimento (ex.: gerar planos, revisar acessibilidade, escrever rubricas, gerar testes).
2) **Runtime (Planner/Persona em DeepAgents):** o runtime carrega skills como **módulos de instrução** para melhorar planejamento e consistência **sem virar dependência de UI/CLI**.

> Decisão de design: no MVP, **skills são “conhecimento e padrões”**, não um serviço externo. O cérebro continua sendo o **Opus 4.6**, e o “controle” vem do **Quality Gate determinístico + tool whitelist**.

---

## 2) Onde ficam as skills (padrão do repo)
**Fonte de verdade:** `.claude/skills/`

Também mantemos uma cópia em `skills/` para:
- facilitar leitura em GitHub,
- permitir consumo por runtimes/SDKs que esperam um diretório “skills” convencional.

Estrutura:
- `.claude/skills/<skill-name>/SKILL.md`
- `skills/<skill-name>/SKILL.md` (espelho)

---

## 3) Skills no desenvolvimento (Claude Code)
### 3.1) O que você ganha no dev
- comandos repetíveis (estilo “slash commands”),
- padronização de output (ex.: sempre gerar plano no schema),
- checklists (acessibilidade / segurança / testes),
- “prompts corporativos” versionados.

### 3.2) Segurança (dev)
No Claude Code, a frontmatter `allowed-tools` pode restringir ferramentas dentro de uma skill (quando suportado/funcionando no ambiente).  
No runtime, **não confiamos** nessa restrição: runtime controla ferramentas pela whitelist (`allowed_tools` no Agent SDK / tools no LangChain).

---

## 4) Skills no runtime (o que de fato está implementado neste pack)

### 4.1) Planner (DeepAgents) — **IMPLEMENTADO**
O Planner usa **DeepAgents + Opus 4.6** e carrega skills via parâmetro `skills=[...]` no `create_deep_agent(...)`.

No código:
- `runtime/ailine_runtime/planner_deepagents.py`
- Carrega os paths com: `cfg.skill_source_paths()`
- Pode desativar via env:
  - `AILINE_PLANNER_USE_SKILLS=0`

Por quê isso é bom:
- DeepAgents faz “progressive disclosure”: skills podem ser carregadas sob demanda, reduzindo contexto inicial.

### 4.2) Persona Builder do Tutor (DeepAgents) — **IMPLEMENTADO**
Quando `auto_persona=true`, o AiLine gera um system prompt do tutor com Opus 4.6.  
Esse builder também pode carregar skills:

- `runtime/ailine_runtime/tutoring/builder.py`
- Toggle:
  - `AILINE_PERSONA_USE_SKILLS=0`

### 4.3) Executor e Tutor Chat (Claude Agent SDK) — **MVP: NÃO usa Skill tool**
O Executor e o Tutor (sessão de chat) rodam no **Claude Agent SDK** e usam:
- **MCP tools** (`rag_search`, `accessibility_checklist`, `export_variant`, `save_plan`)
- **tool whitelist** por `allowed_tools`

No MVP, não ativamos o “Skill tool” para evitar:
- complexidade extra,
- confusão entre “skill como comando” vs “skill como template”,
- risco de abrir ferramentas demais por engano.

> Se vocês quiserem habilitar “Skill tool” no runtime, isso vira um *upgrade* opcional (e dá pra fazer), mas a rota mais estável para demo é: **skills → usadas no Planner/Persona**, e no Executor/Tutor manter tool whitelist estrita.

---

## 5) Configuração de skills (env vars)
Veja `.env.example`.

Variáveis:
- `AILINE_SKILL_SOURCES` (opcional)
  - vazio → usa defaults: `<repo>/.claude/skills` e `<repo>/skills` (se existirem)
  - exemplo comum rodando em `runtime/`:
    - `AILINE_SKILL_SOURCES="../.claude/skills,../skills"`
- `AILINE_PLANNER_USE_SKILLS` (`1`/`0`)
- `AILINE_PERSONA_USE_SKILLS` (`1`/`0`)

---

## 6) Como escrever uma SKILL.md (padrão recomendado)
Cada skill deve ter:
- Frontmatter YAML (nome, descrição, quando usar, etc.)
- Corpo markdown com:
  - “Sempre faça”
  - “Nunca faça”
  - formato de saída esperado (schema, bullet rules)
  - exemplos curtos

Regra prática:
- SKILL.md curto e operacional > “artigo longo”.

---

## 7) Como validar que skills estão funcionando
Checklist simples:
1) Rode `/plans/generate` com um prompt “complexo” (TEA + TDAH + baixa visão) e veja se o draft melhora consistência.
2) Rode `auto_persona=true` ao criar tutor e veja se a persona sai mais padronizada.
3) Compare com `AILINE_PLANNER_USE_SKILLS=0` para medir impacto.
