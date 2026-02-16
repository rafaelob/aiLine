from __future__ import annotations

import os
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """Best-effort repo root discovery.

    We look for a directory that contains:
      - docs/
      - runtime/
    """
    here = (start or Path(__file__)).resolve()
    for p in [here, *here.parents]:
        if (p / "docs").is_dir() and (p / "runtime").is_dir():
            return p
    # Fallback: assume standard layout ailine/runtime/ailine_runtime/skills/paths.py
    # In Docker, the path may be too shallow -- guard against IndexError.
    depth = 4
    if len(here.parents) > depth:
        return here.parents[depth]
    return here.parents[-1] if here.parents else here


def default_skill_source_paths(repo_root: Path | None = None) -> list[str]:
    root = repo_root or find_repo_root()
    candidates = [
        root / ".claude" / "skills",
        root / "skills",
    ]
    return [c.as_posix() for c in candidates if c.is_dir()]


def parse_skill_source_paths(
    raw: str | None, repo_root: Path | None = None
) -> list[str]:
    """Parse AILINE_SKILL_SOURCES env var.

    Format: comma-separated paths. Paths should be POSIX style, but we normalize '\\' to '/'.
    If not provided, returns default paths (.claude/skills and skills/ if they exist).
    """
    if raw and raw.strip():
        parts = [p.strip() for p in raw.split(",")]
        return [p.replace("\\", "/") for p in parts if p]
    return default_skill_source_paths(repo_root=repo_root)


def get_skill_source_paths() -> list[str]:
    return parse_skill_source_paths(os.getenv("AILINE_SKILL_SOURCES"))
