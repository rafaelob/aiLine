# Code (scaffold)

Este diretório contém um scaffold minimalista para você integrar em qualquer loop/orquestrador.

## Arquivos
- `context_manager.py` — BudgetManager, ContextAssembler, ContextLedger, tool result compaction (stub), handoff helper.
- `examples/` — scripts demonstrando uso.

## O que falta (por design)
- Token counting real: conecte `estimate_tokens()` a tokenizer/vendedor.
  - OpenAI tem endpoint de contagem de tokens (`/v1/responses/input_tokens`) na documentação oficial.
- Summarizer real: substitua `fake_summarizer` por chamada LLM com prompt estruturado.
- Blob store real: substitua `BlobStore` por S3/GCS/DB.

## Integração típica
1. carregar profile (`configs/budget_profiles.yaml`)
   - para sessão contínua, use `utilization_target_ratio` (watermark) + perfis steady/burst
2. construir slices (system/dev, state_json, recency, summaries, evidence pack, tool results)
3. `assembler.select(slices)`
4. serializar para o formato do vendor
5. logar ledger e traces

