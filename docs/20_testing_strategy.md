# 20 — Estratégia de Testes (inclui acessibilidade)

## 1) Objetivo
Garantir que o demo não quebra e que o pipeline é previsível **e acessível**.

---

## 2) Tipos de teste

### 2.1) Testes determinísticos (sem LLM)
- Validador (Quality Gate): regras objetivo↔atividade↔avaliação + checklist acessibilidade
- Serialização/Schema (Pydantic)
- Tool Registry adapters (LangChain + MCP)

### 2.2) Testes com LLM (golden tests)
- 3–5 prompts fixos (com perfis diferentes)
- comparar apenas propriedades estáveis:
  - schema válido
  - percent de objetivos cobertos
  - sem campos vazios críticos
  - accessibility_pack presente

### 2.3) Teste de integração (smoke)
- `POST /plans/generate` → run_id
- stream eventos
- run termina em `done`
- plano persistido + variantes exportáveis

### 2.4) Testes de acessibilidade da UI (ideal)
- `axe-core`/`pa11y` no CI (mesmo que básico no MVP)
- checklist manual rápido:
  - teclado
  - foco visível
  - contraste
  - sem dependência de cor

---

## 3) “Fail fast” no demo
- se o validador reprovar 3x → retornar erro amigável
- evitar loops infinitos
- sempre retornar relatório do porquê falhou (para parecer produto)
