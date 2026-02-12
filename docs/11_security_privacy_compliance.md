# 11 — Segurança, Privacidade e Compliance (com foco em dados de acessibilidade)

> Regra prática: **o agente pode fazer tudo que as tools permitem**.
> Então segurança = **limitar ferramentas e dados**, não “pedir pro modelo se comportar”.

---

## 1) Princípios
- **Minimizar ferramentas**: só o necessário para o MVP (whitelist).
- **Minimizar dados**: guardar só o essencial; evitar texto livre.
- **Auditar tudo**: run_events com tool calls e resultados (sanitizados).
- **Separar dados sensíveis**: perfis de acessibilidade podem expor vulnerabilidades.

---

## 2) Dados sensíveis: perfis e preferências de acessibilidade
`class_accessibility_profile` e `learner_profiles`:
- podem implicar TEA/TDAH/dificuldades/deficiências,
- portanto são **dados sensíveis** (no Brasil, atenção extra pela LGPD; em escola, contexto é delicado).

Regras MVP (para o hackathon):
- perfis por **label anônima**, sem nome real;
- evitar campos livres longos (sem história clínica, sem laudo);
- armazenar separado de logs de execução (ou com redaction forte);
- export **nunca** inclui detalhes do perfil por default (somente adaptações e requisitos gerais);
- retenção curta (ex.: 7–30 dias) no store local.

Regras pós-hackathon (produto):
- consentimento e finalidade clara para armazenar perfis,
- RBAC (professor, coordenação, AEE),
- criptografia em repouso e em trânsito,
- auditoria de acesso.

---

## 3) Segurança no Claude Agent SDK (Executor)

### 3.1) Allowed tools (whitelist)
- Libere somente tools do domínio AiLine:
  - `mcp__ailine__rag_search`
  - `mcp__ailine__curriculum_lookup`
  - `mcp__ailine__accessibility_checklist`
  - `mcp__ailine__export_variant`
  - `mcp__ailine__save_plan`

> Nada de ferramentas de execução arbitrária, shell, rede, etc.

### 3.2) permission_mode
- Em demo/CI: `bypassPermissions` **somente** com whitelist estrita.
- Em produção: modos mais restritos + consentimento para ações sensíveis.

### 3.3) Hooks/guardrails (quando virar produto)
- bloquear qualquer tool fora da whitelist,
- redigir/anonimizar logs (principalmente `notes`),
- políticas de size-limit (evitar exfiltração via output grande),
- validação de schema antes de salvar.

---

## 4) Segurança no Planner (DeepAgents)
- Planner não deve ter tools de escrita/persistência.
- Ideal: Planner usa só leitura (RAG/lookup) e devolve JSON estruturado.
- Evitar incluir dados sensíveis no prompt (minimizar contexto).

---

## 5) Compliance (nota: não é parecer jurídico)
Referências úteis:
- **WCAG/eMAG**: acessibilidade digital (produto e exports)
- **LGPD (BR)**: princípios de minimização, finalidade, necessidade e controle de acesso
- **FERPA (US)**: princípios de privacidade educacional (se aplicável)

Boas práticas que ajudam no hackathon (mesmo sem jurídico):
- reduzir PII (não coletar nome do aluno),
- logs sanitizados,
- deixar explícito que o sistema **não diagnostica** e não substitui AEE/IEP.

---

## 6) Fronteiras de responsabilidade (importante para TEA/TDAH)
AiLine:
- sugere adaptações pedagógicas e formatos acessíveis,
- marca quando precisa de revisão humana (Libras/Braille-ready/adequações formais),
- mantém professor no controle.

AiLine **não**:
- emite diagnóstico,
- recomenda intervenção clínica,
- substitui equipe pedagógica/AEE.


---

## Extensão: Tutoria (Tutor Agents) — segurança e privacidade
Dados adicionais:
- `tutor_agents` (perfil funcional do aluno, persona)
- `tutor_sessions` (histórico de conversa)
- `materials` (conteúdo do professor)

Regras recomendadas:
- Autenticação e autorização por `teacher_id`/escola (multi-tenant).
- `rag_search` deve **sempre** ser escopado por tenant (no MVP exigimos `teacher_id`).
- Minimizar PII (usar apelidos e perfis funcionais).
- Retenção curta e opção de deleção/export.
- Redação/mascara de dados antes de logs.
