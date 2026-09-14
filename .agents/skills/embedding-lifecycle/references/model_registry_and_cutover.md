# Model registry, backfill state, and the cutover protocol

Executable shapes for the three things that have to exist before a re-embedding starts: an
authoritative declaration of what is in the column, a per-row backfill state machine, and a frozen
evaluation protocol. Python/SQL are illustrative; the discipline is the point.

---

## 1. The registry: one authoritative declaration

The failure this prevents is not "we used the wrong model". It is "nobody can say what is in the
column", which is unrecoverable without re-embedding a sample to find out.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingSpec:
    """The three facts that make two vectors comparable, plus how they are stored.

    Frozen on purpose: a spec that can be mutated at runtime is a spec that will be,
    and the mutation will not be in the diff."""
    key: str              # stable name, e.g. "docs.v2"
    model_id: str         # exact provider identifier, never a friendly alias
    dimensions: int
    preprocessing: str    # the EXACT transform, precise enough to reproduce
    normalized: bool      # unit-normalized at write time?
    distance: str         # cosine | l2 | inner_product
    column: str           # which column holds vectors of this spec


SPECS = {
    "docs.v1": EmbeddingSpec(
        key="docs.v1",
        model_id="<provider model id as documented>",
        dimensions=1536,
        preprocessing="title + '\\n\\n' + body; collapse whitespace; no prefix",
        normalized=True,
        distance="cosine",
        column="emb_1536",
    ),
    "docs.v2": EmbeddingSpec(
        key="docs.v2",
        model_id="<new provider model id>",
        dimensions=3072,
        preprocessing="title + '\\n\\n' + body; collapse whitespace; no prefix",
        normalized=True,
        distance="cosine",
        column="emb_3072",
    ),
}
```

`preprocessing` is prose, and it must be precise enough that a second person reproduces it
byte-for-byte. "Cleaned text" is not a spec. If the transform is non-trivial, name the function and
pin its module — the string is documentation, the function is the truth, and they must not drift.

### Write-time assertion

The only mechanical defence against a mixed-space column. It costs microseconds.

```python
def store(row_id: str, vector: list[float], spec: EmbeddingSpec, produced_by: str) -> None:
    if produced_by != spec.model_id:
        raise ValueError(
            f"spec {spec.key} expects {spec.model_id}, got {produced_by} -- "
            "storing this would silently corrupt the column"
        )
    if len(vector) != spec.dimensions:
        raise ValueError(f"spec {spec.key} expects {spec.dimensions} dims, got {len(vector)}")
    if spec.normalized and abs(_l2(vector) - 1.0) > 1e-3:
        raise ValueError(
            "vector is not unit length -- was it truncated without re-normalizing?"
        )
    _write(spec.column, row_id, vector)
```

The third check is the one that catches manual truncation. Slicing an L2-normalized vector produces
a shorter vector that is no longer unit length, and every cosine/inner-product distance computed
against it is quietly wrong while still looking like a distance.

### Schema-side pin

Put the spec key where it survives the codebase:

```sql
COMMENT ON COLUMN docs.emb_3072 IS
  'EmbeddingSpec docs.v2 -- see SPECS registry. Do not write vectors from any other spec.';
```

---

## 2. Per-row backfill state

A global cursor cannot express "row 4,000,201 failed". Per-row state can, and that is the entire
difference between a resumable migration and a migration with permanent holes.

```sql
ALTER TABLE docs ADD COLUMN emb_v2_state text
  NOT NULL DEFAULT 'pending'
  CHECK (emb_v2_state IN ('pending', 'in_flight', 'done', 'failed', 'skipped'));
ALTER TABLE docs ADD COLUMN emb_v2_attempts int NOT NULL DEFAULT 0;
ALTER TABLE docs ADD COLUMN emb_v2_error text;

CREATE INDEX ON docs (emb_v2_state) WHERE emb_v2_state <> 'done';
```

| State | Meaning | Retry? |
|---|---|---|
| `pending` | never attempted | n/a — this is the queue |
| `in_flight` | claimed by a worker | only after a lease timeout |
| `done` | vector written and asserted | no |
| `failed` | attempted, error recorded | yes, bounded by `attempts` |
| `skipped` | deliberately excluded, reason recorded | no |

`skipped` is not decoration. Without it, deliberately-excluded rows sit in `pending` forever and the
backlog never reaches zero — so the swap gate can never pass honestly, and somebody eventually
passes it dishonestly.

Claim work with a lease so a crashed worker does not strand rows:

```sql
UPDATE docs SET emb_v2_state = 'in_flight', emb_v2_claimed_at = now()
WHERE id IN (
  SELECT id FROM docs
  WHERE emb_v2_state = 'pending'
     OR (emb_v2_state = 'in_flight' AND emb_v2_claimed_at < now() - interval '15 minutes')
     OR (emb_v2_state = 'failed'    AND emb_v2_attempts < 5)
  ORDER BY id
  LIMIT 500
  FOR UPDATE SKIP LOCKED
)
RETURNING id, title, body;
```

`FOR UPDATE SKIP LOCKED` is what lets several workers drain the same queue without coordinating.

### Backlog and population, per class

```sql
-- Backlog: must be zero before the swap gate can pass.
SELECT emb_v2_state, count(*) FROM docs GROUP BY 1;

