# Template — Evidence Pack (RAG)

```yaml
evidence_pack:
  query: "..."
  retrieved_at: "..."
  policy:
    max_total_tokens: 20000
    max_tokens_per_source: 4000
    diversity: true
  items:
    - id: E1
      source:
        title: "..."
        publisher: "..."
        url: "https://..."
        date_published: "date not found"
        date_updated: "date not found"
        access_scope: "tenant:..."
      excerpt: |
        "..."
      span: "L100-L130"
      relevance: 0.93
      hash: "sha256:..."
```
