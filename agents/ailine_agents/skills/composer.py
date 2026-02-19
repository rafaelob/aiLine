"""Compose skill instructions into system prompt fragments with token budget management.

The SkillPromptComposer takes a set of activated skills (each with priority,
instructions, and reason) and produces a single markdown fragment that fits
within a configurable token budget.  This fragment is injected into the LLM
system prompt so the model operates under the right pedagogical skill set.

Token estimation uses a fast heuristic (chars / 4) which is accurate enough
for budget gating without needing a real tokeniser dependency.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TRUNCATION_MARKER = "(... truncated due to token limit ...)"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActivatedSkill:
    """A skill that has been selected for the current prompt context.

    Attributes:
        name: Unique identifier for the skill (e.g. ``"lesson-planner"``).
        description: Short human-readable summary of the skill's purpose.
        instructions_md: Full markdown instructions to inject into the prompt.
        reason: Why this skill was selected (displayed in the header listing).
        priority: Ordering weight -- lower values are higher priority.
            ``0`` = pinned (always included first),
            ``10`` = accessibility (high importance),
            ``20`` = matched (standard match).
    """

    name: str
    description: str
    instructions_md: str
    reason: str
    priority: int


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in *text* using a chars/4 heuristic.

    This intentionally over-counts slightly for safety so we stay within
    budget even when the real tokeniser would produce fewer tokens.

    Returns:
        Estimated token count, always >= 1 for non-empty text, 0 for empty.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def truncate_to_budget(text: str, budget_tokens: int) -> str:
    """Truncate *text* so its estimated token count fits within *budget_tokens*.

    If the text already fits, it is returned unchanged.  Otherwise it is
    sliced to approximately ``budget_tokens * 4`` characters (keeping the
    beginning which typically contains the most important rules) and a
    visible truncation marker is appended.

    Args:
        text: The source text to truncate.
        budget_tokens: Maximum token budget for the result.

    Returns:
        The (possibly truncated) text.
    """
    if budget_tokens <= 0:
        return _TRUNCATION_MARKER

    if estimate_tokens(text) <= budget_tokens:
        return text

    # Reserve space for the marker itself.
    marker_chars = len(_TRUNCATION_MARKER) + 1  # +1 for the newline
    max_chars = max(0, budget_tokens * 4 - marker_chars)
    truncated = text[:max_chars].rstrip()
    return f"{truncated}\n{_TRUNCATION_MARKER}"


# ---------------------------------------------------------------------------
# Composer
# ---------------------------------------------------------------------------


def compose_skills_fragment(
    skills: Iterable[ActivatedSkill],
    *,
    token_budget: int = 2500,
    per_skill_min_tokens: int = 120,
    per_skill_soft_cap_tokens: int = 900,
) -> str:
    """Compose a prompt fragment from activated skills within a token budget.

    The algorithm:

    1. Sort skills by ``(priority, name)`` ascending so higher-priority
       skills appear first and are last to be dropped.
    2. Build a header section listing every skill name and its selection
       reason.
    3. For each skill, format a ``## Skill: {name}`` block containing
       the description and instruction markdown.
    4. Apply a per-skill soft cap to prevent any single skill from
       consuming the entire budget.
    5. If the total still exceeds the budget, truncate instruction
       blocks starting from the lowest-priority skill.
    6. If *still* over budget, drop the lowest-priority skills entirely
       until the fragment fits.
    7. The highest-priority skill is never dropped -- its instructions
       are truncated instead.

    Args:
        skills: Activated skills to include.
        token_budget: Total token budget for the composed fragment.
        per_skill_min_tokens: Minimum tokens to allocate per skill block
            (below this the skill is dropped rather than producing a
            uselessly tiny snippet).
        per_skill_soft_cap_tokens: Soft cap per skill to prevent one large
            skill from crowding out others.

    Returns:
        Markdown fragment ready for injection into the system prompt.
        Empty string only if *skills* is empty.
    """
    sorted_skills = sorted(skills, key=lambda s: (s.priority, s.name))
    if not sorted_skills:
        return ""

    # ------------------------------------------------------------------
    # Phase 1: Build header
    # ------------------------------------------------------------------
    header_lines = ["## Skills Runtime (Active)", ""]
    for skill in sorted_skills:
        header_lines.append(f"- **{skill.name}**: {skill.reason}")
    header_lines.append("")
    header = "\n".join(header_lines)

    header_tokens = estimate_tokens(header)
    remaining_budget = token_budget - header_tokens

    # ------------------------------------------------------------------
    # Phase 2: Build per-skill blocks with soft cap
    # ------------------------------------------------------------------
    blocks: list[tuple[ActivatedSkill, str]] = []
    for skill in sorted_skills:
        raw_block = _format_skill_block(skill)
        capped_block = truncate_to_budget(raw_block, per_skill_soft_cap_tokens)
        blocks.append((skill, capped_block))

    # ------------------------------------------------------------------
    # Phase 3: Fit within total budget
    # ------------------------------------------------------------------
    total_tokens = sum(estimate_tokens(blk) for _, blk in blocks)

    if total_tokens <= remaining_budget:
        # Everything fits -- assemble and return.
        return _assemble(header, blocks)

    # ------------------------------------------------------------------
    # Phase 4: Proportional truncation of instruction blocks
    # ------------------------------------------------------------------
    # Distribute remaining budget proportionally but respect min tokens.
    blocks = _proportional_truncate(blocks, remaining_budget, per_skill_min_tokens)

    total_tokens = sum(estimate_tokens(blk) for _, blk in blocks)
    if total_tokens <= remaining_budget:
        return _assemble(header, blocks)

    # ------------------------------------------------------------------
    # Phase 5: Drop lowest-priority skills until budget fits
    # ------------------------------------------------------------------
    blocks = _drop_until_fits(blocks, remaining_budget, per_skill_min_tokens)

    # Rebuild the header to reflect surviving skills only.
    surviving_names = {skill.name for skill, _ in blocks}
    header = _rebuild_header(sorted_skills, surviving_names)

    return _assemble(header, blocks)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _format_skill_block(skill: ActivatedSkill) -> str:
    """Format a single skill into a markdown block."""
    parts = [f"## Skill: {skill.name}"]
    if skill.description:
        parts.append(skill.description)
    parts.append("")
    parts.append(skill.instructions_md)
    return "\n".join(parts)


def _proportional_truncate(
    blocks: list[tuple[ActivatedSkill, str]],
    budget: int,
    min_tokens: int,
) -> list[tuple[ActivatedSkill, str]]:
    """Truncate blocks proportionally to fit within *budget*.

    Skills that are already below the proportional share are left as-is;
    only oversized blocks are shrunk.
    """
    if not blocks:
        return blocks

    total_tokens = sum(estimate_tokens(blk) for _, blk in blocks)
    if total_tokens <= budget:
        return blocks

    result: list[tuple[ActivatedSkill, str]] = []
    for skill, block_text in blocks:
        block_tokens = estimate_tokens(block_text)
        # Proportional share, but at least min_tokens.
        share = max(min_tokens, int(budget * block_tokens / total_tokens))
        result.append((skill, truncate_to_budget(block_text, share)))
    return result


def _drop_until_fits(
    blocks: list[tuple[ActivatedSkill, str]],
    budget: int,
    min_tokens: int,
) -> list[tuple[ActivatedSkill, str]]:
    """Drop lowest-priority (last) blocks until the total fits in *budget*.

    The first block (highest priority) is never dropped; its instructions
    are truncated to fit if necessary.
    """
    while len(blocks) > 1:
        total = sum(estimate_tokens(blk) for _, blk in blocks)
        if total <= budget:
            break
        blocks = blocks[:-1]

    # If only the highest-priority block remains and still exceeds budget,
    # hard-truncate it.
    if blocks:
        total = sum(estimate_tokens(blk) for _, blk in blocks)
        if total > budget:
            skill, block_text = blocks[0]
            blocks = [(skill, truncate_to_budget(block_text, max(min_tokens, budget)))]

    return blocks


def _rebuild_header(
    all_skills: list[ActivatedSkill],
    surviving_names: set[str],
) -> str:
    """Rebuild the header section listing only surviving skills."""
    header_lines = ["## Skills Runtime (Active)", ""]
    for skill in all_skills:
        if skill.name in surviving_names:
            header_lines.append(f"- **{skill.name}**: {skill.reason}")
    header_lines.append("")
    return "\n".join(header_lines)


def _assemble(header: str, blocks: list[tuple[ActivatedSkill, str]]) -> str:
    """Join header and skill blocks into the final fragment."""
    parts = [header]
    for _, block_text in blocks:
        parts.append(block_text)
    return "\n---\n\n".join(parts)
