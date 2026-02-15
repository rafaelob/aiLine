"""Extended tests for config.py (legacy) -- covers skill_source_paths and get_config."""

from __future__ import annotations

import os


class TestAiLineConfig:
    def test_default_creation(self):
        from ailine_runtime.config import AiLineConfig

        cfg = AiLineConfig()
        # Env vars may override defaults; check against actual env or default
        expected_planner = os.getenv("AILINE_PLANNER_MODEL", "anthropic:claude-opus-4-6")
        expected_executor = os.getenv("AILINE_EXECUTOR_MODEL", "google-gla:gemini-3-flash-preview")
        assert cfg.planner_model == expected_planner
        assert cfg.executor_model == expected_executor
        assert cfg.max_refinement_iters == 2

    def test_skill_source_paths(self):
        from ailine_runtime.config import AiLineConfig

        cfg = AiLineConfig()
        paths = cfg.skill_source_paths()
        assert isinstance(paths, list)

    def test_skill_source_paths_from_env(self):
        from ailine_runtime.config import AiLineConfig

        cfg = AiLineConfig(skill_sources_env="/path/a,/path/b")
        paths = cfg.skill_source_paths()
        assert "/path/a" in paths
        assert "/path/b" in paths

    def test_get_config(self):
        from ailine_runtime.config import get_config

        cfg = get_config()
        assert cfg is not None
        # The default is ".local_store", but AILINE_LOCAL_STORE env var
        # may override it (e.g., "/app/.local_store" inside Docker).
        expected = os.getenv("AILINE_LOCAL_STORE", ".local_store")
        assert cfg.local_store_dir == expected
