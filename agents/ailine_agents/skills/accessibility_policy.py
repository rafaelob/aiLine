"""Accessibility-to-skill policy mapping for automatic skill selection.

Maps the 7 accessibility need categories from
``ailine_runtime.accessibility.profiles.AccessibilityNeeds`` to the 17
available skill slugs.  The mapping encodes domain knowledge about *which*
skills materially help a given accessibility profile and at what priority.

Design decisions
----------------
* ``SkillPolicy`` is a frozen dataclass (immutable after creation) to
  guarantee the mapping table is never accidentally mutated at runtime.
* Priority tiers (must / should / nice) translate to numeric priority
  values (0 / 10 / 20) so callers can sort deterministically.
* ``human_review_triggers`` captures skills whose activation implies the
  plan must go through a human reviewer (e.g. sign-language content
  requires a certified interpreter to validate).
* ``resolve_accessibility_skills`` deduplicates across multiple needs,
  always keeping the *highest* priority (lowest numeric value) for each
  skill, then trims to ``max_skills``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# ---------------------------------------------------------------------------
# Constants — canonical skill slugs (kept in sync with skills/ directory)
# ---------------------------------------------------------------------------

ALL_SKILL_SLUGS: Final[frozenset[str]] = frozenset(
    {
        "accessibility-adaptor",
        "accessibility-coach",
        "audio-description-generator",
        "curriculum-bncc-align",
        "curriculum-mapper",
        "curriculum-us-align",
        "differentiated-instruction",
        "lesson-planner",
        "multi-language-content-adapter",
        "parent-report-generator",
        "progress-analyzer",
        "quiz-generator",
        "rubric-writer",
        "sign-language-interpreter",
        "socratic-tutor",
        "study-plan-personalizer",
        "tutor-agent-builder",
    }
)

# The 7 accessibility need categories from profiles.py.
ACCESSIBILITY_NEED_CATEGORIES: Final[frozenset[str]] = frozenset(
    {
        "autism",
        "adhd",
        "learning",
        "hearing",
        "visual",
        "speech_language",
        "motor",
    }
)

# Numeric priority values for each tier.
_PRIORITY_MUST: Final[int] = 0
_PRIORITY_SHOULD: Final[int] = 10
_PRIORITY_NICE: Final[int] = 20


# ---------------------------------------------------------------------------
# SkillPolicy — immutable policy for a single accessibility need
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SkillPolicy:
    """Skill selection policy for a single accessibility need category.

    Attributes:
        must: Skills that *must* be included when this need is active.
        should: Skills that *should* be included if the skill budget allows.
        nice: Skills that are *nice to have* if there is still room.
        human_review_triggers: Skills whose activation requires human review
            of the generated plan before it reaches the learner.
    """

    must: tuple[str, ...]
    should: tuple[str, ...]
    nice: tuple[str, ...] = ()
    human_review_triggers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate that all referenced slugs are known skill slugs."""
        all_referenced = (
            set(self.must)
            | set(self.should)
            | set(self.nice)
            | set(self.human_review_triggers)
        )
        unknown = all_referenced - ALL_SKILL_SLUGS
        if unknown:
            raise ValueError(
                f"SkillPolicy references unknown skill slug(s): {sorted(unknown)}. "
                f"Valid slugs: {sorted(ALL_SKILL_SLUGS)}"
            )
        # human_review_triggers must be a subset of the union of must+should+nice
        selectable = set(self.must) | set(self.should) | set(self.nice)
        orphan_triggers = set(self.human_review_triggers) - selectable
        if orphan_triggers:
            raise ValueError(
                f"human_review_triggers {sorted(orphan_triggers)} are not in "
                "must/should/nice — they would never be selected."
            )


# ---------------------------------------------------------------------------
# ACCESSIBILITY_SKILL_POLICY — the canonical mapping table
# ---------------------------------------------------------------------------