-- Population per class: the number that actually gates readers.
SELECT doc_class,
       count(*)                                     AS total,
       count(emb_3072)                              AS populated,
       round(count(emb_3072)::numeric
             / nullif(count(*), 0), 4)              AS fraction
FROM docs
GROUP BY doc_class
ORDER BY fraction ASC;      -- worst class first: that is the one that gates you
```

Order ascending on purpose. The global average is reassuring and useless; the worst class is the
one that decides whether the column can be trusted.

---

## 3. The evaluation protocol

### Freeze the probe set first

```python
@dataclass(frozen=True)
class Probe:
    query: str
    relevant_ids: frozenset[str]   # known-relevant docs
    doc_class: str                 # so per-class recall is computable
```

Rules that make the measurement mean something:

- Assemble it **before** the migration starts. A probe set built afterwards is a probe set selected,
  consciously or not, to pass.
- Version it and store it with the code. Never edit during a migration — an edited probe set
  measures the edit.
- Cover **every document class**, and both head and tail queries. Head-only probe sets miss exactly
  the degradation that matters, because tail queries are where a weaker space shows first.
- Draw from real traffic where possible. Hand-written probes encode what you expected users to ask.

### Ground truth is exact search, not the old index

```python
def recall_at_k(spec: EmbeddingSpec, probes: list[Probe], k: int) -> dict:
    """recall@k of the ANN index against a brute-force scan in the SAME space.

    Comparing the new index against the OLD index conflates two changes -- the
    embedding space and the index -- and cannot attribute the difference to either."""
    per_class: dict[str, list[float]] = {}
    for p in probes:
        truth = exact_top_k(spec, p.query, k)     # brute force, no index
        got = ann_top_k(spec, p.query, k)         # what production would return
        hit = len(set(truth) & set(got)) / k
        per_class.setdefault(p.doc_class, []).append(hit)
    return {
        "overall": _mean([v for vs in per_class.values() for v in vs]),
        "per_class": {c: _mean(vs) for c, vs in per_class.items()},
        "worst_class": min(per_class, key=lambda c: _mean(per_class[c])),
    }
```

Report `per_class` and `worst_class` alongside `overall`, always. A global recall of 0.94 that hides
one class at 0.31 is a passing number in front of a broken migration.

### Record the full comparison

Run on the same frozen probe set, before and after:

| Metric | Old | New | Gate |
|---|---|---|---|
| recall@k overall | | | >= agreed bar |
| recall@k worst class | | | >= agreed bar |
| p50 latency | | | <= ceiling |
| p95 latency | | | <= ceiling |
| index build time | | | operational note |
| index size | | | operational note |
| one-off re-embed spend | | | budget |
| ongoing per-document rate | | | budget |

Agree the bars **before** running the measurement. Bars chosen after seeing the numbers are not
bars. Fix `k` before running it as well, and write it into the row labels: the Old and New columns
must be the same `k`, and a bar quoted as "recall >= 0.9" without its `k` is not a bar either.

### Preprocessing variants use the same protocol

A prefix or template change is evaluated exactly like a model change, on this corpus, with this
probe set. Measured on one production system: the same model and the same prefix technique across
three corpora produced three different verdicts — one corpus rejected it outright, two gained about
**+0.073** and **+0.015** on an nDCG-class metric.

Record the delta next to the config value:

```yaml
preprocessing:
  prefix: "<the prefix, verbatim>"
  measured_delta: +0.073        # nDCG-class, frozen probe set v3
  measured_on: 2026-07-29
  corpus: docs
  # No measured gain, no default. A prefix that helped another corpus is a
  # hypothesis about this one.
