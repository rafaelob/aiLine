"""Tests for shared.config -- Pydantic Settings-based configuration."""

from __future__ import annotations

import os
from unittest.mock import patch


class TestLLMConfig:
    def test_defaults(self):
        from ailine_runtime.shared.config import LLMConfig

        # Clear env vars that may override LLM defaults (e.g., Docker sets AILINE_LLM_PROVIDER).
        clean_env = {
            k: v for k, v in os.environ.items() if not k.startswith("AILINE_LLM_")
        }
        with patch.dict(os.environ, clean_env, clear=True):
            cfg = LLMConfig()
            assert cfg.provider == "anthropic"
            assert cfg.model == "claude-opus-4-6"
            assert cfg.api_key == ""

    def test_env_override(self):
        from ailine_runtime.shared.config import LLMConfig

        with patch.dict(
            os.environ, {"AILINE_LLM_PROVIDER": "openai", "AILINE_LLM_MODEL": "gpt-4o"}
        ):
            cfg = LLMConfig()
            assert cfg.provider == "openai"
            assert cfg.model == "gpt-4o"


class TestEmbeddingConfig:
    def test_defaults(self):
        from ailine_runtime.shared.config import EmbeddingConfig

        # Build a clean env snapshot without AILINE_EMBEDDING_* keys so
        # pydantic-settings falls back to the field defaults.
        clean_env = {
            k: v for k, v in os.environ.items() if not k.startswith("AILINE_EMBEDDING_")
        }
        with patch.dict(os.environ, clean_env, clear=True):
            cfg = EmbeddingConfig()
            assert cfg.provider == "gemini"
            assert cfg.model == "gemini-embedding-001"
            assert cfg.dimensions == 1536

    def test_env_override(self):
        from ailine_runtime.shared.config import EmbeddingConfig

        with patch.dict(
            os.environ,
            {
                "AILINE_EMBEDDING_PROVIDER": "openai",
                "AILINE_EMBEDDING_DIMENSIONS": "1536",
            },
        ):
            cfg = EmbeddingConfig()
            assert cfg.provider == "openai"
            assert cfg.dimensions == 1536


class TestDatabaseConfig:
    def test_defaults(self):
        from ailine_runtime.shared.config import DatabaseConfig

        # Clear env vars that may override defaults (e.g., AILINE_DB_URL inside Docker).
        clean_env = {
            k: v for k, v in os.environ.items() if not k.startswith("AILINE_DB_")
        }
        with patch.dict(os.environ, clean_env, clear=True):
            cfg = DatabaseConfig()
            assert "sqlite" in cfg.url
            assert cfg.pool_size == 10
            assert cfg.echo is False


class TestSettings:
    def test_defaults(self):
        from ailine_runtime.shared.config import Settings

        settings = Settings()
        assert settings.planner_model == "anthropic:claude-opus-4-6"
        assert settings.max_refinement_iters == 2
        assert settings.demo_mode is False
        assert settings.default_locale == "pt-BR"
        assert settings.enable_exports is True

    def test_env_override(self):
        from ailine_runtime.shared.config import Settings

        with patch.dict(
            os.environ, {"AILINE_DEMO_MODE": "true", "AILINE_MAX_REFINEMENT_ITERS": "5"}
        ):
            settings = Settings()
            assert settings.demo_mode is True
            assert settings.max_refinement_iters == 5

    def test_api_key_aliases(self):
        from ailine_runtime.shared.config import Settings

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-123"}):
            settings = Settings()
            assert settings.anthropic_api_key == "sk-test-123"

    def test_sub_configs_instantiate(self):
        from ailine_runtime.shared.config import Settings

        settings = Settings()
        assert settings.llm.provider == "anthropic"
        assert settings.embedding.provider == "gemini"
        assert settings.vectorstore.provider == "pgvector"
        assert settings.db.pool_size == 10
        assert "redis" in settings.redis.url


class TestGetSettings:
    def test_singleton(self):
        import ailine_runtime.shared.config as config_mod

        # Reset singleton
        config_mod._settings = None
        s1 = config_mod.get_settings()
        s2 = config_mod.get_settings()
        assert s1 is s2
        # Cleanup
        config_mod._settings = None
