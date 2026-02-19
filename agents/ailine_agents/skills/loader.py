"""Parse SKILL.md files: YAML frontmatter + markdown body."""

from __future__ import annotations

import re
from pathlib import Path

import yaml  # type: ignore[import-untyped]  # types-PyYAML not installed in agents env

from .registry import SkillDefinition

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_skill_md(path: Path) -> SkillDefinition:
    """Parse a SKILL.md file into a SkillDefinition.

    Expected format:
        ---
        name: skill-name
        description: ...
        metadata:
          version: ...
          ...
        ---
        # Markdown body (instructions)
    """
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"No YAML frontmatter found in {path}")

    raw_yaml = yaml.safe_load(match.group(1))
    if not isinstance(raw_yaml, dict):
        raise ValueError(f"Frontmatter is not a YAML mapping in {path}")

    name = raw_yaml.get("name", path.parent.name)
    description = raw_yaml.get("description", "")
    if isinstance(description, str):
        description = description.strip()

    raw_metadata = raw_yaml.get("metadata", {})
    if not isinstance(raw_metadata, dict):
        raw_metadata = {}

    # Legacy fields that should live under metadata
    legacy_fields = (
        "version",
        "compatible_runtimes",
        "compatible_providers",
        "recommended_models",
        "optional_models",
        "compatibility",
    )
    for field in legacy_fields:
        if field in raw_yaml and field not in raw_metadata:
            raw_metadata[field] = raw_yaml[field]

    # Enforce dict[str, str] per agentskills.io spec
    metadata: dict[str, str] = {
        str(k): str(v) if not isinstance(v, str) else v
        for k, v in raw_metadata.items()
    }

    body = text[match.end() :].strip()

    return SkillDefinition(
        name=name,
        description=description,
        instructions=body,
        metadata=metadata,
    )