ACCESSIBILITY_SKILL_POLICY: Final[dict[str, SkillPolicy]] = {
    # ── Autism (TEA) ──────────────────────────────────────────────────────
    # Predictability, clear communication, sensory considerations, visual
    # schedules and transition scripts.  Differentiated instruction and
    # personalised study plans are high-value.  Quiz/rubric writers provide
    # structured, predictable assessment.
    "autism": SkillPolicy(
        must=(
            "accessibility-coach",
            "accessibility-adaptor",
        ),
        should=(
            "differentiated-instruction",
            "study-plan-personalizer",
            "lesson-planner",
        ),
        nice=(
            "quiz-generator",
            "rubric-writer",
            "progress-analyzer",
        ),
    ),
    # ── ADHD ──────────────────────────────────────────────────────────────
    # Chunking, timers, checkpoints, movement breaks.  Personalised study
    # plans help with organisation; progress analysis keeps motivation
    # visible; quizzes provide frequent low-stakes checkpoints.
    "adhd": SkillPolicy(
        must=(
            "accessibility-coach",
            "accessibility-adaptor",
        ),
        should=(
            "differentiated-instruction",
            "study-plan-personalizer",
            "progress-analyzer",
        ),
        nice=(
            "quiz-generator",
            "lesson-planner",
            "rubric-writer",
        ),
    ),
    # ── Learning difficulties (dyslexia, learning gaps) ───────────────────
    # Simplified language, glossaries, examples-first, alternative response
    # formats.  Multi-language adapter helps simplify vocabulary; socratic
    # tutor provides scaffolded guidance.
    "learning": SkillPolicy(
        must=(
            "accessibility-coach",
            "accessibility-adaptor",
        ),
        should=(
            "differentiated-instruction",
            "study-plan-personalizer",
            "multi-language-content-adapter",
            "socratic-tutor",
        ),
        nice=(
            "quiz-generator",
            "rubric-writer",
            "lesson-planner",
        ),
    ),
    # ── Hearing ───────────────────────────────────────────────────────────
    # Captions, transcripts, sign language, visual redundancy.  The sign-
    # language interpreter skill requires human review because generated
    # sign-language content must be validated by a certified interpreter.
    "hearing": SkillPolicy(
        must=(
            "accessibility-coach",
            "accessibility-adaptor",
        ),
        should=(
            "differentiated-instruction",
            "study-plan-personalizer",
            "sign-language-interpreter",
        ),
        nice=(
            "multi-language-content-adapter",
            "quiz-generator",
            "rubric-writer",
        ),
        human_review_triggers=("sign-language-interpreter",),
    ),
    # ── Visual ────────────────────────────────────────────────────────────
    # Alt text, audio descriptions, screen-reader structure, large print.
    # Audio-description-generator is a should (high value for visual
    # impairment).
    "visual": SkillPolicy(
        must=(
            "accessibility-coach",
            "accessibility-adaptor",
        ),
        should=(
            "differentiated-instruction",
            "study-plan-personalizer",
            "audio-description-generator",
        ),
        nice=(
            "quiz-generator",
            "rubric-writer",
            "lesson-planner",
        ),
    ),
    # ── Speech / Language ─────────────────────────────────────────────────
    # AAC/pictograms, alternative response methods, simplified language.
    # Multi-language adapter helps simplify; socratic tutor provides
    # gentle checking without requiring verbal fluency.
    "speech_language": SkillPolicy(
        must=(
            "accessibility-coach",
            "accessibility-adaptor",
        ),
        should=(
            "differentiated-instruction",
            "study-plan-personalizer",
            "multi-language-content-adapter",
            "socratic-tutor",
        ),
        nice=(
            "quiz-generator",
            "rubric-writer",
            "lesson-planner",
        ),
    ),
    # ── Motor ─────────────────────────────────────────────────────────────
    # Alternative input methods, reduced fine-motor demands.  Quiz and
    # rubric writers can generate MCQ / click-based assessments.
    "motor": SkillPolicy(
        must=(
            "accessibility-coach",
            "accessibility-adaptor",
        ),
        should=(
            "differentiated-instruction",
            "study-plan-personalizer",
        ),
        nice=(
            "quiz-generator",
            "rubric-writer",
            "lesson-planner",
        ),
    ),
}


