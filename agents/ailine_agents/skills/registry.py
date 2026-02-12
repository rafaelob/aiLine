"""SkillDefinition model and SkillRegistry for loading/querying skills."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class SkillDefinition(BaseModel):
    """A parsed skill with frontmatter metadata and markdown instructions."""

    name: str
    description: str = ""
    instructions: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillRegistry:
    """Load, index, and query skills from one or more directories."""

    def __init__(self) -> None:
        self._skills: dict[str, SkillDefinition] = {}

    @property
    def skills(self) -> dict[str, SkillDefinition]:
        return dict(self._skills)

    def scan(self, directory: str | Path) -> int:
        """Scan a directory for skill folders containing SKILL.md.

        Returns the number of skills loaded from this directory.
        """
        from .loader import parse_skill_md

        root = Path(directory)
        if not root.is_dir():
            return 0

        count = 0
        for skill_md in sorted(root.glob("*/SKILL.md")):
            try:
                skill = parse_skill_md(skill_md)
                self._skills[skill.name] = skill
                count += 1
            except (ValueError, OSError):
                continue
        return count

    def scan_paths(self, paths: list[str] | None = None) -> int:
        """Scan multiple directories. If paths is None, use default skill sources."""
        if paths is None:
            from ailine_runtime.skills.paths import get_skill_source_paths

            paths = get_skill_source_paths()

        total = 0
        for p in paths:
            total += self.scan(p)
        return total

    def get_by_name(self, name: str) -> SkillDefinition | None:
        return self._skills.get(name)

    def list_names(self) -> list[str]:
        return sorted(self._skills.keys())

    def get_prompt_fragment(self, skill_names: list[str]) -> str:
        """Build a combined system prompt fragment from the requested skills.

        Each skill contributes its description + full markdown instructions.
        Skills not found in the registry are silently skipped.
        """
        parts: list[str] = []
        for name in skill_names:
            skill = self._skills.get(name)
            if skill is None:
                continue
            header = f"## Skill: {skill.name}"
            if skill.description:
                header += f"\n{skill.description}"
            parts.append(f"{header}\n\n{skill.instructions}")

        if not parts:
            return ""
        return "\n\n---\n\n".join(parts)
