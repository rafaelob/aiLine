# Templates (AGENTS.md / CLAUDE.md / SKILL.md / schemas)

Este diretório contém templates prontos para copiar/colar e adaptar:

- `templates/AGENTS.md` — instruções do projeto (estilo “project instructions”)
- `templates/CLAUDE.md` — memória/regras do projeto (estilo IDE/Claude Code)
- `templates/CLAUDE.local.md` — regras locais do usuário (não versionar)
- `templates/.claude/rules/*.md` — regras por path (frontmatter com `paths:`)

Também recomendamos manter templates de *schemas* para:
- rolling summary
- tool result summary
- evidence pack

Abaixo, alguns esquemas úteis para você reutilizar.

---

## 1) Rolling summary schema (canônico)

```md
# ROLLING_SUMMARY

## Objetivo atual
- ...

## Contexto do projeto (curto)
- ...

## Decisões e racional
- [data?] decisão: ...
  - rationale: ...
  - impacto: ...

## Restrições e preferências
- ...

## Progresso / trabalho feito
- ...

## Backlog / próximos passos
- ...

## Artefatos e handles
- handle: <id/path/url> — descrição curta
```

---

## 2) Tool result summary schema

```md
## TOOL_RESULT_SUMMARY
- tool: <name>
- status: success|error
- handle: <optional>
- salient_facts:
  - ...
- caveats:
  - ...
- next_actions:
  - ...

### payload_excerpt
<trecho curto (head/tail) ou tabela compacta>
```

---

## 3) Evidence pack schema (RAG)

```md
## EVIDENCE_PACK
- query: ...

### Evidence 1
- title: ...
- url: ...
- date: ...
- relevance: 0.00–1.00
- quote: "..."
- notes: ...

### Coverage gaps
- ...
```

---

## 4) SKILL.md skeleton

```md
---
name: <skill-name>
description: <1 linha: quando usar>
---

# <Skill title>

## When to use
- ...

## Workflow
1) ...
2) ...

## Output format
- ...

## Budget rules (X/Y)
- ...

## Safety
- ...
```
