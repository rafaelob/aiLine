# 06 — Pipeline de RAG (com “long-context mode” do Opus 4.6)

## 1) Objetivo
Transformar materiais reais em **evidências citáveis** para suportar o plano (objetivos, atividades, avaliação) e reduzir alucinação.

No MVP, RAG também serve para **inclusão**:
- buscar trechos de materiais que podem virar **apoio visual** (resumos, mapas, exemplos),
- localizar termos difíceis para simplificação,
- identificar se há mídia (vídeo/áudio) que exige **legenda/transcrição/descrição**.

---

## 2) Estratégia híbrida: RAG + Long-context

### 2.1) Quando usar Long-context mode
Se o conjunto de materiais (ou um “mapa” deles) cabe no contexto:
- o Planner faz leitura ampla e cria um índice mental (tópicos → evidências)
- excelente para consistência global e “aula com começo-meio-fim”

### 2.2) Quando usar RAG
- muitos documentos,
- necessidade de citações específicas,
- custo/latência.

---

## 3) Index (MVP)
- `pgvector` (ou equivalente) com:
  - chunking por heading/seção,
  - metadados: disciplina, ano, tópico, tipo de mídia, idioma.
- `content_hash` para deduplicação.

---

## 4) Evidências e acessibilidade
### 4.1) Evidência pedagógica
- trechos que justificam objetivo/conteúdo.

### 4.2) Evidência de acessibilidade
- exemplos concretos que viram suporte (ex.: passo a passo, resumo, checklist),
- identificação de requisitos de mídia:
  - vídeo → legenda (e às vezes descrição),
  - áudio → transcrição,
  - imagem/figura → texto alternativo.

---

## 5) Tooling no runtime
- `rag_search(query, k, grade, subject)` → retorna trechos + metadados.
- Planner: usa pouco (só quando precisa).
- Executor: usa para “fechar lacunas” e para gerar variantes acessíveis com evidência.


---

## MVP (hackathon): RAG simplificado com store local
Para permitir um demo funcional sem infraestrutura, o runtime inclui:

- `materials/store.py`: persistência local de materiais (texto)
- `rag_search`: busca simples por tokens (chunking por parágrafo)

Isso é **intencionalmente simples** e deve ser trocado por pgvector/embeddings em produção.
