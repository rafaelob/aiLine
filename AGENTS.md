# AiLine

## Propósito e mapa

- Plataforma educacional inclusiva: transforma materiais de aula em planos
  adaptativos e expõe uma API FastAPI com streaming SSE.
- `runtime/` contém o núcleo, adaptadores e API; `agents/` contém os agentes e
  fluxos; `frontend/` é a aplicação Next.js; `docs/` contém o material de
  produto e `control_docs/` registra arquitetura, testes, segurança e operação.
- `docker-compose.yml` executa API, frontend, PostgreSQL e Redis. Use
  `README.md` como guia de execução e `control_docs/SYSTEM_DESIGN.md` para os
  limites arquiteturais.

## Coordenação

- O protocolo para superfícies compartilhadas está em
  `control_docs/AGENT_PROTOCOL.md`. O registro versionado de entregas é
  `sprints/` (layout 2); `fleet_runtime/` é estado operacional e não é limpeza
  rotineira.

## Comandos verificados

```powershell
docker compose up -d --build
cd runtime; uv run pytest -v --cov
cd agents; uv run pytest -v
cd frontend; pnpm test
cd frontend; pnpm exec playwright test
```

## Limites locais

- O domínio em `runtime/ailine_runtime/domain/` não deve importar frameworks;
  integrações entram por portas e adaptadores.
- Preserve isolamento por locatário e as garantias de eventos terminais ao
  alterar API, SSE, armazenamento vetorial ou agentes.
- Testes `live_llm` exigem chaves reais e são separados dos testes locais;
  execute-os apenas quando o escopo exigir a integração de provedor.
- Configure chaves em `.env` a partir de `.env.example`, sem expor valores em
  código, artefatos ou documentação.
