# 13 — Anti‑padrões (e correções) em Context Management

## 1) “Guardar tudo porque cabe”
**Sintoma:** contexto gigante (200k–1M) com tool dumps e transcript inteiro.

**Por que é ruim:**  
- aumenta custo/latência
- piora “attention budget” e pode causar context rot[^anthropic_context_engineering]
- torna debug impossível

**Correção SOTA:** budgets por slice + digests + pointers + evidence packs.

---

## 2) “System prompt como manual de 50 páginas”
**Sintoma:** system inclui policy + 200 procedimentos + 500 exemplos.

**Correção:** policy kernel + skills on-demand + caching.[^openai_prompt_caching][^openai_skills]

---

## 3) “N turnos fixos”
**Sintoma:** “mantém sempre 20 turnos”.

**Correção:** recency window por tokens + summary hierárquico + `STATE_JSON`.

---

## 4) “Tool outputs confiáveis”
**Sintoma:** tool result entra no contexto sem boundary, e o modelo obedece instruções no output.

**Correção:** treat as untrusted; strip instructions; approvals; least privilege.[^mcp_spec][^openai_agent_safety]

---

## 5) “RAG = colar documentos”
**Correção:** retrieval em 2 estágios, snippet packing, quotas e citações.

---

## 6) “Memória = texto livre”
**Correção:** durable notes schema + TTL + evidência; retrieval on-demand.

---

## 7) “Multi-agent = duplicar contexto para todos”
**Correção:** role-specific context packs + handoff package + shared memory retrieval-backed.

---

## 8) “Sempre Transfer” (handoff de controle) para qualquer subtarefa
**Problema:** custo explode, maior risco de vazamento e prompt injection via histórico/tool dumps.

**Correção:** adote **dual handoff**:
- **Delegate-first** (agents-as-tools) para subtarefas com I/O tipado.
- **Transfer** apenas quando a UX exige que o especialista converse diretamente.

Ver `10A_DUAL_HANDOFF_TRANSFER_VS_DELEGATE.md`.


---

## Referências
[^anthropic_context_engineering]: Anthropic Engineering, “Effective context engineering for AI agents”, **Published Sep 29, 2025**, https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
[^openai_prompt_caching]: OpenAI API Docs, “Prompt caching”, **date not found**, https://developers.openai.com/api/docs/guides/prompt-caching
[^openai_skills]: OpenAI API Docs, “Skills”, **date not found**, https://developers.openai.com/api/docs/guides/tools-skills
[^mcp_spec]: Model Context Protocol, “Specification (Version 2025-06-18)”, **2025-06-18**, https://modelcontextprotocol.io/specification/2025-06-18
[^openai_agent_safety]: OpenAI API Docs, “Safety in building agents”, **date not found**, https://developers.openai.com/api/docs/guides/agent-builder-safety
