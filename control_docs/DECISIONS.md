# DECISIONS — Registro de decisões de NEGÓCIO da frota

> Append-only. Direção de produto, escopo, prioridade, trade-off comercial.
> NÃO substitui os ADRs técnicos do SYSTEM_DESIGN.md. Escreva SÓ via
> `mural.py decision-add` ou pelo painel (autor USER) — nunca à mão.
>
> QUALQUER agente decide, registra e SEGUE trabalhando: ninguém fica bloqueado
> esperando ratificação. A entrada do agente nasce `decided-by-agent` (vale já,
> e ainda deve a revisão do dono); o USER ou o coordenador promove a `accepted`
> com `mural.py decision-set-status`.
>
> EXEMPLO da forma completa — fica DENTRO deste bloco de citação de propósito,
> para não ser lido como decisão de verdade (as entradas reais começam na margem):
>
> `## DEC-NNN — título curto (AAAA-MM-DD, autor: X)`
> `- **Status:** decided-by-agent | accepted | superseded por DEC-NNN | void`
> `- **Contestação:** quem contestou, a objeção, e o que sobreviveu`
>   — ou `sem par — nenhum outro agente ativo na frota`
> `- **Supersede:** DEC-NNN` (só ao retificar)
> `- **Trabalho afetado:** o que foi construído sobre a revogada` (só ao retificar)
> `- **Contexto:** por que a decisão apareceu`
> `- **Decisão:** o que passa a valer`
> `- **Consequências:** o que muda na prática` (opcional)
> `- **Links:** sprint/post/ID` (opcional)
>
> O rótulo `autor:` é OPCIONAL: `(AAAA-MM-DD, operador)` também é lido. Só o
> `Status:` declara vigência — sem ele ninguém pode afirmar que a decisão vale.
> `Contestação` é SEMPRE escrita: um campo em branco é indistinguível de
> "ninguém contestou", e "não havia com quem debater" é outra coisa — mais
> frágil, e portanto merecedora de MAIS atenção do dono, não menos.
