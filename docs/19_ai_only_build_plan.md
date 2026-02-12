# 19 — Plano “AI-only build” (como usar Claude Code + DeepAgents sem quebrar o runtime)

> Você já vai usar Claude Code como dev. Aqui é só um plano de disciplina para acelerar.

## 1) Rotina recomendada
- Use Claude Code para:
  - scaffolding
  - refactors
  - testes
  - docs
- Use DeepAgents CLI para:
  - tarefas longas no repo
  - manter memória de convenções do projeto

## 2) Separar dev tool de runtime
- Claude Code / DeepAgents CLI = ferramentas de dev
- Runtime = serviço (API) chamando:
  - DeepAgents SDK (Planner)
  - Claude Agent SDK (Executor)

## 3) Evitar “misturar”
Não faça o backend depender de:
- permissões interativas
- filesystem do dev
- comandos shell não-sandboxed

O backend deve rodar em container com tools restritas.

