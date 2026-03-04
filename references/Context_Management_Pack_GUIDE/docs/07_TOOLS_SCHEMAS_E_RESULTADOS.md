# 07 — Ferramentas: Schemas e Resultados (Token‑Efficient Tooling) + MCP

## Por que ferramentas dominam o orçamento em agentes “reais”

Em sistemas tool-heavy, o maior consumo de tokens raramente é o chat — é:
- esquemas de tools (quando muitos),
- logs/resultados de tools,
- e “evidência” (RAG) trazida por tools.

Por isso SOTA trata ferramentas como um **produto**: design de contratos, outputs e segurança.

---

## 1) Design de tool schemas (contratos)

### Regras de ouro
1) **Nome explícito e estável**  
   Evite nomes genéricos (“query”, “fetch”). Use verbos + domínio: `db_query_orders`, `crm_get_contact`.

2) **Descrição curta, com “when to use”**  
   Uma linha para “o que faz”, uma linha para “quando usar”.

3) **Parâmetros mínimos e tipados**  
   Use JSON Schema (ou equivalente) e prefira enums ao invés de strings soltas.

4) **Determinismo e idempotência**  
   Sempre que possível, tools devem ser determinísticas e idempotentes; quando não forem (side effects), exija `confirm: true` ou approval.

5) **Escopo + permissões**  
   Ferramentas devem operar sob least privilege (escopo por tenant/user, allowlists).

OpenAI descreve “function calling” com schemas e parâmetros para chamadas de ferramentas.[^openai_function_calling]  
Anthropic discute como escrever ferramentas eficazes e como agentes podem “autoavaliar” tools.[^anthropic_tools]

---

## 2) Output shaping (a maior alavanca de tokens)

### Padrão SOTA: “concise by default, expand on demand”
Toda ferramenta deve aceitar `mode`:

- `mode: "concise"` → retorna digest + ids + contagens + top-N
- `mode: "detailed"` → retorna detalhes paginados
- `mode: "raw"` (raramente) → retorna dump completo (quase nunca vai para o contexto)

### Paginação e filtros obrigatórios
- `limit`, `offset`/`cursor`
- `fields` (projeção de schema)
- `order_by`
- `since`/`updated_after` (freshness)

### Exemplo de retorno conciso (tool result)
```json
{
  "summary": {
    "rows": 1420,
    "top_fields": ["order_id","status","total_usd","created_at"],
    "time_range": ["2026-01-01","2026-02-24"]
  },
  "sample": [
    {"order_id":"O-1001","status":"paid","total_usd":20.0},
    {"order_id":"O-1002","status":"refunded","total_usd":15.0}
  ],
  "pointer": {
    "type":"blob",
    "uri":"s3://.../orders_2026_02_24.parquet",
    "sha256":"..."
  }
}
```

> O contexto recebe `summary+sample+pointer`. O dump fica fora.

---

## 3) Resumir tool results com segurança (sem perder invariantes)

### Quando pode resumir
- Quando o output é grande e você precisa manter apenas:
  - agregados,
  - top-k,
  - e exceções/anomalias.

### Quando NÃO deve resumir
- Quando o output é **fonte de verdade jurídica** (ex.: cláusula contratual).
- Quando você precisa citar/atribuir precisamente (RAG).
- Quando o output será usado para ação irreversível (pagamentos, exclusões).

**Tática:** em outputs críticos, use “schema projection” e “windowed quoting” em vez de resumo.

---

## 4) Externalização: pointers como contrato de engenharia

Sempre que `tool_result_tokens > budget`, faça:
1) Persistência externa (blob/db/vector store)
2) Cálculo de hash (integridade)
3) Inserção no contexto apenas de:
   - digest estruturado
   - pointer (uri + hash + ttl)

Isso habilita:
- rehidratação on-demand
- auditoria
- reprocessamento

---

## 5) MCP: interoperabilidade + segurança

O MCP (Model Context Protocol) padroniza como hosts conectam ferramentas e dados externos via JSON‑RPC, com noções de hosts/clients/servers e features como Tools/Resources/Prompts.[^mcp_spec]

### Implicações práticas para Context Management
- **Tool catalogs** podem vir de servers MCP.
- “Tool annotations/descriptions” podem ser **untrusted** (o spec recomenda cautela).
- O spec enfatiza consentimento, privacidade e segurança de tools.[^mcp_spec]

### OpenAI MCP connectors
OpenAI documenta MCP servers como tools na Responses API e destaca políticas de approval (`require_approval`) e autenticação via token.[^openai_connectors_mcp]

**SOTA:** treat MCP tools as semi-trusted:
- allowlist por server,
- approval padrão para tools sensíveis,
- redaction e minimização de dados compartilhados.

---

## 6) Failure modes típicos em tooling

1) **Schema bloat** (descriptions longas, exemplos demais)  
   → reduzir descrições, mover exemplos para docs externas.

2) **Tool output injection**  
   → marcar tool output como untrusted e instruir o modelo a ignorar instruções contidas em dados.

3) **Non‑idempotent tool misuse**  
   → exigir confirmação/hitl; separar tool `preview` e tool `commit`.

4) **Ambiguidade de tool selection**  
   → melhorar naming, “when to use”, e adicionar router/selector.

---

## Referências
[^openai_function_calling]: OpenAI API Docs, “Function calling”, **date not found**, https://platform.openai.com/docs/guides/function-calling
[^anthropic_tools]: Anthropic Engineering, “Writing effective tools for agents — with agents”, **Published Sep 11, 2025**, https://www.anthropic.com/engineering/writing-tools-for-agents
[^mcp_spec]: Model Context Protocol, “Specification (Version 2025-06-18)”, **2025-06-18**, https://modelcontextprotocol.io/specification/2025-06-18
[^openai_connectors_mcp]: OpenAI API Docs, “Connectors and MCP servers”, **date not found**, https://developers.openai.com/api/docs/guides/tools-connectors-mcp
