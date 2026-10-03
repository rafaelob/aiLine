---
name: embedding-lifecycle
description: "Use when re-embedding a live corpus after a model, dimension, preprocessing or prefix change: shadow columns, blue-green backfill, cutover. Not ANN indexes or chunking."
license: Apache-2.0
metadata:
  version: "1.0.2"
---

# Embedding Lifecycle

> Vector search skills tell you how to *query* embeddings. This one is about everything that
> happens to them over time: they were produced by a specific model, at a specific dimension,
> after specific preprocessing — and the day any of those three changes, the column becomes a
> mixture of incompatible spaces that no database will ever complain about.

## Scope

- Changing embedding model, provider, or version on a corpus that already has vectors.
- Changing dimension — including "just truncating" an existing vector.
- Adding or removing a prefix, instruction, or template in the text sent to the embedder.
- Backfilling embeddings into a live table while queries are being served.
- Deciding whether a partially-populated embedding column may be trusted yet.
- Planning the cutover, and deciding what evidence justifies the swap.
- Auditing why retrieval quality silently degraded after an "unrelated" change.

## Do NOT use for

- Choosing which embedding model to adopt, or reading model benchmarks -> model provider docs and
  independent retrieval benchmarks.
- Chunking, splitting, or document-segmentation strategy -> `rag-systems`.
- ANN index mechanics and tuning (HNSW `m`/`ef_construction`/`ef_search`, IVFFlat `lists`/`probes`,
  hybrid RRF, quantization) -> `postgres-extensions-and-vector-search`.
- Retrieval pipeline architecture, rerankers, query routing -> `rag-systems`.
- General schema migration risk and DDL locking -> `postgres-schema-migrations`.
- Deciding whether identity or biometric embeddings may be *persisted at all* — retention, consent,
  erasure obligations, and the cost-versus-privacy trade of recomputing a vector per request instead
  of storing it -> `privacy-data-protection`. This skill governs a vector column that exists; that
  one governs whether it is allowed to exist.

## First principle: the three facts that make a vector meaningful

An embedding is only comparable to another embedding produced by **the same model, at the same
dimension, from the same preprocessing**. Those three facts are properties of the *column*, not of
the pipeline that happened to run last.

Nothing enforces this. A `vector(1536)` column accepts vectors from any model that outputs 1536
dimensions, and the distance operator will happily compute a number for two vectors from different
spaces. The number is meaningless, but it is a *plausible* number — it sorts, it ranks, it fills a
results page. **A mixed-model column is corrupted data with no error message and no exception in
any log.**

So pin all three where they cannot drift:

```yaml
# One authoritative declaration. Config, schema comment, or migration -- pick one and
# make everything else read from it.
embedding:
  model_id: "<exact provider model identifier>"
  dimensions: 1536
  preprocessing: "title + '\n\n' + body, normalized whitespace, no prefix"
  normalized: true         # unit-normalized at write time?
  distance: cosine
```

And enforce it at the boundary: the writer asserts that the vector it is about to store came from
the declared model/dimension/preprocessing, and refuses otherwise. An assertion here costs
microseconds and is the only thing standing between you and a silent corpus-wide corruption.

## Pillar 1 — dimension transitions and shadow columns

### Never write two dimensions into one column

During a transition, run **shadow columns per dimension**:

```sql
ALTER TABLE docs ADD COLUMN emb_3072 vector(3072);   -- new space, unindexed at first
-- existing: emb_1536 vector(1536), indexed, serving traffic
```

The old column keeps serving while the new one fills. Readers explicitly name the column they
trust; the schema makes the mistake unrepresentable rather than merely discouraged. Drop the old
column only after the cutover gate passes (below) — and after a retention window long enough to
roll back without re-embedding everything again.

### Truncation: native versus post-hoc

Lower dimensions cost less to store and search, so the temptation to shorten vectors is constant.
Whether that is legitimate depends on how the model was trained.

**Matryoshka Representation Learning** (Kusupati et al., arXiv:2205.13147, 2022) trains a single
model so that its prefixes are themselves usable embeddings — the abstract states MRL "learns
coarse-to-fine representations that are at least as accurate and rich as independently trained
low-dimensional representations." When a model is trained this way, a shorter vector is a
*supported output*, not a lossy hack.

