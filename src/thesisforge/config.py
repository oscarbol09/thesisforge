"""Configuration management using Pydantic Settings and YAML loader."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from thesisforge.exceptions import ConfigurationError


class ProviderSettings(BaseModel):
    """Configuration for a specific LLM provider."""

    model_config = ConfigDict(extra="ignore")

    enabled: bool = True
    base_url: str | None = None
    models: list[str] = Field(default_factory=list)


class RAGSettings(BaseModel):
    """Configuration for RAG indexing and search."""

    model_config = ConfigDict(extra="ignore")

    chunk_size: int = 1500
    chunk_overlap: int = 200
    top_k_citations: int = 5
    similarity_threshold: float = 0.72
    cache_ttl_hours: int = 48
    chroma_dir: str = "data/chroma"
    evidence_candidate_threshold: float = 0.25
    evidence_support_threshold: float = 0.40
    academic_apis: dict[str, bool] = Field(
        default_factory=lambda: {
            "semantic_scholar": True,
            "arxiv": True,
            "crossref": True,
        }
    )


class AppSettings(BaseSettings):
    """Master application settings loaded from environment and YAML."""

    model_config = SettingsConfigDict(
        env_prefix="THESISFORGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Application Settings
    app_name: str = "ThesisForge"
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    master_key: str | None = None
    database_url: str = "sqlite+aiosqlite:///./thesisforge.db"

    # Default LLM BYOK settings
    default_provider: str = "openrouter"
    default_model: str = "anthropic/claude-3.5-sonnet"
    timeout_seconds: int = 60
    max_retries: int = 3

    # Provider configs
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    nvidia_nim_api_key: str | None = Field(default=None, alias="NVIDIA_NIM_API_KEY")
    semantic_scholar_api_key: str | None = Field(default=None, alias="SEMANTIC_SCHOLAR_API_KEY")
    crossref_mailto: str = Field(default="thesisforge@academic.org", alias="CROSSREF_MAILTO")

    # Web GUI & Static Assets
    gui_dir: str = "gui"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:3000",
        ]
    )

    # Nested sub-configs
    rag: RAGSettings = Field(default_factory=RAGSettings)
    providers: dict[str, ProviderSettings] = Field(default_factory=dict)


def load_yaml_config(yaml_path: Path | str) -> dict[str, Any]:
    """Safely load and parse YAML configuration file."""
    path = Path(yaml_path)
    if not path.is_file():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            content = yaml.safe_load(f)
            return content if isinstance(content, dict) else {}
    except yaml.YAMLError as err:
        raise ConfigurationError(f"Error parseando archivo YAML '{path}': {err}") from err


@lru_cache(maxsize=1)
def get_settings(config_yaml_path: str = "config.yaml") -> AppSettings:
    """Obtain cached AppSettings instance merged with optional YAML overrides."""
    base_settings = AppSettings()
    yaml_data = load_yaml_config(config_yaml_path)
    if not yaml_data:
        yaml_data = load_yaml_config("config.yaml.example")

    if yaml_data:
        # Merge RAG settings if present
        if "rag" in yaml_data and isinstance(yaml_data["rag"], dict):
            base_settings.rag = RAGSettings.model_validate(yaml_data["rag"])

        # Merge Providers settings if present
        if "providers" in yaml_data and isinstance(yaml_data["providers"], dict):
            providers_dict = yaml_data["providers"]
            if "default_provider" in providers_dict:
                base_settings.default_provider = str(providers_dict["default_provider"])
            if "default_model" in providers_dict:
                base_settings.default_model = str(providers_dict["default_model"])
            if "timeout_seconds" in providers_dict:
                base_settings.timeout_seconds = int(providers_dict["timeout_seconds"])

            for p_name, p_data in providers_dict.items():
                if isinstance(p_data, dict):
                    base_settings.providers[p_name] = ProviderSettings.model_validate(p_data)

    return base_settings