# ---------------------------------------------------------------------------
# resolve_accessibility_skills — the main public function
# ---------------------------------------------------------------------------


def resolve_accessibility_skills(
    needs: list[str],
    *,
    max_skills: int = 8,
    available_skills: set[str] | None = None,
) -> tuple[list[tuple[str, str, int]], bool]:
    """Resolve accessibility needs into an ordered list of skills.

    Given one or more accessibility need categories (e.g. ``["autism", "hearing"]``),
    this function:

    1. Looks up the ``SkillPolicy`` for each need.
    2. Collects all referenced skills with their priority tier and a human-
       readable reason.
    3. Deduplicates: when the same skill appears in multiple needs, the
       *highest* priority (lowest numeric value) wins.
    4. Filters by ``available_skills`` if provided.
    5. Sorts by priority (ascending) then alphabetically within the same tier.
    6. Trims to ``max_skills``.
    7. Determines whether human review is required (any selected skill is
       in a ``human_review_triggers`` list).

    Args:
        needs: List of accessibility need category strings.  Unknown
            categories are silently skipped (defensive; callers should
            validate earlier).
        max_skills: Maximum number of skills to return.  Must be >= 1.
        available_skills: Optional allowlist of skill slugs that are
            actually loaded in the runtime.  ``None`` means all skills
            are available.

    Returns:
        A 2-tuple of:
        - ``list[tuple[str, str, int]]``: Ordered list of
          ``(skill_slug, reason, priority)`` where *priority* 0 is highest.
        - ``bool``: ``True`` if any selected skill triggers human review.

    Raises:
        ValueError: If ``max_skills`` < 1.
    """
    if max_skills < 1:
        raise ValueError(f"max_skills must be >= 1, got {max_skills}")

    # Collect all human-review trigger skills across matched needs.
    all_human_review_triggers: set[str] = set()

    # skill_slug -> (reason, priority)  — keep best (lowest) priority.
    candidates: dict[str, tuple[str, int]] = {}

    for need in needs:
        policy = ACCESSIBILITY_SKILL_POLICY.get(need)
        if policy is None:
            continue

        all_human_review_triggers.update(policy.human_review_triggers)

        # Process each tier.
        for slug in policy.must:
            _upsert_candidate(candidates, slug, need, _PRIORITY_MUST)
        for slug in policy.should:
            _upsert_candidate(candidates, slug, need, _PRIORITY_SHOULD)
        for slug in policy.nice:
            _upsert_candidate(candidates, slug, need, _PRIORITY_NICE)

    # Filter by available skills when an allowlist is given.
    if available_skills is not None:
        candidates = {k: v for k, v in candidates.items() if k in available_skills}

    # Sort: primary by priority (asc), secondary by slug (alpha) for stability.
    sorted_entries = sorted(candidates.items(), key=lambda item: (item[1][1], item[0]))

    # Trim to budget.
    trimmed = sorted_entries[:max_skills]

    result: list[tuple[str, str, int]] = [
        (slug, reason, priority) for slug, (reason, priority) in trimmed
    ]

    # Human review is required if any *selected* skill is a trigger.
    selected_slugs = {slug for slug, _, _ in result}
    needs_human_review = bool(selected_slugs & all_human_review_triggers)

    return result, needs_human_review


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_TIER_LABELS: Final[dict[int, str]] = {
    _PRIORITY_MUST: "must",
    _PRIORITY_SHOULD: "should",
    _PRIORITY_NICE: "nice",
}


def _upsert_candidate(
    candidates: dict[str, tuple[str, int]],
    slug: str,
    need: str,
    priority: int,
) -> None:
    """Insert or upgrade a candidate skill entry.

    If the skill is already tracked with a lower-or-equal priority, keep the
    existing entry.  Otherwise, replace with the higher-priority (lower
    numeric value) entry.

    The *reason* string records the need category and tier for traceability.
    """
    tier_label = _TIER_LABELS.get(priority, f"priority-{priority}")
    reason = f"{need}:{tier_label}"

    existing = candidates.get(slug)
    if existing is None or priority < existing[1]:
        candidates[slug] = (reason, priority)
