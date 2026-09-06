# AiLine

Plataforma educacional inclusiva com API FastAPI/SSE, agentes e frontend Next.js.

## Mapa e fontes locais

- `runtime/` contém núcleo, adaptadores e API; `agents/` contém fluxos; `frontend/` é a aplicação; `docs/` e `control_docs/` registram produto e operação.
- `docker-compose.yml` sobe API, frontend, PostgreSQL e Redis. `README.md` orienta a execução e `control_docs/SYSTEM_DESIGN.md` define os limites arquiteturais.
- `fleet.toml` é a autoridade da CI local. A certificação de entrega executa a suíte declarada nele no SHA completo e exato, em worktree isolada sob a trava global de suíte da máquina; GitHub é espelho opcional, não juiz. Teste no worktree compartilhado não a substitui.

## Comandos locais

```powershell
docker compose up -d --build
cd runtime; uv run pytest -v --cov
cd agents; uv run pytest -v
cd frontend; pnpm test
cd frontend; pnpm exec playwright test
```

Execute a verificação determinística mais próxima antes de ampliar. Testes `live_llm` requerem chaves reais e só entram quando a integração de provedor fizer parte do escopo.

## Invariantes e coordenação

- `runtime/ailine_runtime/domain/` não importa frameworks; integrações entram por portas e adaptadores.
- Preserve isolamento por locatário e eventos terminais em API, SSE, armazenamento vetorial e agentes. Configure segredos por `.env` a partir de `.env.example`, nunca em código, artefatos ou documentação.
- Antes de superfícies Fleet compartilhadas, leia `control_docs/AGENT_PROTOCOL.md`. `sprints/` é o registro versionado (layout 2); `fleet_runtime/` é estado operacional e não é limpeza rotineira.
- `sprints/` é o registro versionado de entrega; `fleet_runtime/` é estado operacional persistente, nunca limpo por rotina; `fleet_tmp/` é a única raiz transitória de limpeza.

Tracker: github — rafaelob/aiLine; Issue = autoridade editável (DEC-113); commits citam #N; TODO/sprints são histórico.
