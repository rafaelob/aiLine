# Contribuindo para o AiLine

Obrigado por querer contribuir.

## Princípios do projeto
- **Inclusão primeiro:** TEA, TDAH, dificuldades de aprendizagem, deficiência auditiva e visual são requisitos.
- **Amplificar o professor:** o humano decide; o agente executa e valida.
- **Segurança por default:** tool whitelist e dados mínimos.

## Como rodar
Veja `README.md` e `docs/10_api_and_frontend.md`.

## Como propor mudanças
- Abra uma issue/PR com:
  - contexto
  - decisão de design
  - impacto em acessibilidade
  - testes (quando aplicável)

## Estilo de código
- Python 3.11+
- Pydantic v2
- Prefira funções pequenas e modelos explícitos

## Testes
```bash
cd runtime
pytest -q
```
