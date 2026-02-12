# 07 — Alinhamento Curricular (US + BR)

## 1) Objetivo
Garantir que o plano não seja “genérico”: ele precisa estar alinhado a objetivos reais de currículo.

---

## 2) Abordagem no MVP
### 2.1) Currículo como ferramenta (Tool)
Criamos uma tool:
- `curriculum_lookup(standard, grade, topic)`  
Retorna:
- objetivos (IDs + descrição),
- habilidades prévias,
- exemplos de avaliação.

No Brasil:
- BNCC por área/ano + habilidades (códigos).

Nos EUA:
- pode começar com uma tabela mínima (Common Core/NGSS) e expandir.

### 2.2) Agente especializado (subagent)
No Planner:
- subagent `curriculum_agent` faz mapeamento:
  - tópicos dos materiais → objetivos do currículo
  - checa “gap” (o que faltou no material)

---

## 3) Validação
O Quality Gate deve checar:
- plano menciona quais objetivos cobre (IDs/códigos)
- atividade e avaliação existem para cada objetivo

---

## 4) Saídas (artefatos)
- `alignment_map`: objetivos → etapas do plano
- `coverage_report`: o que ficou de fora (para o professor decidir)