Current embedding APIs expose this directly (both checked at the vendor's own docs, 2026-07-29):

| Provider | Parameter | Documented note |
|---|---|---|
| OpenAI embeddings (`developers.openai.com/api/docs/guides/embeddings`) | `dimensions` | Using the parameter is "the suggested approach"; if you slice manually instead, "you need to be sure to normalize the dimensions of the embedding". |
| Gemini embeddings (`ai.google.dev/gemini-api/docs/embeddings`) | `output_dimensionality` | Default output 3072. `gemini-embedding-2` "introduces automatic renormalization for non-default dimensions"; with `gemini-embedding-001` "you must manually normalize non-3072 dimensions". |

Two rules follow:

1. **Ask the API for the dimension you want** rather than slicing the returned array. The
   parameter is the supported path and it handles normalization where the model requires it.
2. **If you must slice manually, re-normalize.** Truncating an L2-normalized vector produces a
   vector that is no longer unit length, and cosine/inner-product distances computed against it are
   quietly wrong. This is the single most common truncation bug.

For a model **not** trained with prefix-usable representations, truncation is not a dimension
choice — it is discarding information from an arbitrary basis, and it must be validated by measured
recall or not done. Verify the property against the model's own documentation before assuming it.

> Because truncated output from an MRL-style model is a first-class output, a lower dimension can
> be a deliberate *design* choice — cheaper storage, faster search, smaller index — rather than a
> workaround for a dimension cap. Decide it on measured recall and cost, not on what fits.

## Pillar 2 — re-embedding is a blue-green migration

Re-embedding a populated corpus is not a backfill job. It is a migration of the substrate every
read depends on, running while those reads continue. Treat it with migration discipline:

1. **Stage without an index.** Write new vectors into the staging column with no ANN index —
   maintaining an index during a bulk write is far more expensive than building it once at the end,
   and the half-built index is not usable anyway.
2. **Drain the backlog** with a worker that is idempotent, resumable, and rate-limited to the
   embedding provider's quota. Track per-row state, not a global cursor: a global cursor cannot
   express "row 4,000,201 failed and needs a retry".
3. **Build the index once**, after the drain, with the build-time session settings raised.
4. **Never merge different spaces by `min(distance)`.** Distances compare only
   inside one space (same model, dimension, preprocessing). Rank each spec
   independently, then fuse or route with an evaluated rule (RRF, learned fusion,
   or new-if-present). A document in only one column must still be findable —
   that is coverage, not a shared metric. See `references/model_registry_and_cutover.md`.
5. **Gate the swap** (next section). Never swap on elapsed time or on "the job finished".

The runnable SQL for the index-side — partial indexes per class, the blue-green index
rebuild with its session settings, and the pre-swap gate — is in
`postgres-extensions-and-vector-search`'s `hnsw_scale_operations.md` (sections 3 and 5).
That `UNION ALL` + `min(dist)` pattern is same-spec rebuild only; do not copy it
across EmbeddingSpecs. This skill owns lifecycle; that one owns index mechanics.

## Pillar 3 — preprocessing variants are model variants

Whatever text you hand the embedder defines the space. A contextual prefix, an instruction prefix,
a title concatenation, a template, a normalization step — each one moves every vector. Two corpora
embedded with different prefixes by the same model at the same dimension are **not comparable**,
and the schema cannot tell you so.

This means a prefix change is a re-embedding, with the full blue-green treatment above. It also
means the prefix decision must be made per corpus, on evidence:

> **Gate preprocessing variants per corpus by measured retrieval delta. Never globally.**

Measured on one production system across three corpora with the same model and the same prefix
technique: one corpus **rejected** the prefix (retrieval quality did not improve and the change was
not adopted), while two others gained meaningfully — deltas of roughly **+0.073** and **+0.015** on
an nDCG-class retrieval metric. The same change, the same model, three different verdicts,
determined entirely by corpus structure.

The operating rule that follows:

**No measured gain, no default.** A preprocessing technique that helped a different corpus is a
hypothesis about yours, not a setting to inherit. Measure on a probe set from *this* corpus before
adopting, and record the measured delta next to the config value so the next person can see what
bought it.

## Pillar 4 — backfill state is three-state, never boolean

While a column is filling, "is the embedding column ready?" has three answers, and the middle one
is the dangerous one.

Track population **per class**, not globally — a column that is 90% populated overall can be 0%
populated for an entire document type, and a global number hides exactly that:

```sql
SELECT doc_class,
       count(*)                                  AS total,
       count(emb_3072)                           AS populated,
       count(emb_3072)::float / nullif(count(*), 0) AS fraction
FROM docs
GROUP BY doc_class;
```

Then gate on the fraction with three states — `dead` / `partial` / `usable` — and never with an
"at least one row is populated" test. A gate written as `null_frac < 1.0` flips ON the moment the
backfill writes its first row, at which point the column is used and nearly the whole corpus is
silently excluded from every filtered query.

How `partial` resolves depends on query shape: degrade to a post-filter when a later stage
re-applies the predicate, and refuse when nothing downstream can catch the omission. That
distinction, the status channel that carries it to callers, and the fail-closed consumer rules are
owned by `zero-vs-unknown-semantics` — apply it here rather than re-inventing a local variant.

**Every class must be present before any consumer treats the column as complete.** Absence of a
class is not zero documents of that class; it is an unfinished migration wearing an answer's
clothes.

## Pillar 5 — cutover evaluation

The swap needs evidence, and the evidence must be prepared *before* the migration starts, because
a probe set assembled afterwards is a probe set chosen to pass.

**Fix the probe set first.** A frozen set of queries with known-relevant documents, drawn from real
traffic where possible, covering every document class and both head and tail queries. Freeze it,
version it, and do not touch it during the migration — a probe set edited mid-flight measures the
edit, not the model.

**Measure recall@k against exact search, not against the old index.** Run the same probe queries
with an exact (brute-force) scan in the new space to get ground truth, then measure what the ANN
index returns against it. Comparing new-index results to old-index results conflates two changes —
the embedding space and the index — and cannot tell you which one moved the number.

**Record before and after, on the same probe set:**

| Dimension | Why it gates the swap |
|---|---|
| recall@k vs exact | the retrieval quality question itself |
| per-class recall | a global average hides a class that collapsed |
| p50 / p95 query latency | a quality gain paid for entirely in latency may not be a gain |
| index build time and size | operational cost of the new steady state |
| embedding spend, one-off and ongoing | the re-embed bill plus the new per-document rate |

**The swap gate — all of these, together:**

- [ ] Backlog is zero, and the drain worker **exited successfully** (not "was stopped", not "looks
      finished" — a killed worker leaves an unknown tail).
- [ ] Every document class is present in the new column at the expected count.
- [ ] The index exists and the query plan **names it** — read the plan; do not assume the planner
      chose what you built.
- [ ] recall@k on the frozen probe set meets the pre-agreed bar, per class as well as overall.
- [ ] Latency and cost are within the pre-agreed ceiling.
- [ ] Rollback is one config change away, and the old column still exists.

If any box is unchecked, the correct action is to keep serving the old column. It is working.

## Pillar 6 — retrieval drift: the corpus moves while the model stands still

The cutover gate proves the space was good on the day it was measured. Nothing keeps proving it. The
model is frozen by design — that is what pinning it means — but the corpus is not: new document
classes arrive, vocabulary shifts, the query mix follows the product. Quality decays against a fixed
embedder without any event causing it, so nothing fires.

### Norm checks are an integrity probe, not a quality metric

Vector-norm monitoring is worth having: it catches an empty input that embedded to near-zero, a
truncated batch, a preprocessing step that stopped running. But note what it can say. **On a
unit-normalized column a healthy norm is a constant** — so the check is definitionally a write-path
integrity check. It finds malformed vectors, never wrong ones. A vector can be unit length, in the
right space, and retrieve the wrong documents, and every norm-based check passes. Do not report norm
outliers as drift detection; they answer a different question.

### Re-run the frozen probe set on a schedule

The Pillar 5 protocol is already the drift monitor; what is missing is a cadence and retention. Run
the frozen probe set against production periodically, persist recall@k overall **and per class** with
a timestamp, and alert on a drop against the *trailing baseline* rather than an absolute floor. A
floor is set either so low it never fires or so high it fires forever; the informative signal is
"this corpus, worse than last month".

### A stale probe set reports "no drift" — that is the trap

A probe set frozen at cutover describes the corpus as it was then. Documents added since appear in no
probe's relevant set, so a query that *should* now return a new document is still scored against the
old answer. The metric holds steady precisely because it stopped asking about anything new. Two
lifecycle rules, which look contradictory and are not:

- **Frozen within a comparison** — never edited while a before/after measurement runs.
- **Extended between comparisons**, deliberately and versioned, whenever a new document class or query
  intent enters the corpus.

Extending resets the baseline. **Store the probe-set version and the `k` next to every recorded
measurement, and compare only within both**: a series that silently changes its denominator — a new
probe set, or a `recall@10` row landing next to `recall@5` ones — is worse than no series, because it
is trusted. Track probe-set *coverage* too — zero probes touching the newest
class is the drift you will not otherwise see.

## Common pitfalls

- **Changing the model without changing the column.** No error, no exception, plausible results,
  corrupted corpus. The most expensive failure in this skill and the least visible.
- **Slicing an embedding without re-normalizing.** Distances silently wrong for every truncated
  vector; results still look ranked.
- **Truncating a model not trained for it**, on the assumption that "leading dimensions matter
  most". Validate on recall or do not do it.
- **Maintaining the ANN index during a bulk backfill.** Far slower than a single build at the end,
  and the partial index is not usable meanwhile.
- **A global backfill cursor.** Cannot express a failed row, so failures become permanent holes
  that no re-run repairs.
- **Global population gates.** 90% overall can be 0% for one class.
- **Inheriting a preprocessing prefix because it helped elsewhere.** Measured here: same model,
  same prefix, three corpora, three different verdicts including one rejection.
- **Assembling the probe set after the migration.** It will pass. That is why it was assembled then.
- **Benchmarking the new index against the old index.** Conflates the space change with the index
  change; use exact search as ground truth.
- **Dropping the old column at swap time.** Rollback then costs a full re-embed. Keep it for a
  retention window.
- **Leaving the model id undocumented in the schema.** Six months later nobody can say what is in
  the column, and the only way to find out is to re-embed a sample and compare.
- **Calling a norm-outlier check "drift detection".** On a unit-normalized column the healthy value is
  a constant; the check finds malformed vectors, not worse ones.
- **Never extending the probe set after cutover.** It goes on reporting stability about a corpus that
  no longer exists, which is indistinguishable from health.
- **Extending the probe set without versioning the measurement.** The recall series changes its
  denominator mid-flight and the step looks like a regression, or hides one.
- **Charting `recall@5` and `recall@10` as one series.** Recall only rises with `k`, so the step is
  the reporting choice, not the corpus. Filter the baseline query by `k` too, not only by version.

## Validation checklist

- [ ] Model id, dimension, preprocessing, normalization, and distance metric are declared in one
      authoritative place, and writers assert against it.
- [ ] Dimension transitions use shadow columns; no column ever holds two spaces.
- [ ] Any truncation uses the provider's dimension parameter, or re-normalizes explicitly.
- [ ] The backfill worker is idempotent, resumable, rate-limited, and tracks per-row state.
- [ ] The ANN index is built once, after the drain.
- [ ] Population is tracked per class and gated three-state, never with an "at least one" test.
- [ ] Preprocessing variants were measured on this corpus, and the measured delta is recorded next
      to the config value.
- [ ] The probe set was frozen before the migration began.
- [ ] recall@k was measured against exact search, per class, before and after.
- [ ] The swap gate passed every box, including "the drain exited successfully" and "the plan names
      the index".
- [ ] Rollback is a config change, and the old column survives a retention window.
- [ ] After cutover, the frozen probe set runs on a cadence, and recall is alerted against the
      trailing baseline — not against an absolute floor, and not on vector norms.
- [ ] Every stored recall measurement carries its probe-set version and its `k`, and no chart or
      baseline query mixes two of either.
- [ ] Probe-set coverage of the newest document classes is checked, not assumed.

## Reference files

- `references/model_registry_and_cutover.md` — read this when setting up the pinned model
  declaration and the write-time assertion, when preparing the probe set and running the
  before/after cutover measurement, or when wiring the post-cutover drift monitor: the registry
  shape, the per-row backfill state machine, the evaluation protocol, and the versioned
  recall-history table with its trailing-baseline and probe-coverage queries, in executable form.
