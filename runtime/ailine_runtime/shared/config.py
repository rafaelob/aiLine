from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AILINE_LLM_")
    provider: Literal["anthropic", "openai", "gemini", "openrouter", "fake"] = (
        "anthropic"
    )
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
    provider: Literal["pgvector", "chroma"] = "pgvector"


class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AILINE_DB_")
    url: str = "sqlite+aiosqlite:///./dev.db"
    pool_size: int = 10
    max_overflow: int = 10
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
    anthropic_api_key: str = Field(
        "",
        validation_alias=AliasChoices("ANTHROPIC_API_KEY", "AILINE_ANTHROPIC_API_KEY"),
    )
    openai_api_key: str = Field(
        "", validation_alias=AliasChoices("OPENAI_API_KEY", "AILINE_OPENAI_API_KEY")
    )
    google_api_key: str = Field(
        "", validation_alias=AliasChoices("GOOGLE_API_KEY", "AILINE_GOOGLE_API_KEY")
    )
    openrouter_api_key: str = Field(
        "",
        validation_alias=AliasChoices(
            "OPENROUTER_API_KEY", "AILINE_OPENROUTER_API_KEY"
        ),
    )

    # Sub-configs
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    vectorstore: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    db: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)

    # Pipeline — all model IDs use Pydantic AI format: "provider:model-name"
    planner_model: str = "anthropic:claude-opus-4-6"
    executor_model: str = "google-gla:gemini-3-flash-preview"
    qg_model: str = "anthropic:claude-sonnet-4-5"
    tutor_model: str = "anthropic:claude-sonnet-4-5"
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

        return parse_skill_source_paths(
            self.skill_sources if self.skill_sources else None
        )

    def validate_environment(self) -> list[str]:
        """Validate that critical environment variables are set for the current env.

        Returns a list of validation errors. In production, raises
        ``OSError`` if any critical variable is missing.
        In dev/test, returns warnings as a list.

        Production requirements:
        - DB URL must NOT be SQLite
        - At least one LLM API key must be set
        - JWT key material must be configured

        Always:
        - DB URL must be set (non-empty)
        """
        errors: list[str] = []
        warnings: list[str] = []
        is_prod = self.env == "production"

        # DB URL always required
        if not self.db.url:
            errors.append("AILINE_DB__URL is required")

        if is_prod:
            # Production must not use SQLite
            if "sqlite" in self.db.url.lower():
                errors.append(
                    "SQLite is not allowed in production. Set AILINE_DB__URL to a PostgreSQL connection string."
                )

            # At least one LLM API key in production
            has_llm_key = any(
                [
                    self.anthropic_api_key,
                    self.openai_api_key,
                    self.google_api_key,
                    self.openrouter_api_key,
                ]
            )
            if not has_llm_key:
                errors.append(
                    "At least one LLM API key is required in production. "
                    "Set ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, "
                    "or OPENROUTER_API_KEY."
                )

            # JWT key material in production
            import os

            jwt_secret = os.getenv("AILINE_JWT_SECRET", "")
            jwt_public_key = os.getenv("AILINE_JWT_PUBLIC_KEY", "")
            if not jwt_secret and not jwt_public_key:
                errors.append(
                    "JWT key material is required in production. "
                    "Set AILINE_JWT_SECRET (HS256) or "
                    "AILINE_JWT_PUBLIC_KEY (RS256/ES256)."
                )

        if errors and is_prod:
            raise OSError(
                "Production environment validation failed:\n"
                + "\n".join(f"  - {e}" for e in errors)
            )

        return errors + warnings


_settings: Settings | None = None
_settings_lock = __import__("threading").Lock()


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        with _settings_lock:
            if _settings is None:
                _settings = Settings()  # type: ignore[call-arg]  # pydantic validation_alias vs mypy
    return _settings
