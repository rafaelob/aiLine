from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .token_count import TokenCounter


@dataclass(frozen=True)
class SkillMeta:
    name: str
    description: str
    path: Path


class SkillsRegistry:
    """Loads Skill metadata at startup; loads full SKILL.md on activation.

    This implements *progressive disclosure*:
      - Discovery: read only YAML frontmatter (name, description).
      - Activation: load full SKILL.md (optionally chunked).
    """
    def __init__(self, skills_dir: Path, token_counter: TokenCounter) -> None:
        self.skills_dir = skills_dir
        self.token_counter = token_counter
        self._meta_by_name: dict[str, SkillMeta] = {}

    @staticmethod
    def _parse_frontmatter(text: str) -> dict[str, str]:
        # Minimal YAML-ish parser: key: value per line, only in frontmatter block.
        if not text.startswith("---"):
            return {}
        parts = text.split("\n")
        # find second '---'
        try:
            end = parts[1:].index("---") + 1
        except ValueError:
            return {}
        fm_lines = parts[1:end]
        out: dict[str, str] = {}
        for line in fm_lines:
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
        return out

    def discover(self) -> None:
        """Scan skills_dir for */SKILL.md and cache metadata."""
        self._meta_by_name.clear()
        if not self.skills_dir.exists():
            return
        for skill_md in self.skills_dir.glob("*/SKILL.md"):
            txt = skill_md.read_text(encoding="utf-8")
            fm = self._parse_frontmatter(txt)
            name = fm.get("name") or skill_md.parent.name
            desc = fm.get("description", "").strip()
            self._meta_by_name[name] = SkillMeta(name=name, description=desc, path=skill_md.parent)

    def list_skills(self) -> list[SkillMeta]:
        return sorted(self._meta_by_name.values(), key=lambda s: s.name.lower())

    def build_index_snippet(self, max_tokens: int) -> str:
        """Return a compact catalog of skills to include in the core context."""
        lines = ["## SKILLS_INDEX", "(progressive disclosure: carregue SKILL.md completo apenas quando ativar)\n"]
        for s in self.list_skills():
            lines.append(f"- {s.name}: {s.description}")
        text = "\n".join(lines).strip()
        # Enforce budget.
        if self.token_counter.count_text(text) <= max_tokens:
            return text
        # Trim by dropping the tail.
        trimmed: list[str] = lines[:2]
        for line in lines[2:]:
            candidate = "\n".join(trimmed + [line])
            if self.token_counter.count_text(candidate) > max_tokens:
                break
            trimmed.append(line)
        trimmed.append("\n(… catálogo truncado por budget …)")
        return "\n".join(trimmed)

    def load_skill_md(self, name: str) -> str:
        meta = self._meta_by_name.get(name)
        if not meta:
            raise KeyError(f"Skill not found: {name}")
        return (meta.path / "SKILL.md").read_text(encoding="utf-8")

    def activate(self, name: str, max_tokens: int, sections: Optional[list[str]] = None) -> str:
        """Load full (or chunked) SKILL.md for an active skill.

        If `sections` is provided, tries to include only headings matching those strings.
        """
        full = self.load_skill_md(name)
        if sections:
            chunk = self._select_sections(full, sections)
        else:
            chunk = full

        if self.token_counter.count_text(chunk) <= max_tokens:
            return chunk

        # Hard truncate. In production, prefer summarizing or selecting smaller sections.
        char_budget = int(max_tokens * self.token_counter.chars_per_token)
        return chunk[:char_budget] + "\n\n(… SKILL.md truncado por budget …)\n"

    @staticmethod
    def _select_sections(markdown: str, section_titles: list[str]) -> str:
        """Naive section selector: keeps headings that contain any of the titles (case-insensitive)."""
        wanted = [t.lower() for t in section_titles]
        lines = markdown.splitlines()
        out: list[str] = []
        keep = True  # keep frontmatter / intro by default
        for line in lines:
            if line.strip().startswith("#"):
                h = line.strip("# ").lower()
                keep = any(w in h for w in wanted)
            if keep:
                out.append(line)
        return "\n".join(out).strip()
