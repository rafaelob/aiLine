"""Shared data-loading utilities for curriculum JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...domain.entities.curriculum import CurriculumObjective, CurriculumSystem

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "curriculum"


def load_objectives_from_json(filename: str) -> list[CurriculumObjective]:
    """Load curriculum objectives from a JSON data file.

    Args:
        filename: Name of the JSON file inside ``data/curriculum/``.

    Returns:
        Parsed list of ``CurriculumObjective`` instances.

    Raises:
        FileNotFoundError: When the data file does not exist.
        ValueError: When JSON content cannot be parsed into valid objectives.
    """
    filepath = _DATA_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Curriculum data file not found: {filepath}")

    raw: list[dict[str, Any]] = json.loads(filepath.read_text(encoding="utf-8"))
    objectives: list[CurriculumObjective] = []
    for entry in raw:
        objectives.append(
            CurriculumObjective(
                code=entry["code"],
                system=CurriculumSystem(entry["system"]),
                subject=entry["subject"],
                grade=entry["grade"],
                domain=entry.get("domain", ""),
                description=entry["description"],
                keywords=entry.get("keywords", []),
                bloom_level=entry.get("bloom_level"),
            )
        )
    return objectives


def load_grade_mapping() -> dict[str, Any]:
    """Load the Brazil <-> US grade equivalency mapping.

    Returns:
        Parsed dict with ``mappings`` list and optional ``kindergarten`` entry.
    """
    filepath = _DATA_DIR / "grade_mapping.json"
    if not filepath.exists():
        raise FileNotFoundError(f"Grade mapping file not found: {filepath}")
    return json.loads(filepath.read_text(encoding="utf-8"))


def text_matches(query: str, text: str) -> bool:
    """Case-insensitive substring match."""
    return query.lower() in text.lower()


def keyword_matches(query: str, objective: CurriculumObjective) -> bool:
    """Check if *query* appears in keywords or description (case-insensitive)."""
    q = query.lower()
    for kw in objective.keywords:
        if q in kw.lower():
            return True
    return q in objective.description.lower()
