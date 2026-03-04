# Skills + MCP: integração estado‑da‑arte (com orçamento X/Y)

Este documento cobre:

- **Skills** como pacotes de instruções (e, em alguns stacks, ferramentas/ambiente) com manifesto `SKILL.md`, usando **progressive disclosure**.
- **MCP (Model Context Protocol)** como padrão para conectar ferramentas, recursos e prompts externos.
- Como tudo isso interage com **orçamento X/Y**, caching e segurança.

---

## 1) Skills: “progressive disclosure” com `SKILL.md`

### 1.1 O que é uma skill (na prática)
Uma skill é um pacote com:
- **descrição curta** (para descoberta),
- **instruções completas** (para execução),
- opcionalmente código/arquivos que o agente pode acessar (ex.: via shell),
- e, em stacks que suportam, uma forma padronizada de distribuição e versionamento.

A filosofia correta é:
- o agente **não** carrega todas as skills completas sempre;
- ele mantém um **índice mínimo** e “abre” apenas as skills necessárias.

### 1.2 Estrutura recomendada
- `skills/<skill-name>/SKILL.md`
  - frontmatter: `name`, `description`
  - corpo: “When to use”, “Workflow”, “Outputs”, “Budgets”, “Safety”

### 1.3 OpenAI Skills (comportamento e implicações)
Na plataforma OpenAI, a skill é descrita por um `SKILL.md` com frontmatter e pode ser “anexada” ao ambiente do agente.  
Dois detalhes importantes:

- o modelo pode ler o `SKILL.md` quando a skill é montada,
- e as instruções da skill aparecem com **prioridade equivalente a mensagens do usuário** (não como system).  
  Portanto:
  - mantenha skills curtas e específicas,
  - e evite instruções que conflitem com system/dev.

Referência: OpenAI Platform Docs → *Skills*  
https://platform.openai.com/docs/guides/skills

### 1.4 Progressive disclosure em X/Y
- **skills index** (nome + descrição): entra no **core (X)** ou em um bloco cacheável do prefixo.
- **skill completa** (`SKILL.md`): só entra quando ativada, e deve respeitar um teto (ex.: 10–25k tokens).
- se uma skill for grande, use:
  - **seleção por seções** (carregar apenas headings relevantes),
  - ou uma “skill‑summary” cacheável e um “detail pack” sob demanda.

### 1.5 Segurança e governança
- trate skills como **código**: versionamento, revisão, CI.
- evite incluir segredos em `SKILL.md`.
- se a skill habilita ações perigosas, exija política de **aprovação explícita**.

---

## 2) MCP: como pensar (host/client/server)

### 2.1 Papéis e arquitetura (MCP)
MCP define três papéis:
- **Host**: a aplicação/IDE que coordena o agente.
- **Client**: componente que mantém conexão com um ou mais servidores.
- **Server**: programa que expõe capacidades.

O protocolo é baseado em **JSON‑RPC 2.0** e pode usar diferentes transportes (ex.: STDIO, Streamable HTTP).

Referência: Model Context Protocol → *Architecture*  
https://modelcontextprotocol.io/docs/learn/architecture

### 2.2 Primitivas: tools, resources, prompts
Um servidor pode expor:
- **tools**: ações (executáveis) com schema de entrada.
- **resources**: dados/contexto (ex.: arquivos, páginas, itens).
- **prompts**: templates parametrizados.

Referência: MCP Spec  
https://modelcontextprotocol.io/specification/

---

## 3) MCP e orçamento X/Y

### 3.1 O problema real
Se você conectar um agente a “vários servidores MCP”, você cria:
- catálogos enormes de tools,
- schemas grandes,
- outputs grandes e heterogêneos.

Sem disciplina, isso explode Y e derruba o core.

### 3.2 Soluções práticas

#### A) Catálogo mínimo + schema on‑demand
- Mantenha no prompt apenas:
  - tool name + descrição curta + (talvez) assinatura resumida.
- Carregue schema completo **apenas da tool escolhida**.

#### B) Filtragem de tools na origem
Sempre que possível, filtre tools:
- por allowlist (somente ferramentas relevantes),
- por “capabilities” (modo read‑only vs write),
- por namespace.

#### C) Compressão de resultados: handle + summary
- armazene payload bruto fora do contexto (arquivo/DB),
- inclua no prompt:
  - um resumo estruturado (facts),
  - e um handle.

---

## 4) MCP “nativo” em stacks modernas (OpenAI como exemplo)

Alguns provedores/SDKs permitem conectar MCP servers como **tools remotas** diretamente na camada de tools.

No ecossistema OpenAI:
- você define servidores MCP como tools do tipo `mcp`,
- o runtime lista tools disponíveis (há um item de saída “list tools”),
- você pode **filtrar** tools com `allowed_tools`,
- e definir políticas de **aprovação** (`require_approval`).

Referência: OpenAI Platform Docs → *Connectors and MCP servers*  
https://platform.openai.com/docs/guides/connectors-mcp

> Implicação para X/Y: mesmo que o schema não esteja “no texto”, o catálogo e resultados entram no turno e precisam caber no orçamento. Use allowlists e compressão.

---

## 5) Prompt caching e estabilidade do prefixo (Anthropic e OpenAI)

Caching não aumenta a janela, mas reduz custo/latência e ajuda em loops tool‑heavy.  
Boas práticas universais:
- system/dev/regras/índices estáveis no começo,
- conteúdo variável no final,
- evitar reordenar tools e schemas.

Referências:
- OpenAI → *Prompt caching*: https://platform.openai.com/docs/guides/prompt-caching  
- Anthropic → *Prompt caching*: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching

---

## 6) Checklist rápido (skills + MCP)

- [ ] Skills index <= budget e cacheável
- [ ] Skill completa só entra quando ativada
- [ ] Catálogo MCP filtrado (allowlist)
- [ ] Schema on-demand (não carregar tudo)
- [ ] Tool outputs grandes → handle + summary
- [ ] Aprovação obrigatória para tools perigosas
- [ ] Observabilidade: tamanho do catálogo, tamanho do schema, bytes de payload, tokens inline

---

## Próximo passo

Veja:
- `04_memory_graph.md` (memória)
- `05_orchestration_reference.md` (loop do agente)
