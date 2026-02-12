# 05 — Providers, Model Routing e Adapter Layer (Anthropic-first)

Este documento responde diretamente:
- **“tem API do Claude Code?”** → não como “web API”; Claude Code é um tool/runner.
- **como usar Opus 4.6 no runtime** (Claude API vs Agent SDK).
- **como combinar DeepAgents + Claude Agent SDK** com um adapter limpo.

---

## 1) Esclarecimento: Claude Code ≠ API web

**Claude Code** é um ambiente/CLI para trabalho agentico (com ferramentas e permissões).  
Para uso em um projeto (runtime), você tem 2 opções boas:

1) **Claude API** (Messages API)  
   - você chama `claude-opus-4-6` diretamente.
   - é o caminho “API-first” para backend.

2) **Claude Agent SDK** (Python/TS)  
   - é um SDK que chama o Claude Code “por baixo” e permite:
     - *allowed_tools* / *permission_mode*
     - MCP servers (tools custom)
     - hooks (guardrails/observabilidade)
     - execuções longas e iterativas

> Para o hackathon, o Agent SDK é ótimo porque o runtime fica “agentico de verdade” e você consegue demonstrar tool use com logs.

---

## 2) Como setar Opus 4.6 (incluindo modo 1M e effort)

### 2.1) Identificadores úteis
- Modelo base na API: `claude-opus-4-6`
- Em Claude Code, existe suporte a:
  - **effort levels** (low/medium/high/max)
  - “1M context” via nome/alias com sufixo `[1m]` (beta)

### 2.2) Configuração recomendada no projeto
- `.claude/settings.json` (fonte de verdade versionada)
- Variáveis de ambiente para trocar rapidamente em demo:
  - `CLAUDE_CODE_EFFORT_LEVEL=high` (ou `max` quando quiser “wow”)
  - `AILINE_MODEL=claude-opus-4-6`

---

## 3) Routing (simples, alinhado ao hackathon)

### 3.1) Regra do hackathon
**Opus 4.6 tem que parecer o cérebro principal.**

Então, para o MVP:
- Planner: **Opus 4.6**
- Executor: **Opus 4.6** (ou, se precisar de custo, Sonnet em etapas não-críticas — mas no hackathon eu manteria Opus para evitar discussão)

### 3.2) “OpusPlan” (opcional)
Se você quiser um argumento de “otimização”:
- usar Opus para planejamento + Sonnet para execução mecânica.
- só faça isso se o demo continuar claramente “Opus-first”.

---

## 4) Adapter: DeepAgents ↔ Claude Agent SDK (o que vamos construir)

### 4.1) Por que precisa de adapter?
- DeepAgents (LangChain) consome tools no formato LangChain.
- Agent SDK consome tools via MCP schema.

A integração mais limpa é padronizar ferramentas em 1 lugar e gerar os dois formatos.

### 4.2) Tool Registry canônico (contrato)
Cada tool tem:
- `name`
- `description`
- `args_model` (Pydantic) → gera JSON Schema
- `handler` (async)

### 4.3) Adapter para DeepAgents (LangChain Tools)
- Usa `StructuredTool` / `@tool`
- Valida args com o mesmo `args_model`

### 4.4) Adapter para Agent SDK (SDK MCP Tools)
- Usa `claude_agent_sdk.tool(...)`
- Recebe args como `dict`, valida com Pydantic e retorna `{"content":[...]}`

---

## 5) Exemplo de código (scaffolding)
Veja o diretório `runtime/` para um stub pronto:
- `runtime/ailine_runtime/tools/registry.py`
- `runtime/ailine_runtime/tools/adapters_langchain.py`
- `runtime/ailine_runtime/tools/adapters_agent_sdk.py`
- `runtime/ailine_runtime/planner_deepagents.py`
- `runtime/ailine_runtime/executor_agent_sdk.py`

> Importante: a ideia é você escrever as ferramentas 1 vez e usar nos 2 runtimes.

---

## 6) “O que pode / não pode” (prático)

### Pode
- Usar Claude API direto para certas etapas (ex.: RAG summarization).
- Usar Agent SDK para tool use com MCP e hooks.
- Usar DeepAgents como planner/harness com subagents.

### Não recomendo (no hackathon)
- Transformar Claude Code em “servidor permanente” exposto publicamente (risco operacional).
- Liberar ferramentas perigosas no runtime (Bash/FS real) sem sandbox.
- Misturar 3 provedores diferentes sem necessidade (dilui narrativa do Opus 4.6).

