---
name: mcp-tool-discovery
description: Descobrir e filtrar tools via MCP, com catálogo mínimo e schema on-demand.
---

# MCP Tool Discovery

## When to use
Use quando:
- você tem 1+ MCP servers conectados,
- precisa descobrir tools relevantes para a tarefa,
- quer evitar “catálogo gigante” no prompt.

## Workflow
1) Liste servers MCP disponíveis.
2) Aplique allowlist/namespace para reduzir tools.
3) Monte um **catálogo mínimo**:
   - tool name
   - 1 linha de descrição
4) Só carregue schema quando uma tool for escolhida.

## Output format
- “Tools candidatas” (top‑5)
- “Por que cada uma é relevante”
- “Riscos / precisa aprovação?”

## Budget rules (X/Y)
- Catálogo MCP deve caber no tool budget.
- Use allowlist na origem sempre que possível.
- Resultados grandes → handle + summary.

## Safety
- Tools que escrevem/alteram estado exigem aprovação explícita.
- Não passe credenciais no prompt.
