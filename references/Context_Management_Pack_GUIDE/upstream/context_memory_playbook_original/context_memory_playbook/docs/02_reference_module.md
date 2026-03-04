# Módulo de referência (Python): `contextkit`

O pacote em `src/contextkit/` é uma implementação mínima (mas extensível) de:

- Budgets X/Y (core vs tool budget)
- Rolling summary (sumarização incremental)
- Catálogo de skills com progressive disclosure (`SKILL.md`)
- Integração “genérica” com tools + compressão de outputs (handle + summary)
- Memória em grafo (SQLite) com proveniência e TTL
- Estruturas para EvidencePack (RAG)

> Objetivo: servir como “esqueleto” para você adaptar ao seu stack (OpenAI/Anthropic/OSS).

---

## 1) Componentes

### 1.1 Config e políticas
- `contextkit/config.py`
  - `Budgets`: X e Y + reservas
  - `HistoryPolicy`: âncoras e rolling summary
  - `SkillsPolicy`: budgets do índice e das skills ativas
  - `ToolsPolicy`: budgets de catálogo/schema/result
  - `RAGPolicy`: compressão de evidências
  - `Storage`: onde salvar artefatos e DB de memória

### 1.2 Montagem do contexto
- `contextkit/context_assembler.py`
  - constrói **core** (<= X) com compaction quando necessário
  - permite adicionar “tool context blocks” respeitando o teto Y

### 1.3 Rolling summary
- `contextkit/rolling_summary.py`
  - mantém um resumo canônico em schema fixo
  - pode usar LLM real (plugável) ou fallback determinístico (para demo/testes)

### 1.4 Tool outputs como “artefatos”
- `contextkit/tool_context_manager.py`
  - salva payload grande fora do prompt (arquivo)
  - devolve `TOOL_RESULT_SUMMARY` com handle + excerpt

### 1.5 Memória em grafo
- `contextkit/memory/graph_memory.py`
  - store SQLite com nodes/edges, TTL e proveniência
- `contextkit/memory/memory_manager.py`
  - política de escrita (ex.: exigir confirmação)
  - aplica writes em nós/arestas

### 1.6 RAG / Evidence packs
- `contextkit/rag/evidence_pack.py`
  - estrutura `EvidencePack` com itens (quote + URL + data)
  - compressão por orçamento
- `contextkit/rag/rag_manager.py`
  - wrapper para normalizar ferramentas de busca

---

## 2) Execução do demo

```bash
python examples/demo_minimal.py
```

O demo:
- usa budgets pequenos para forçar compaction,
- mostra como o core é mantido <= X,
- calcula tool budget como (Y − core).

---

## 3) Como integrar com provedores reais

### 3.1 OpenAI (recomendação de arquitetura)
Em geral, a forma “estado‑da‑arte” de integrar com OpenAI é:

- usar **Responses API** (estado conversacional + tools),
- usar **token counting endpoint** para métricas exatas,
- quando fizer sentido, ativar **compaction server‑side**,
- aplicar **prompt caching** (prefixo estável),
- integrar **MCP servers** como tools remotas quando aplicável.

> Este módulo não “chama” a OpenAI API por padrão (para manter o repositório sem credenciais).
> Em produção, implemente um `LLMClient` e um `ToolRunner` que chamem o seu provedor.

### 3.2 Anthropic
Se você estiver no ecossistema Anthropic/Claude:
- use prompt caching (marcando blocos cacheáveis),
- mantenha o prefixo estável e evite reordenar tools/system/messages,
- aplique o mesmo X/Y para garantir reserva de contexto para tool outputs.

---

## 4) O que você provavelmente vai adaptar

- Contagem de tokens: trocar heurística por tokenizer real / endpoint do provedor.
- Política de compaction: rolling summary vs compaction server‑side.
- “Tool selection”: heurística + LLM planner.
- Armazenamento de artefatos: S3/Blob, DB, vector store.
- Memória: adicionar memória vetorial e ranking híbrido (vetor + grafo).

---

## 5) Garantias (invariantes)

Se você usar o `ContextAssembler` como “gate”, você consegue garantir:

- **core_tokens <= X**
- **total_tokens <= Y** (desde que tool blocks sejam empacotados via budget)
- outputs grandes não entram no prompt sem compressão + handle

---

## Próximo passo

Veja `05_orchestration_reference.md` para um loop de agente completo.
