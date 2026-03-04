# 08 — RAG: Retrieval Context, Compressão e Evidence Pack com Citações

## Objetivo (SOTA)
RAG serve para **fidelidade** e **auditabilidade**. Em agentes, RAG mal feito vira:
- bloat de tokens,
- prompt injection via documentos,
- e “citações falsas”.

A solução SOTA é transformar retrieval em um **Evidence Pack**: snippets + metadados + citações + políticas de compressão.

---

## 1) Ingestão: chunking + metadados + permissões

### Metadados mínimos (por chunk)
- `doc_id`, `doc_title`, `source_url`/`uri`
- `author`/`publisher` (se aplicável)
- `created_at`, `updated_at` (se existir)
- `version`/`etag`/`sha256`
- `access_scope` (tenant/user/role)
- `tags` (domínio)
- `chunk_index`, `chunk_span`

### Permissões (não negociável)
- retrieval deve ser filtrado por ACL antes do rerank.
- logs devem redigir PII e segredos.

---

## 2) Recuperação em 2 estágios (recall → rerank)

**Stage A: recall (amplo)**
- BM25/keyword + embedding
- top 50–200 (depende da latência)

**Stage B: rerank (preciso)**
- cross-encoder / reranker / LLM rerank
- top 5–20 para o Evidence Pack

> SOTA: adicionar diversidade/MMR para evitar top‑k redundante (mesma fonte repetida).

---

## 3) Freshness/versioning (evitar “stale truth”)
- use `updated_at`/`version` para priorizar documentos recentes quando o problema é temporal.
- para compliance, fixe versões e guarde hash.

---

## 4) Compressão de contexto: como caber sem perder fé

### Técnicas SOTA (combináveis)
1) **Windowed quoting**  
   Inclua apenas as frases necessárias (trechos contíguos pequenos).
2) **Schema projection**  
   Se o documento é tabular/JSON, projete campos relevantes.
3) **Snippet packing**  
   Empacote snippets curtos de fontes diferentes, com metadados mínimos.
4) **Evidence quotas**
   - limite por fonte (evitar “dominação”)
   - limite total de tokens (budget)

### O que NÃO fazer
- Colar documentos inteiros.
- Colar páginas HTML com navegação.
- Colar “resultados de busca” sem checagem.

---

## 5) Evidence Pack (template recomendado)

```yaml
evidence_pack:
  query: "..."
  retrieved_at: "2026-02-24T00:00:00Z"
  items:
    - id: E1
      source:
        title: "..."
        publisher: "..."
        url: "https://..."
        date_published: "date not found"
        date_updated: "date not found"
        access_scope: "tenant:acme"
      excerpt: |
        "...trecho curto..."
      relevance: 0.91
      span: "L120-L150"
      hash: "sha256:..."
  constraints:
    max_total_tokens: 20000
    max_tokens_per_source: 4000
```

---

## 6) Citações e checks de fé (faithfulness)

### Regras de saída
- Respostas com afirmações factuais devem apontar para `E#` (evidence id).
- Se não houver evidência, o agente deve declarar incerteza ou pedir mais dados.

### Checks automáticos (baratos)
- **Coverage check**: cada claim “importante” tem ao menos uma evidência.
- **Attribution check**: evidência realmente contém a informação (string/semântica).
- **Conflict check**: quando duas fontes divergem, declarar e explicar.

---

## 7) Segurança: RAG e prompt injection

RAG e tool results são vetores clássicos de “context poisoning”.  
O MCP spec enfatiza que ferramentas são caminhos de execução e dados podem conter descrições untrusted.[^mcp_spec]  
OpenAI recomenda práticas de segurança ao construir agentes (inclui prevenção de misuse).[^openai_agent_safety]

**Mitigações:**
- Nunca permitir que docs “redefinam” system/dev.
- “Strip instructions” durante ingestão (remover trechos imperativos suspeitos).
- Hard rules no runtime: allowlists, approvals, limites.

---

## 8) JIT retrieval vs pre-retrieval

### Prefira JIT retrieval quando:
- a pergunta depende de uma subconsulta que o agente ainda não sabe fazer;
- o usuário muda o objetivo;
- você quer reduzir custo (recuperar só quando necessário).

### Prefira pre-retrieval quando:
- o workflow sempre exige evidência (compliance),
- há alto risco de alucinação,
- a latência do rerank é aceitável.

---

## Referências
[^mcp_spec]: Model Context Protocol, “Specification (Version 2025-06-18)”, **2025-06-18**, https://modelcontextprotocol.io/specification/2025-06-18
[^openai_agent_safety]: OpenAI API Docs, “Safety in building agents”, **date not found**, https://developers.openai.com/api/docs/guides/agent-builder-safety
