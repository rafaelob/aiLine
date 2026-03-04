# AGENTS.md — Instruções do Projeto (para agentes)

> Este arquivo é para **instruções duráveis** e auditáveis sobre o projeto.
> Ele deve ser curto, objetivo e versionado.

## Objetivo do projeto (3–5 linhas)
- ...

## Regras não negociáveis
- Segurança: não vazar segredos (tokens, chaves, credenciais) em logs/artefatos.
- Qualidade: testes obrigatórios para mudanças relevantes.
- Observabilidade: registrar `core_tokens`, `total_tokens`, `tool_budget_tokens`.
- Aprovações: ações irreversíveis exigem confirmação explícita.

## Orçamento de contexto (X/Y)
- X_core_tokens: <defina>
- Y_total_tokens: <defina>
- rolling_summary_max_tokens: <defina>
- anchor_turns: <defina>

## Stack / arquitetura
- Linguagens:
- Dependências críticas:
- Serviços externos:
- Convenções:

## Como rodar / testar
- `make test`
- `make lint`
- `make format`

## Pastas importantes
- `src/`
- `docs/`
- `tests/`

## Tooling / MCP / Skills
- MCP servers:
  - <nome> — <o que faz> — <read-only|write> — <aprovação?>
- Skills:
  - <skill> — <quando usar>

## Segurança operacional
- Onde ficam segredos (ex.: vault/ENV):
- Padrões de redaction:
- Logs e retenção:

## Como pedir esclarecimentos
Peça esclarecimentos quando:
- faltam requisitos que bloqueiam decisão,
- há risco de fazer mudanças irreversíveis,
- há ambiguidade em limites (X/Y) ou segurança.
