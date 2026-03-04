# Checklists de produção (contexto, tools, MCP, memória)

Use estas listas como “gate” antes de colocar um agente em produção.

---

## A) Contexto e budgets (X/Y)

- [ ] X e Y definidos a partir da janela do modelo e do pior caso de tools
- [ ] Reserva de output definida (não use Y = janela inteira)
- [ ] Rolling summary com schema fixo e teto de tokens
- [ ] Âncoras definidas (N turns recentes)
- [ ] “Core gate” garante `core_tokens <= X`
- [ ] “Total gate” garante `total_tokens <= Y`
- [ ] Payloads grandes viram artefatos (handle + excerpt)

---

## B) Tools / RAG

- [ ] Catálogo mínimo (nome + descrição)
- [ ] Schema on‑demand (apenas para tools escolhidas)
- [ ] Tool output compressor (handle + summary)
- [ ] EvidencePack padronizado (quotes curtas + URLs + datas)
- [ ] Cada tool tem budget específico (tokens/bytes)
- [ ] Logs de tool calls e outputs (para auditoria)

---

## C) MCP

- [ ] Servidores MCP versionados e documentados
- [ ] Transporte definido (stdio vs streamable HTTP)
- [ ] Autenticação segura (tokens via env, OAuth quando aplicável)
- [ ] Allowlist de tools (reduz superfície e contexto)
- [ ] Política de aprovação para tools write‑capable
- [ ] Timeouts e retries configurados
- [ ] Namespacing claro (ex.: `github__`, `db__`)

---

## D) Skills

- [ ] Todas skills têm `SKILL.md` com frontmatter (name/description)
- [ ] Índice de skills cabe no budget e é cacheável
- [ ] Skills completas só entram quando ativadas
- [ ] Skills perigosas exigem aprovação e logs
- [ ] Não há segredos em arquivos de skill

---

## E) Memória e personalização

- [ ] Política de escrita (o que entra, o que não entra)
- [ ] Confirmação do usuário antes de writes duráveis
- [ ] Proveniência em todos os itens
- [ ] TTL/retention definido
- [ ] Mecanismo de remoção/correção
- [ ] Recuperação sob demanda e compacta (tool budget)
- [ ] Sem PII/segredos por padrão

---

## F) Segurança

- [ ] Redação de segredos em logs e artefatos
- [ ] Aprovação para ações irreversíveis (deploy, delete, pagamentos)
- [ ] Princípio do menor privilégio (read‑only tools quando possível)
- [ ] Isolamento de execução (sandbox) quando aplicável

---

## G) Observabilidade e qualidade

- [ ] Token ledger por turno
- [ ] Traços/spans para LLM e tool calls
- [ ] Alertas de “context overflow”
- [ ] Avaliações de regressão (sessões longas + tool heavy)
- [ ] Benchmarks de custo/latência por tarefa

---

## H) Operação

- [ ] Rotação de credenciais
- [ ] Limites de rate/custo por usuário
- [ ] Feature flags para tool sets e skills
- [ ] Playbook de incidentes (tool misfire, vazamento, drift)
