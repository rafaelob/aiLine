from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AILINE_LLM_")
    provider: Literal["anthropic", "openai", "gemini", "openrouter", "fake"] = "anthropic"
    model: str = "claude-opus-4-6"
    api_key: str = ""


class EmbeddingConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AILINE_EMBEDDING_")
    provider: Literal["gemini", "openai", "local", "openrouter"] = "gemini"
    model: str = "gemini-embedding-001"
    dimensions: int = 1536
    api_key: str = ""
    batch_size: int = 100
    """Max embeddings per API call. Controls chunking of large embed requests
    to avoid provider timeouts and memory pressure. Typical provider limits:
    Gemini=100, OpenAI=2048. Use a conservative default."""


class VectorStoreConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AILINE_VECTORSTORE_")
    provider: Literal["pgvector", "qdrant", "chroma"] = "pgvector"


class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AILINE_DB_")
    url: str = "sqlite+aiosqlite:///./dev.db"
    pool_size: int = 5
    max_overflow: int = 5
    echo: bool = False


class RedisConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AILINE_REDIS_")
    url: str = "redis://localhost:6379/0"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AILINE_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API keys (top-level for convenience; accept both ANTHROPIC_API_KEY and AILINE_ANTHROPIC_API_KEY)
    anthropic_api_key: str = Field("", validation_alias=AliasChoices("ANTHROPIC_API_KEY", "AILINE_ANTHROPIC_API_KEY"))
    openai_api_key: str = Field("", validation_alias=AliasChoices("OPENAI_API_KEY", "AILINE_OPENAI_API_KEY"))
    google_api_key: str = Field("", validation_alias=AliasChoices("GOOGLE_API_KEY", "AILINE_GOOGLE_API_KEY"))
    openrouter_api_key: str = Field(
        "", validation_alias=AliasChoices("OPENROUTER_API_KEY", "AILINE_OPENROUTER_API_KEY")
    )

    # Sub-configs
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    vectorstore: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    db: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)

    # Pipeline
    planner_model: str = "claude-opus-4-6"
    executor_model: str = "claude-opus-4-6"
    planner_effort: str = "high"
    max_refinement_iters: int = 2

    # Local store (MVP fallback)
    local_store: str = ".local_store"

    # Skills
    skill_sources: str = ""
    planner_use_skills: bool = True
    persona_use_skills: bool = True

    # Exports
    enable_exports: bool = True
    default_variants: str = (
        "standard_html,low_distraction_html,large_print_html,high_contrast_html,"
        "dyslexia_friendly_html,screen_reader_html,visual_schedule_html,student_plain_text,audio_script"
    )

    # Environment (development | staging | production)
    env: Literal["development", "staging", "production"] = "development"

    # Demo
    demo_mode: bool = False

    # i18n
    default_locale: str = "pt-BR"

    def skill_source_paths(self) -> list[str]:
        from ..skills.paths import parse_skill_source_paths

        return parse_skill_source_paths(self.skill_sources if self.skill_sources else None)


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]  # pydantic validation_alias vs mypy
    return _settings
