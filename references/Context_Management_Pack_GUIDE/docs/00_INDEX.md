# Índice de Documentos

Use este índice como “trilha” para navegar no pack.

## Trilha rápida (2–3h)
1. **01_ESTADO_DA_ARTE.md** — princípios SOTA e implicações práticas
2. **03_ORCAMENTO_E_MATRIZ_DE_DECISAO.md** — escolha estratégia por workload
3. **03A_SESSOES_MULTI_VS_CONTINUA.md** — multi‑sessão vs sessão contínua + watermarks (crítico para long‑running)
4. **04_PROFILES_DE_ORCAMENTO.md** — aplique perfis (inclui 350k e perfis steady/burst)
5. **12_BLUEPRINT_IMPLEMENTACAO.md** — pipeline + pseudocódigo + exemplos
6. **11_OBSERVABILIDADE_E_GOVERNANCA.md** — medir para não virar superstição

## Trilha profunda (1–2 dias)
- 02_TAXONOMIA_E_CONTEXT_STACK.md
- 05_SYSTEM_PROMPT_E_SKILLS.md
- 06_HISTORICO_POR_TOKENS.md
- 07_TOOLS_SCHEMAS_E_RESULTADOS.md
- 08_RAG_EVIDENCE_PACK.md
- 09_MEMORIA_E_COMPACCAO.md
- 10_MULTI_AGENT.md
- 10A_DUAL_HANDOFF_TRANSFER_VS_DELEGATE.md
- 03A_SESSOES_MULTI_VS_CONTINUA.md
- 13_ANTI_PADROES.md
- 14_ROTEIRO_30_60_90.md
- 15_MAPA_DE_FONTES.md

## Convenções
- **Budget** = limite de tokens por fatia/camada.
- **Slice** = um bloco de contexto tipado (ex.: “STATE_JSON”, “RAG_EVIDENCE”, “TOOL_RESULT”).
- “**Pointer**” = referência a artefato externo (S3/GCS/DB/VectorStore) que pode ser rehidratado.
- “**Evidence Pack**” = snippets + metadados + citações (com controles de fé).

