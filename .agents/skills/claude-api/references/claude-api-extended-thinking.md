# Claude API — Thinking / Extended Reasoning (detailed reference)

Extracted verbatim from `claude-api/SKILL.md` on 2026-07-28 to keep the SKILL.md body under the 5k-token cap.

---

Three modes, per the Messages API:

| Mode | Config | Notes |
|------|--------|-------|
| Adaptive | `{"type": "adaptive"}` | Model decides whether/how much to think. On by default on Sonnet 5. Supported on Fable 5.1 (mandatory — adaptive-only), Fable 5 (mandatory — adaptive-only), Opus 5 (mandatory — adaptive-only), and Opus 4.8 and Opus 4.7 (adaptive-only); also on Opus 4.6 and Sonnet 4.6 (both modes). |
| Enabled | `{"type": "enabled", "budget_tokens": N}` | Explicit budget; `N` >= 1024 and `<` `max_tokens`. Supported on Sonnet 4.6 and Opus 4.6 (deprecated — use adaptive instead); Haiku 4.5, Opus 4.5, Sonnet 4.5 (enabled-only, no adaptive). **Returns 400 on Fable 5.1, Fable 5, Opus 5, Sonnet 5, Opus 4.8, and Opus 4.7** (use adaptive; Fable models cannot disable thinking). |
| Disabled | `{"type": "disabled"}` | No thinking. **Fable 5.1 and Fable 5:** always returns 400. **Opus 5 only:** `disabled` itself returns 400 unless `output_config.effort` is `low`/`medium`/`high` — combining `disabled` with `xhigh`/`max` returns 400. Every other model in this table accepts `disabled` at any effort level. |

Both `enabled` and `adaptive` accept `display`: `"summarized"` or `"omitted"` (the default on Fable 5.1, Fable 5, and the adaptive models). Fable 5.1 additionally supports `"updates"` behind the `thinking-display-updates-2026-08-18` beta header.

#### Adaptive thinking (Fable 5.1, Fable 5, Opus 5, Opus 4.8, Sonnet 5, Sonnet 4.6) — recommended when available

```python
message = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=16000,
    thinking={"type": "adaptive"},
    messages=[{"role": "user", "content": "Solve this step by step: ..."}]
)

# Response contains thinking blocks and text blocks
for block in message.content:
    if block.type == "thinking":
        print("Thinking:", block.thinking)
    elif block.type == "text":
        print("Answer:", block.text)
```

#### Extended thinking with explicit budget (Sonnet 4.6, Haiku 4.5)

```python
message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 8000},
    messages=[{"role": "user", "content": "Solve this step by step: ..."}]
)
```

Note: Fable 5.1, Fable 5, Opus 5, Opus 4.8, and Opus 4.7 do NOT support `enabled`/extended thinking — use adaptive on these models (enabled returns a 400 error). Fable 5.1 and Fable 5 also reject `disabled`; use `output_config.effort` to control depth. Opus 5 goes one step further: `disabled` only works at `effort` <= `high` (400 at `xhigh`/`max`) — Opus 4.8 and Opus 4.7 allow `disabled` at any effort. Sonnet 4.6 and Opus 4.6 support both adaptive and enabled, but `enabled` (`budget_tokens`) is deprecated on these models and will be removed in a future release — migrate to adaptive mode. Haiku 4.5, Opus 4.5, and Sonnet 4.5 support enabled-only (no adaptive).
