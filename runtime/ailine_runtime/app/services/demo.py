"""Demo mode service -- cached golden path responses for reliable demos.

Loads curated scenario JSON files from data/demo/ and provides them
via a simple in-memory lookup. Used by the demo router and middleware
to bypass real pipeline execution during hackathon presentations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger("ailine.services.demo")

_DEMO_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "demo"


class DemoService:
    """Provides cached golden path responses for demo mode.

    Scenarios are loaded once at construction from JSON files in
    the demo data directory. Each file must contain an ``id`` field
    used as the lookup key.
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        self._data_dir = data_dir or _DEMO_DATA_DIR
        self._scenarios: dict[str, dict[str, Any]] = {}
        self._load_scenarios()

    def _load_scenarios(self) -> None:
        """Load all scenario JSON files from the data directory."""
        if not self._data_dir.is_dir():
            logger.warning("demo_data_dir_missing", path=str(self._data_dir))
            return

        loaded = 0
        for fpath in sorted(self._data_dir.glob("*.json")):
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
                scenario_id = data.get("id")
                if not scenario_id:
                    logger.warning("demo_scenario_no_id", file=fpath.name)
                    continue
                self._scenarios[scenario_id] = data
                loaded += 1
            except (json.JSONDecodeError, OSError) as exc:
                logger.error("demo_scenario_load_error", file=fpath.name, error=str(exc))

        logger.info("demo_scenarios_loaded", count=loaded)

    @property
    def scenario_count(self) -> int:
        """Number of loaded scenarios."""
        return len(self._scenarios)

    def list_scenarios(self) -> list[dict[str, Any]]:
        """Return summary list of all available demo scenarios."""
        summaries: list[dict[str, Any]] = []
        for s in self._scenarios.values():
            item: dict[str, Any] = {
                "id": s["id"],
                "title": s["title"],
                "description": s["description"],
            }
            for optional in ("grade", "subject", "locale", "expected_skills", "demo_tags"):
                if optional in s:
                    item[optional] = s[optional]
            summaries.append(item)
        return summaries

    def reset(self) -> None:
        """Clear and reload all scenario data (for demo reset)."""
        self._scenarios.clear()
        self._load_scenarios()

    def get_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        """Return full scenario data by ID, or None if not found."""
        return self._scenarios.get(scenario_id)

    def get_cached_plan(self, scenario_id: str) -> dict[str, Any] | None:
        """Return the pre-computed lesson plan for a scenario."""
        scenario = self._scenarios.get(scenario_id)
        if scenario:
            return scenario.get("cached_plan")
        return None

    def get_cached_events(self, scenario_id: str) -> list[dict[str, Any]]:
        """Return the list of simulated SSE events for a scenario."""
        scenario = self._scenarios.get(scenario_id)
        if scenario:
            events: list[dict[str, Any]] = scenario.get("cached_events", [])
            return events
        return []

    def get_score(self, scenario_id: str) -> int | None:
        """Return the quality score for a scenario."""
        scenario = self._scenarios.get(scenario_id)
        if scenario:
            return scenario.get("score")
        return None

    def get_prompt(self, scenario_id: str) -> str | None:
        """Return the original prompt for a scenario."""
        scenario = self._scenarios.get(scenario_id)
        if scenario:
            return scenario.get("prompt")
        return None
