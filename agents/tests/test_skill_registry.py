"""Tests for the skill registry: loading, parsing, querying."""

from __future__ import annotations

from pathlib import Path

import pytest

from ailine_agents.skills.loader import parse_skill_md
from ailine_agents.skills.registry import SkillDefinition, SkillRegistry

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_SKILL_MD = """\
---
name: test-skill
description: A test skill for unit testing.
metadata:
  version: "1.0.0"
  compatibility:
    runtimes: [langgraph]
    providers: [anthropic]
---

# Test Skill

You are a test skill. Follow these instructions.

## Rules
- Rule one
- Rule two
"""

LEGACY_SKILL_MD = """\
---
name: legacy-skill
description: Skill with old-style frontmatter fields.
version: 0.2.0
compatible_runtimes:
  - claude_code
  - langgraph
compatible_providers:
  - anthropic
recommended_models:
  - claude-opus-4-6
optional_models:
  - claude-sonnet-4-5-20250929
---

# Legacy Skill

Body content here.
"""

MINIMAL_SKILL_MD = """\
---
name: minimal
description: Minimal skill.
---

Just instructions.
"""

NO_FRONTMATTER = """\
# No Frontmatter

Just markdown, no YAML.
"""


@pytest.fixture()
def skill_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with sample skills."""
    # test-skill
    (tmp_path / "test-skill").mkdir()
    (tmp_path / "test-skill" / "SKILL.md").write_text(SAMPLE_SKILL_MD, encoding="utf-8")

    # legacy-skill
    (tmp_path / "legacy-skill").mkdir()
    (tmp_path / "legacy-skill" / "SKILL.md").write_text(LEGACY_SKILL_MD, encoding="utf-8")

    # minimal
    (tmp_path / "minimal").mkdir()
    (tmp_path / "minimal" / "SKILL.md").write_text(MINIMAL_SKILL_MD, encoding="utf-8")

    # no-frontmatter (should fail gracefully)
    (tmp_path / "bad-skill").mkdir()
    (tmp_path / "bad-skill" / "SKILL.md").write_text(NO_FRONTMATTER, encoding="utf-8")

    return tmp_path


# ---------------------------------------------------------------------------
# parse_skill_md tests
# ---------------------------------------------------------------------------


class TestParseSkillMd:
    def test_parse_standard(self, tmp_path: Path) -> None:
        path = tmp_path / "s" / "SKILL.md"
        path.parent.mkdir()
        path.write_text(SAMPLE_SKILL_MD, encoding="utf-8")

        skill = parse_skill_md(path)
        assert skill.name == "test-skill"
        assert "test skill for unit testing" in skill.description
        assert "# Test Skill" in skill.instructions
        assert "Rule one" in skill.instructions
        assert skill.metadata["version"] == "1.0.0"

    def test_parse_legacy_fields_migrate_to_metadata(self, tmp_path: Path) -> None:
        path = tmp_path / "s" / "SKILL.md"
        path.parent.mkdir()
        path.write_text(LEGACY_SKILL_MD, encoding="utf-8")

        skill = parse_skill_md(path)
        assert skill.name == "legacy-skill"
        assert skill.metadata["version"] == "0.2.0"
        assert "claude_code" in skill.metadata["compatible_runtimes"]
        assert "anthropic" in skill.metadata["compatible_providers"]
        assert "claude-opus-4-6" in skill.metadata["recommended_models"]
        assert "claude-sonnet-4-5-20250929" in skill.metadata["optional_models"]

    def test_parse_minimal(self, tmp_path: Path) -> None:
        path = tmp_path / "s" / "SKILL.md"
        path.parent.mkdir()
        path.write_text(MINIMAL_SKILL_MD, encoding="utf-8")

        skill = parse_skill_md(path)
        assert skill.name == "minimal"
        assert skill.description == "Minimal skill."
        assert "Just instructions." in skill.instructions

    def test_parse_no_frontmatter_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "s" / "SKILL.md"
        path.parent.mkdir()
        path.write_text(NO_FRONTMATTER, encoding="utf-8")

        with pytest.raises(ValueError, match="No YAML frontmatter"):
            parse_skill_md(path)


# ---------------------------------------------------------------------------
# SkillDefinition model tests
# ---------------------------------------------------------------------------


class TestSkillDefinition:
    def test_create_with_defaults(self) -> None:
        sd = SkillDefinition(name="x")
        assert sd.name == "x"
        assert sd.description == ""
        assert sd.instructions == ""
        assert sd.metadata == {}

    def test_create_with_fields(self) -> None:
        sd = SkillDefinition(
            name="my-skill",
            description="desc",
            instructions="# Hello",
            metadata={"version": "1.0"},
        )
        assert sd.name == "my-skill"
        assert sd.metadata["version"] == "1.0"


# ---------------------------------------------------------------------------
# SkillRegistry tests
# ---------------------------------------------------------------------------


class TestSkillRegistry:
    def test_scan_loads_valid_skills(self, skill_dir: Path) -> None:
        reg = SkillRegistry()
        loaded = reg.scan(skill_dir)
        # bad-skill should be skipped (no frontmatter)
        assert loaded == 3
        assert set(reg.list_names()) == {"test-skill", "legacy-skill", "minimal"}

    def test_scan_nonexistent_directory(self) -> None:
        reg = SkillRegistry()
        assert reg.scan("/nonexistent/path") == 0

    def test_get_by_name(self, skill_dir: Path) -> None:
        reg = SkillRegistry()
        reg.scan(skill_dir)
        skill = reg.get_by_name("test-skill")
        assert skill is not None
        assert skill.name == "test-skill"

    def test_get_by_name_missing(self, skill_dir: Path) -> None:
        reg = SkillRegistry()
        reg.scan(skill_dir)
        assert reg.get_by_name("nonexistent") is None

    def test_get_prompt_fragment(self, skill_dir: Path) -> None:
        reg = SkillRegistry()
        reg.scan(skill_dir)

        fragment = reg.get_prompt_fragment(["test-skill", "minimal"])
        assert "## Skill: test-skill" in fragment
        assert "## Skill: minimal" in fragment
        assert "---" in fragment  # separator between skills

    def test_get_prompt_fragment_empty(self, skill_dir: Path) -> None:
        reg = SkillRegistry()
        reg.scan(skill_dir)
        assert reg.get_prompt_fragment(["nonexistent"]) == ""

    def test_get_prompt_fragment_partial(self, skill_dir: Path) -> None:
        reg = SkillRegistry()
        reg.scan(skill_dir)
        fragment = reg.get_prompt_fragment(["test-skill", "nonexistent"])
        assert "## Skill: test-skill" in fragment
        assert "nonexistent" not in fragment

    def test_skills_property_returns_copy(self, skill_dir: Path) -> None:
        reg = SkillRegistry()
        reg.scan(skill_dir)
        copy = reg.skills
        assert len(copy) == 3
        copy["new"] = SkillDefinition(name="new")
        assert "new" not in reg.skills

    def test_scan_multiple_dirs(self, tmp_path: Path) -> None:
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        (dir_a / "skill-a").mkdir(parents=True)
        (dir_a / "skill-a" / "SKILL.md").write_text(
            "---\nname: skill-a\ndescription: A\n---\nBody A\n", encoding="utf-8"
        )
        (dir_b / "skill-b").mkdir(parents=True)
        (dir_b / "skill-b" / "SKILL.md").write_text(
            "---\nname: skill-b\ndescription: B\n---\nBody B\n", encoding="utf-8"
        )

        reg = SkillRegistry()
        total = reg.scan_paths([str(dir_a), str(dir_b)])
        assert total == 2
        assert set(reg.list_names()) == {"skill-a", "skill-b"}


# ---------------------------------------------------------------------------
# Integration: scan real skills directory
# ---------------------------------------------------------------------------


class TestRealSkillsDir:
    """Integration tests using the actual skills/ directory from the repo."""

    @pytest.fixture()
    def repo_skills_dir(self) -> Path:
        # Navigate to repo root from agents/tests/
        p = Path(__file__).resolve().parent.parent.parent / "skills"
        if not p.is_dir():
            pytest.skip("skills/ directory not found")
        return p

    def test_scan_real_skills(self, repo_skills_dir: Path) -> None:
        reg = SkillRegistry()
        loaded = reg.scan(repo_skills_dir)
        assert loaded >= 11  # we have 11 skills in the repo
        assert "lesson-planner" in reg.list_names()
        assert "socratic-tutor" in reg.list_names()
        assert "accessibility-coach" in reg.list_names()

    def test_planner_skills_fragment(self, repo_skills_dir: Path) -> None:
        reg = SkillRegistry()
        reg.scan(repo_skills_dir)
        fragment = reg.get_prompt_fragment(["lesson-planner", "accessibility-coach"])
        assert "## Skill: lesson-planner" in fragment
        assert "## Skill: accessibility-coach" in fragment
        assert "UDL" in fragment

    def test_tutor_skill_fragment(self, repo_skills_dir: Path) -> None:
        reg = SkillRegistry()
        reg.scan(repo_skills_dir)
        fragment = reg.get_prompt_fragment(["socratic-tutor"])
        assert "## Skill: socratic-tutor" in fragment
        assert "socrático" in fragment.lower() or "socratic" in fragment.lower()