```

Without the recorded delta, the next person cannot tell a measured decision from a copied one, and
will copy it onward.

---

## 4. The swap gate, as a script

```python
def may_swap(report) -> tuple[bool, list[str]]:
    blockers = []
    if report.backlog != 0:
        blockers.append(f"backlog is {report.backlog}, must be 0")
    if not report.drain_exited_cleanly:
        blockers.append("drain worker did not exit successfully -- unknown tail")
    for cls, n in report.missing_classes.items():
        blockers.append(f"class {cls} missing {n} rows in the new column")
    if not report.plan_names_index:
        blockers.append("query plan does not name the new index -- read the plan, do not assume")
    if report.recall_overall < report.bar_overall:
        blockers.append(f"recall@k {report.recall_overall} < bar {report.bar_overall}")
    if report.recall_worst_class < report.bar_per_class:
        blockers.append(
            f"worst class {report.worst_class} at {report.recall_worst_class} "
            f"< bar {report.bar_per_class}"
        )
    if report.p95_latency > report.latency_ceiling:
        blockers.append(f"p95 {report.p95_latency} > ceiling {report.latency_ceiling}")
    if not report.old_column_retained:
        blockers.append("old column dropped -- rollback would require a full re-embed")
    return (not blockers), blockers
```

Two conditions deserve their emphasis:

- **`drain_exited_cleanly`** — "the backlog is zero" and "the worker finished" are different facts.
  A worker killed at 99.99% leaves a tail nobody enumerated, and the backlog query run against a
  stalled queue reports zero pending only because nothing is claiming.
- **`plan_names_index`** — the planner is not obliged to use the index you built. Read the plan.
  Assuming it did is how a "successful" migration ships a sequential scan.

If the gate returns blockers, keep serving the old column. It is working, and it will keep working
while you fix the blocker.

---

## 5. After the swap: the scheduled drift monitor

The same probe set and the same `recall_at_k` become the standing monitor. What changes is that the
result is *stored*, so a later run has something to be worse than.

```sql
CREATE TABLE retrieval_quality_runs (
  id             bigserial PRIMARY KEY,
  measured_at    timestamptz NOT NULL DEFAULT now(),
  spec_key       text NOT NULL,          -- which EmbeddingSpec was live
  probe_set_ver  text NOT NULL,          -- NOT nullable: see below
  k              int  NOT NULL,
  recall_overall numeric(6,4) NOT NULL,
  recall_by_class jsonb NOT NULL,        -- {"contract": 0.91, "invoice": 0.34}
  corpus_rows    bigint NOT NULL         -- context for a moved number
);

CREATE INDEX ON retrieval_quality_runs (spec_key, probe_set_ver, k, measured_at DESC);
```

`probe_set_ver` and `k` are both `NOT NULL` and both sit in the index ahead of `measured_at`, for the
same reason: **a trend line may only be drawn within one probe-set version at one k.** Extending the
probe set changes what is being asked, so the step it produces is not a regression and must not be
alerted as one. And `recall@5` and `recall@10` are different measurements of the same index — recall
is non-decreasing in `k`, since a larger `k` can only add hits to the numerator — so a series that
mixes them moves when the reporting choice moves, and its jumps get read as corpus changes. The
column exists precisely so the comparison can exclude the other k; a schema that records `k` while
the queries ignore it is worse than not recording it, because the mixture now looks deliberate.

Compare within a version **and** within a k; re-baseline explicitly when you cut a new probe set, and
keep one row per (version, k) rather than letting one overwrite the other.

Alert on the trailing baseline, per class, not on an absolute floor:

```sql
-- $3 is k. Every clause that selects rows for comparison must carry it.
WITH latest AS (
  SELECT * FROM retrieval_quality_runs
  WHERE spec_key = $1 AND probe_set_ver = $2 AND k = $3
  ORDER BY measured_at DESC LIMIT 1
),
baseline AS (                       -- median of the prior window, same version, same k
  SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY recall_overall) AS med
  FROM retrieval_quality_runs
  WHERE spec_key = $1 AND probe_set_ver = $2 AND k = $3
    AND measured_at >= now() - interval '60 days'
    AND measured_at <  (SELECT measured_at FROM latest)
)
SELECT l.recall_overall, b.med, l.recall_overall - b.med AS delta
FROM latest l CROSS JOIN baseline b;
```

A median over a window, not the single previous run: one noisy run should not page anybody, and a
slow slide is exactly the shape this is meant to catch.

### Probe-set coverage, which is what goes stale

```sql
-- Classes with no probe at all: an unmonitored slice of the corpus.
SELECT d.doc_class, count(*) AS rows
FROM docs d
WHERE d.doc_class NOT IN (SELECT doc_class FROM probe_set WHERE version = $1)
GROUP BY 1 ORDER BY rows DESC;

-- Recency: how much of what arrived lately is inside any probe's relevant set.
SELECT count(*) FILTER (WHERE id IN (SELECT unnest(relevant_ids) FROM probe_set WHERE version = $1))
         ::numeric / nullif(count(*), 0) AS recent_coverage
FROM docs WHERE created_at >= now() - interval '90 days';
```

Both queries are meant to return an uncomfortable number as the corpus grows. That discomfort is the
signal to cut a new probe-set version — not to widen the alert threshold.
