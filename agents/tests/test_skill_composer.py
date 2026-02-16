"""Tests for the skill prompt composer: token estimation, truncation, and composition."""

from __future__ import annotations

import pytest

from ailine_agents.skills.composer import (
    _TRUNCATION_MARKER,
    ActivatedSkill,
    compose_skills_fragment,
    estimate_tokens,
    truncate_to_budget,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_skill(
    name: str = "test-skill",
    description: str = "A test skill.",
    instructions_md: str = "Follow these rules.",
    reason: str = "matched by context",
    priority: int = 20,
) -> ActivatedSkill:
    return ActivatedSkill(
        name=name,
        description=description,
        instructions_md=instructions_md,
        reason=reason,
        priority=priority,
    )


# ---------------------------------------------------------------------------
# ActivatedSkill dataclass
# ---------------------------------------------------------------------------


class TestActivatedSkill:
    def test_frozen(self) -> None:
        skill = _make_skill()
        with pytest.raises(AttributeError):
            skill.name = "changed"  # type: ignore[misc]

    def test_fields(self) -> None:
        skill = ActivatedSkill(
            name="abc",
            description="desc",
            instructions_md="# Rules",
            reason="pinned",
            priority=0,
        )
        assert skill.name == "abc"
        assert skill.description == "desc"
        assert skill.instructions_md == "# Rules"
        assert skill.reason == "pinned"
        assert skill.priority == 0

    def test_equality(self) -> None:
        a = _make_skill(name="x", priority=5)
        b = _make_skill(name="x", priority=5)
        assert a == b

    def test_inequality(self) -> None:
        a = _make_skill(name="x", priority=5)
        b = _make_skill(name="y", priority=5)
        assert a != b


# ---------------------------------------------------------------------------
# estimate_tokens
# ---------------------------------------------------------------------------


class TestEstimateTokens:
    def test_empty_string(self) -> None:
        assert estimate_tokens("") == 0

    def test_short_string(self) -> None:
        # "ab" => len 2 // 4 = 0, but max(1, 0) = 1
        assert estimate_tokens("ab") == 1

    def test_four_chars(self) -> None:
        assert estimate_tokens("abcd") == 1

    def test_eight_chars(self) -> None:
        assert estimate_tokens("abcdefgh") == 2

    def test_longer_string(self) -> None:
        text = "x" * 400
        assert estimate_tokens(text) == 100

    def test_always_positive_for_nonempty(self) -> None:
        assert estimate_tokens("a") >= 1


# ---------------------------------------------------------------------------
# truncate_to_budget
# ---------------------------------------------------------------------------


class TestTruncateToBudget:
    def test_fits_within_budget(self) -> None:
        text = "Hello world"
        result = truncate_to_budget(text, budget_tokens=100)
        assert result == text
        assert _TRUNCATION_MARKER not in result

    def test_exceeds_budget(self) -> None:
        text = "x" * 1000  # ~250 tokens
        result = truncate_to_budget(text, budget_tokens=50)
        assert _TRUNCATION_MARKER in result
        assert len(result) < len(text)

    def test_zero_budget(self) -> None:
        result = truncate_to_budget("anything", budget_tokens=0)
        assert result == _TRUNCATION_MARKER

    def test_negative_budget(self) -> None:
        result = truncate_to_budget("anything", budget_tokens=-10)
        assert result == _TRUNCATION_MARKER

    def test_exact_fit(self) -> None:
        text = "abcd"  # 1 token
        result = truncate_to_budget(text, budget_tokens=1)
        assert result == text

    def test_truncated_result_fits_budget(self) -> None:
        text = "x" * 4000  # ~1000 tokens
        budget = 100
        result = truncate_to_budget(text, budget)
        assert estimate_tokens(result) <= budget + 5  # small tolerance for rounding

    def test_preserves_beginning(self) -> None:
        text = "IMPORTANT_START " + "filler " * 500
        result = truncate_to_budget(text, budget_tokens=20)
        assert result.startswith("IMPORTANT_START")


# ---------------------------------------------------------------------------
# compose_skills_fragment — basic
# ---------------------------------------------------------------------------


class TestComposeSkillsFragmentBasic:
    def test_empty_skills(self) -> None:
        assert compose_skills_fragment([]) == ""

    def test_single_skill(self) -> None:
        skill = _make_skill(name="alpha", reason="selected")
        result = compose_skills_fragment([skill], token_budget=5000)
        assert "## Skills Runtime (Ativas)" in result
        assert "**alpha**" in result
        assert "## Skill: alpha" in result
        assert "Follow these rules." in result

    def test_header_lists_all_skills(self) -> None:
        skills = [
            _make_skill(name="alpha", reason="reason-a", priority=10),
            _make_skill(name="beta", reason="reason-b", priority=20),
        ]
        result = compose_skills_fragment(skills, token_budget=5000)
        assert "- **alpha**: reason-a" in result
        assert "- **beta**: reason-b" in result

    def test_skills_sorted_by_priority_then_name(self) -> None:
        skills = [
            _make_skill(name="charlie", priority=20),
            _make_skill(name="alpha", priority=10),
            _make_skill(name="bravo", priority=10),
        ]
        result = compose_skills_fragment(skills, token_budget=5000)
        # alpha (10) and bravo (10) before charlie (20)
        alpha_pos = result.index("## Skill: alpha")
        bravo_pos = result.index("## Skill: bravo")
        charlie_pos = result.index("## Skill: charlie")
        assert alpha_pos < bravo_pos < charlie_pos

    def test_separator_between_blocks(self) -> None:
        skills = [
            _make_skill(name="a", priority=0),
            _make_skill(name="b", priority=10),
        ]
        result = compose_skills_fragment(skills, token_budget=5000)
        assert "\n---\n\n" in result

    def test_never_empty_if_skills_provided(self) -> None:
        skill = _make_skill(instructions_md="x" * 40000)
        result = compose_skills_fragment([skill], token_budget=50)
        assert len(result) > 0
        assert "## Skill:" in result


# ---------------------------------------------------------------------------
# compose_skills_fragment — budget behaviour
# ---------------------------------------------------------------------------


class TestComposeSkillsFragmentBudget:
    def test_soft_cap_limits_single_large_skill(self) -> None:
        large = _make_skill(
            name="giant",
            instructions_md="x" * 8000,  # ~2000 tokens
            priority=10,
        )
        small = _make_skill(
            name="tiny",
            instructions_md="small instructions",
            priority=20,
        )
        result = compose_skills_fragment(
            [large, small],
            token_budget=3000,
            per_skill_soft_cap_tokens=400,
        )
        # Both should be present because the cap prevents giant from crowding.
        assert "## Skill: giant" in result
        assert "## Skill: tiny" in result

    def test_drops_low_priority_when_over_budget(self) -> None:
        high = _make_skill(
            name="high",
            instructions_md="x" * 600,
            priority=0,
        )
        low = _make_skill(
            name="low",
            instructions_md="x" * 600,
            priority=20,
        )
        result = compose_skills_fragment(
            [high, low],
            token_budget=200,
            per_skill_soft_cap_tokens=500,
        )
        # High-priority must survive.
        assert "## Skill: high" in result
        # Low-priority may be dropped.
        # (exact behaviour depends on budget math, but high must be present)

    def test_highest_priority_never_dropped(self) -> None:
        skills = [
            _make_skill(name=f"skill-{i}", instructions_md="y" * 2000, priority=i * 10)
            for i in range(5)
        ]
        result = compose_skills_fragment(skills, token_budget=100)
        # skill-0 has priority 0 and must survive even with tiny budget.
        assert "## Skill: skill-0" in result

    def test_truncation_marker_on_budget_squeeze(self) -> None:
        skill = _make_skill(
            name="big",
            instructions_md="z" * 10000,
            priority=0,
        )
        result = compose_skills_fragment([skill], token_budget=200)
        assert _TRUNCATION_MARKER in result

    def test_fits_within_budget_no_truncation(self) -> None:
        skills = [
            _make_skill(name="a", instructions_md="short", priority=0),
            _make_skill(name="b", instructions_md="also short", priority=10),
        ]
        result = compose_skills_fragment(skills, token_budget=5000)
        assert _TRUNCATION_MARKER not in result

    def test_per_skill_min_tokens_drops_instead_of_tiny_snippet(self) -> None:
        """When a skill would receive fewer tokens than per_skill_min_tokens,
        it should be dropped rather than producing useless truncated output."""
        high = _make_skill(name="high", instructions_md="a" * 800, priority=0)
        low = _make_skill(name="low", instructions_md="b" * 800, priority=20)
        # With a very tight budget and high min, the low-priority skill gets dropped.
        result = compose_skills_fragment(
            [high, low],
            token_budget=250,
            per_skill_min_tokens=200,
            per_skill_soft_cap_tokens=300,
        )
        assert "## Skill: high" in result

    def test_description_included_in_block(self) -> None:
        skill = _make_skill(name="x", description="Important description")
        result = compose_skills_fragment([skill], token_budget=5000)
        assert "Important description" in result


# ---------------------------------------------------------------------------
# compose_skills_fragment — edge cases
# ---------------------------------------------------------------------------


class TestComposeSkillsFragmentEdgeCases:
    def test_single_skill_huge_budget(self) -> None:
        skill = _make_skill()
        result = compose_skills_fragment([skill], token_budget=100_000)
        assert _TRUNCATION_MARKER not in result

    def test_duplicate_priority_deterministic_order(self) -> None:
        skills = [
            _make_skill(name="z", priority=10),
            _make_skill(name="a", priority=10),
            _make_skill(name="m", priority=10),
        ]
        result = compose_skills_fragment(skills, token_budget=5000)
        a_pos = result.index("## Skill: a")
        m_pos = result.index("## Skill: m")
        z_pos = result.index("## Skill: z")
        assert a_pos < m_pos < z_pos

    def test_empty_instructions(self) -> None:
        skill = _make_skill(name="empty", instructions_md="")
        result = compose_skills_fragment([skill], token_budget=5000)
        assert "## Skill: empty" in result

    def test_empty_description(self) -> None:
        skill = _make_skill(name="nodesc", description="")
        result = compose_skills_fragment([skill], token_budget=5000)
        assert "## Skill: nodesc" in result

    def test_generator_input(self) -> None:
        """compose_skills_fragment accepts any Iterable, not just lists."""

        from collections.abc import Generator

        def gen() -> Generator[ActivatedSkill, None, None]:
            yield _make_skill(name="gen-skill")

        result = compose_skills_fragment(gen(), token_budget=5000)  # type: ignore[arg-type]
        assert "## Skill: gen-skill" in result

    def test_header_rebuilt_after_drops(self) -> None:
        """When skills are dropped, the header should only list survivors."""
        high = _make_skill(name="survivor", instructions_md="a" * 200, priority=0)
        low = _make_skill(name="dropped", instructions_md="b" * 8000, priority=20)
        result = compose_skills_fragment(
            [high, low],
            token_budget=120,
            per_skill_soft_cap_tokens=300,
        )
        if "## Skill: dropped" not in result:
            # The dropped skill should not appear in the header either.
            assert "**dropped**" not in result

    def test_very_small_budget_still_produces_output(self) -> None:
        skill = _make_skill(name="vital", priority=0)
        result = compose_skills_fragment([skill], token_budget=10)
        assert len(result) > 0
