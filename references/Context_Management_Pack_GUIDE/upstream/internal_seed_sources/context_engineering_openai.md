# Context Engineering — Short-Term Memory Management with Sessions (OpenAI Agents SDK)

---

## Table of contents

1. [What this guide covers](#what-this-guide-covers)
2. [Why context management matters](#why-context-management-matters)

   * [Figure 1 — Memory OFF vs ON](#figure-1--memory-off-vs-on-agent-memory-off-vs-onpng)
3. [Prerequisites & quick smoke test](#prerequisites--quick-smoke-test)
4. [Technique A — Context Trimming (keep last-N user turns)](#technique-a--context-trimming-keep-lastn-user-turns)

   * [What counts as a “turn”](#what-counts-as-a-turn-trimming-turn-boundarypng)
   * [Choosing `max_turns`](#choosing-max_turns)
   * [Why trimming works & when it runs](#why-trimming-works--when-it-runs)
5. [Technique B — Context Summarization (older → summary, keep last-K verbatim)](#technique-b--context-summarization-older--summary-keep-lastk-verbatim)

   * [Summary prompt (structure & rules)](#summary-prompt-structure--rules)
   * [Principles for great memory summaries](#principles-for-great-memory-summaries)
   * [Implementation outline & concurrency discipline](#implementation-outline--concurrency-discipline)
   * [Figures 3 & 4 — SummarizingSession flows](#figures-3--4--summarizingsession-flows)
6. [APIs & data model](#apis--data-model)
7. [Observability & debugging](#observability--debugging)
8. [Evaluation playbook](#evaluation-playbook)
9. [Notes & design choices](#notes--design-choices)
10. [Appendix A — Image asset map](#appendix-a--image-asset-map)
11. [Appendix B — Worked examples (trimming & summarizing)](#appendix-b--worked-examples-trimming--summarizing)

---

## What this guide covers

* **Problem.** Long, multi-turn agent runs need **active context management**. Keeping *too much* history slows models and derails tool use; keeping *too little* causes amnesia and rework.
* **Context = tokens** the model can see at once (input + output). Even with large windows, raw chat logs, redundant tool outputs, and noisy retrievals will overwhelm prompts.
* **Goal.** Keep agents **fast, coherent, cost-efficient** by curating short-term memory.
* **Two concrete patterns** using the OpenAI Agents SDK `Session` abstraction:

  1. **Context Trimming** — drop older turns, keep the **last *N user turns*** intact.
  2. **Context Summarization** — compress the **older prefix** into a **structured summary**, then **keep the last *K* user turns** verbatim.

---

## Why context management matters

* **Sustained coherence.** Prevents “yesterday’s plan” from overriding today’s ask.
* **Higher tool-call accuracy.** Better function selection/arguments, fewer retries & timeouts in multi-tool runs.
* **Lower latency & cost.** Smaller prompts = fewer tokens = faster turns.
* **Error/hallucination containment.** Summaries act like “clean rooms”; trimming avoids amplifying bad facts (“context poisoning”).
* **Easier debugging & observability.** Bounded histories stabilize logs for diffs, attributions, and reproducible failures.
* **Multi-issue & handoff resilience.** Per-issue mini-summaries let you pause/resume, escalate to humans, or hand off to other agents smoothly.

### Figure 1 — Memory OFF vs ON (`agent-memory-off-vs-on.png`)

![Agent memory OFF vs ON](agent-memory-off-vs-on.png)

**ASCII sketch**

```
Without Memory (OFF)                        With Memory (ON)
-------------------------------------      --------------------------------------
U: Hi, need help.                           U: Hi, need help.
A: Sure, what's up?                         A: Sure — we tried X and Y yesterday.
                                            Here's what's next.

... (assistant forgets prior steps) ...     U: LED still blinking.
U: LED still blinking.                      A: Got it. After reset, we saw error 42.
A: Which LED?                               Next step: check battery health -> Z.

=> Re-asks, repeats tools.                  => Continues from accurate current state.
```

---

## Prerequisites & quick smoke test

* **Install libraries**

  ```bash
  pip install openai-agents nest_asyncio
  ```
* **Configure the OpenAI client** (API key via env or directly) and run a **hello-world agent** (e.g., a “Customer Support Assistant”) to verify setup.
* **Runner basics.** You’ll use `Runner.run(...)` with your agent(s) and a `Session` to pass conversation history.

---

## Technique A — Context Trimming (keep last-N user turns)

**Idea.** Keep only the **last *N* user turns**, where a **turn** = one **real user** message **plus everything that follows it** (assistant replies, tool calls/results, reasoning) **until the next user message**.

**Pros**

* Deterministic & simple (no extra model calls).
* Lowest latency/cost.
* Recent steps preserved **verbatim** (great for debugging & tool reproducibility).

**Cons**

* A hard cut-off: long-range details (IDs, constraints, decisions) can vanish.
* Recent turns with big tool payloads can still be large.

**Best for**

* Tool-heavy flows where nearby context dominates (ops automations, CRM/API tasks).
* Predictable behavior and very low overhead.

### What counts as a “turn” (`trimming-turn-boundary.png`)

![Turn boundary diagram](trimming-turn-boundary.png)

**ASCII timeline**

```
Index →  0        1           2             3        4         5        6         7
        ┌──────┐  ┌──────────┐ ┌───────────┐ ┌──────┐ ┌───────┐ ┌──────┐ ┌───────┐ ┌──────┐
Role →  user    assistant      tool_call     tool_res user      assistant user      assistant
Turn A: [ user0 → assistant1 → tool2 → tool3 ]
Turn B: [ user4 → assistant5 ]
Turn C: [ user6 → assistant7 ]

Keep last N *user* turns (e.g., N=2) ⇒ keep Turn B + Turn C (indices 4..7), drop 0..3.
```

### Choosing `max_turns`

* **Measure.** Sample transcripts; compute user-turn counts per conversation and per “issue” inside a conversation.
* **Grade.** Use an LLM grader to estimate how many turns are needed to complete the average issue; start with that as `max_turns`.
* **Iterate.** Adjust by evals (see [Evaluation playbook](#evaluation-playbook)).

### Why trimming works & when it runs

* **Why:** The assistant always has **complete nearby turns** (recent asks + tool effects). Old context is discarded wholesale (no partial turn fragments).
* **When:**

  * **On write:** `add_items(...)` appends then **immediately trims** to the last N user turns.
  * **On read:** `get_items(...)` returns a **trimmed view** (defensive if something bypassed a write).

---

## Technique B — Context Summarization (older → summary, keep last-K verbatim)

**Idea.** Set two knobs:

* `context_limit` — maximum **real user turns** in raw history before summarizing.
* `keep_last_n_turns` — how many **recent** user turns to preserve **verbatim** after summarizing.

**Invariant:** `keep_last_n_turns ≤ context_limit`.

**Flow (high level)**

1. When real user turns **exceed** `context_limit`, **summarize the prefix** (everything before the earliest of the last `keep_last_n_turns` turn starts).
2. **Inject** a synthetic pair at the top of the kept region:

   * **user (shadow prompt):** “Summarize the conversation we had so far.”
   * **assistant (summary):** *structured, ≤200-word snapshot*
3. **Keep last `keep_last_n_turns`** user turns **verbatim**.

**Pros**

* Retains long-range memory compactly (decisions, IDs, constraints, rationales).
* Smoother UX for very long threads; avoids “amnesia”.

**Cons**

* Risk of summary loss/bias; needs a careful prompt and evals.
* Extra latency/cost at refresh points.

**Best for**

* Analyst/concierge workflows, planning/coaching, policy/RAG Q&A where accumulated context matters.

### Summary prompt (structure & rules)

**Sections (≤200 words total; short bullets; verbs first)**

* **Product & Environment** — device/model, OS/app versions, network/context.
* **Reported Issue** — single-sentence latest problem statement.
* **Steps Tried & Results** — chronological, including tools & exact error strings/codes.
* **Identifiers** — ticket #, serial, account/email if provided.
* **Timeline Milestones** — key events with timestamps or relative ordering.
* **Tool Performance Insights** — which tools worked/failed and why (if evident).
* **Current Status & Blockers** — resolved vs pending; explicit blockers.
* **Next Recommended Step** — one concrete action (or two alternatives) aligned with policy/tooling.

**Rules**

* **Contradiction check** vs system/tool definitions and recent updates; **latest wins**.
* **Temporal ordering** — make freshness explicit.
* **Hallucination control** — never invent facts; quote errors exactly.
* **Concise bullets** — no fluff; readable at a glance.

### Principles for great memory summaries

* **Use-case specificity.** Tailor sections/phrasing to the workflow.
* **Chunking.** Prefer structured sections over paragraphs.
* **Tool insights.** Capture lessons from failures/successes.
* **Model choice & budget.** Balance quality vs latency/tokens; sometimes using the **same model** as the agent helps consistency.

### Implementation outline & concurrency discipline

* **Records.** Store items as `{"msg": {...}, "meta": {...}}`. Only allow `{"role","content","name"}` through to the model; everything else lives in `meta`.
* **Decision step (locked).** Count **real** user turn starts (role == "user" and not `meta.synthetic`). If `real_turns > context_limit`, compute `boundary` = earliest index of the last `keep_last_n_turns` user-turn starts.
* **Snapshot (outside lock).** Copy prefix messages up to `boundary`; **summarize** with your summarizer (e.g., `LLMSummarizer`).
* **Apply (locked again).** Re-check condition to avoid races; if still needed, **replace prefix** with synthetic `(user→assistant)` pair + **keep** suffix; normalize synthetic flags on all real user/assistant records.
* **Idempotency.** If messages arrive mid-summary, the re-check prevents stale rewrites.
* **Sanitization helpers.**

  * `_sanitize_for_model(msg)` — drop non-allowed keys.
  * `_is_real_user_turn_start(rec)` — role=='user' and not synthetic.
  * `_normalize_synthetic_flags_locked()` — ensure explicit boolean flags for observability.

### Figures 3 & 4 — SummarizingSession flows

**Figure 3 — High-level idea (`summarizing-session-overview.png`)**

![SummarizingSession overview](summarizing-session-overview.png)

```
Raw history (many turns) ──> Count real user turns
         |                       |
         | if real_turns > context_limit
         v
  [ Summarize prefix BEFORE earliest of last K user-turns ]
         |
         v
Insert at boundary:
  user(synthetic): "Summarize the conversation we had so far."
  assistant(synthetic): "<structured summary>"
         |
         v
Keep last K user-turns verbatim  ──>  Provide trimmed+summarized history to model
```

**Figure 4 — Summary injection + keep-last-N (`summary-plus-keep-last-n.png`)**

![Summary + keep last N](summary-plus-keep-last-n.png)

```
BEFORE (indices)
0 .. [ prefix to summarize ] .. b-1 | b .. [ kept K turns verbatim ] .. end

AFTER
[ user(synth): "Summarize the conversation we had so far." ]
[ assistant(synth): "<structured summary (sections ..)>" ]
| b .. [ kept K turns verbatim ] .. end
```

---

## APIs & data model

**Session API (typical methods)**

* `get_items(limit: Optional[int]) -> List[Msg]` — model-safe, possibly trimmed.
* `add_items(items: List[Msg]) -> None` — append; trimming/summarization may run.
* `pop_item() -> Optional[Msg]` — pop latest model-safe message.
* `clear_session() -> None` — clear records.
* `get_full_history(limit: Optional[int]) -> List[Record]` — debug/analytics; raw `{"msg","meta"}`.
* `get_items_with_metadata() -> List[Record]` — like above with structured metadata.
* **Trimming-only helper:** `set_max_turns(n: int)` and `raw_items()` (debug).

**Record & keys**

* **Message (`msg`) allowed keys:** `{"role","content","name"}`.
* **Metadata (`meta`) examples:** ids, tool info, timestamps, `synthetic: bool`.
* **Tool roles:** define a set like `{"tool","tool_result"}` to reduce prompt noise (e.g., summarizer builds snippets from tool outputs with limits).

**Synthetic flags**

* All **real** user/assistant messages must have `meta.synthetic = False`.
* The inserted **summary pair** has `meta.synthetic = True`.

**Edge cases**

* `keep_last_n_turns = 0` ⇒ summarize **everything** before suffix; keep no recent verbatim turns (rare; mostly for archival compression).
* If `boundary <= 0`, skip summarization (nothing to summarize).
* Clamp `keep_last_n_turns` to `context_limit` when callers change knobs.

---

## Observability & debugging

* **Stable logs.** After summarization, the “fresh side” (kept last K user turns) remains verbatim; the older side collapses into a **two-message** summary block (easy to detect by `synthetic` flag).
* **Inspection.** Use `get_items_with_metadata()` to see the full audit trail: synthetic shadow prompt, generated summary, real turns with ids/timestamps.
* **Consistency checks.** Log token counts before/after to catch aggressive pruning; diff summaries across runs to track regressions.

---

## Evaluation playbook

* **Baseline & deltas.** Keep your core evals; compare before/after adopting trimming/summarization.
* **LLM-as-Judge.** Grade summary quality with a rubric focusing on: fidelity, freshness, critical details, and the requested structure.
* **Transcript replay.** Re-run long conversations and measure next-turn accuracy with vs without memory (entities/IDs exact-match; rubric scoring for reasoning).
* **Error regression tracking.** Watch for dropped constraints, unanswered questions, and unnecessary/repeated tool calls.
* **Token pressure checks.** Alert when token limits force dropping **protected** context; log pre/post token counts.

---

## Notes & design choices

* **Turn boundary preserved on the fresh side.** The K kept turns remain exactly as they happened.
* **Two-message summary block.** Predictable for renderers and downstream tools.
* **Async + locks.** Release the lock while the summarizer runs; **re-check** the condition after await; then apply the summary atomically.
* **Idempotency.** Late arrivals during summarization won’t corrupt state due to the post-await re-check.
* **Customization knobs.**

  * Trimming: `max_turns`.
  * Summarizing: `context_limit`, `keep_last_n_turns`, summarizer `model`, `max_tokens`, and (optional) **tool snippet limits** to avoid giant tool payloads.

---

## Appendix A — Image asset map

Use these filenames when exporting/embedding visuals:

* `agent-memory-off-vs-on.png` — Memory OFF vs ON side-by-side.
* `trimming-turn-boundary.png` — What counts as a turn (timeline).
* `summarizing-session-overview.png` — High-level summarization flow.
* `summary-plus-keep-last-n.png` — Summary injection + keep-last-N.

---

## Appendix B — Worked examples (trimming & summarizing)

### B1) Trimming example (tiny history)

```
History (old → new):
0: user       "Hi"
1: assistant  "Hello!"
2: tool_call  "lookup(...)"
3: tool_result "{...}"
4: user       "It didn't work"
5: assistant  "Try rebooting"
6: user       "Rebooted, now error 42"
7: assistant  "On it"
```

* With `max_turns = 2`, user turns are at indices **4** and **6**.
* Earliest kept = **4** ⇒ **keep 4..7** (two complete turns), **drop 0..3**.

**Why this works well**

* Recent asks and tool effects stay intact; older noise is removed entirely.
* Trimming runs **on write** and **on read** to guarantee boundedness.

---

### B2) Summarizing example (router case)

**Raw narrative (condensed)**

* User checks FAQs → no fix.
* Firmware v1.0.3 confirmed.
* Factory reset → now **error 42**.
* Later, user reports **404** when accessing a page.
* Agent asks about connectivity, continues troubleshooting.

**After summarization (illustrative, ≤200 words)**

```
• Product & Environment:
  - Router, Firmware v1.0.3; Windows 10.
• Reported Issue:
  - Router fails to connect; after factory reset, shows error 42. Later, web page returns 404.
• Steps Tried & Results:
  - FAQs checked: no resolution.
  - Firmware verified: v1.0.3 (issue persists).
  - Factory reset: produced error 42.
• Identifiers:
  - Not provided.
• Timeline Milestones:
  - FAQs → Firmware check → Factory reset → Error 42 → 404 on webpage.
• Tool Performance Insights:
  - Version check succeeded; reset did not resolve and introduced 42.
• Current Status & Blockers:
  - Connectivity uncertain; exact 404 context unclear.
• Next Recommended Step:
  - Verify WAN link, DNS, and router admin portal; capture full 404 URL & time.
```

**Injected pair at boundary**

* `user (synthetic)`: “Summarize the conversation we had so far.”
* `assistant (synthetic)`: *(the structured summary above)*

**Kept verbatim**

* The **last K** real user turns (e.g., “I got 404…”, “Are you connected…”) remain intact, ensuring freshness for the next model turn.

---

### B3) Summary-prompt template (ready to adapt)

```
SYSTEM
You are a senior customer-support assistant for tech devices and setups.
Compress the earlier conversation into a precise, reusable snapshot.

Before you write (silently):
- Contradiction check (user vs system/tool defs; latest info wins).
- Temporal ordering (sort events; mark superseded info).
- Hallucination control (do not invent; quote error strings/codes).

Write a structured summary (≤200 words) with sections:
• Product & Environment
• Reported Issue
• Steps Tried & Results
• Identifiers
• Timeline Milestones
• Tool Performance Insights
• Current Status & Blockers
• Next Recommended Step

Rules:
- Concise bullets; verbs first; no fluff.
- Quote exact error strings/codes when available.
- If earlier info is superseded, note “Superseded:” and omit details.
```

---

### B4) Implementation skeletons (for orientation)

> The guide’s code shows full implementations; below are condensed skeletons to orient your own code layout.

**Trimming session (essentials, conceptual)**

```python
class TrimmingSession(SessionABC):
    def __init__(self, name: str, max_turns: int = 3):
        self.name = name
        self.max_turns = max(1, int(max_turns))
        self._items = deque()
        self._lock = asyncio.Lock()

    async def get_items(self, limit: int | None = None):
        async with self._lock:
            trimmed = self._trim_to_last_user_turns(list(self._items))
        return trimmed[-limit:] if (limit and limit >= 0) else trimmed

    async def add_items(self, items: list[Msg]):
        if not items: return
        async with self._lock:
            self._items.extend(items)
            trimmed = self._trim_to_last_user_turns(list(self._items))
            self._items.clear()
            self._items.extend(trimmed)

    def _trim_to_last_user_turns(self, items: list[Msg]) -> list[Msg]:
        # Walk backward; find earliest index among the last N real user messages.
        count, start_idx = 0, 0
        for i in range(len(items) - 1, -1, -1):
            if items[i].get("role") == "user":
                count += 1
                if count == self.max_turns:
                    start_idx = i
                    break
        return items[start_idx:]
```

**Summarizer & summarizing session (essentials, conceptual)**

```python
class LLMSummarizer:
    def __init__(self, client, model="gpt-4o", max_tokens=400, tool_trim_limit=2048):
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.tool_trim_limit = tool_trim_limit

    async def summarize(self, messages: list[Msg]) -> tuple[str, str]:
        # Build compact snippets from history (tools/results trimmed)
        prompt = [
          {"role": "system", "content": SUMMARY_PROMPT},
          {"role": "user", "content": "\n".join(make_snippets(messages, self.tool_trim_limit))}
        ]
        summary = await to_text(self.client, self.model, prompt, self.max_tokens)
        return "Summarize the conversation we had so far.", summary


class SummarizingSession:
    _ALLOWED_MSG_KEYS = {"role", "content", "name"}

    def __init__(self, keep_last_n_turns=2, context_limit=3, summarizer: LLMSummarizer | None = None):
        self.keep_last_n_turns = int(keep_last_n_turns)
        self.context_limit = int(context_limit)
        self.summarizer = summarizer
        self._records: list[dict] = []     # {"msg": {...}, "meta": {...}}
        self._lock = asyncio.Lock()

    async def add_items(self, items: list[Msg]) -> None:
        # 1) Ingest
        async with self._lock:
            for it in items:
                msg, meta = self._split_msg_and_meta(it)
                self._records.append({"msg": msg, "meta": meta})
            need, boundary = self._summarize_decision_locked()

        if not need:
            async with self._lock:
                self._normalize_synth_flags_locked()
            return

        # 2) Snapshot (no lock) and summarize
        async with self._lock:
            prefix = [r["msg"] for r in self._records[:boundary]]
        user_shadow, summary_text = await self._summarize(prefix)

        # 3) Apply (re-check under lock)
        async with self._lock:
            still_need, new_boundary = self._summarize_decision_locked()
            if not still_need:
                self._normalize_synth_flags_locked()
                return
            # Replace prefix with synthetic pair, keep suffix
            synth = [
              {"msg": {"role": "user", "content": user_shadow}, "meta": {"synthetic": True}},
              {"msg": {"role": "assistant", "content": summary_text}, "meta": {"synthetic": True}},
            ]
            suffix = self._records[new_boundary:]  # last K turns verbatim
            self._records = synth + suffix
            self._normalize_synth_flags_locked()
```
