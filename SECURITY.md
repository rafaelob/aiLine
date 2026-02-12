# Security (AiLine)

## Reporting a vulnerability
Para o hackathon, reporte issues sensíveis diretamente aos mantenedores (não em issues públicas).

## Threat model (MVP)
- **Risco:** prompt injection via materiais (RAG)
- **Mitigações no MVP:**
  - tools com whitelist
  - `rag_search` exige `teacher_id` (escopo)
  - relatório determinístico (Quality Gate) fora do modelo

## Produção (roadmap)
- Auth + multi-tenant
- Sanitização e isolamento de documentos
- Embeddings com filtros por tenant
- Logging com redaction
