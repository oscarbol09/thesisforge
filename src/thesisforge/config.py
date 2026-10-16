"""Configuration management using Pydantic Settings and YAML loader."""

from functools import lru_cache
from pathlib import Path
from typing import Any, ClassVar

import yaml
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from thesisforge.core.logging import get_logger
from thesisforge.exceptions import ConfigurationError

logger = get_logger(__name__)


class YamlDictSettingsSource(PydanticBaseSettingsSource):
    """Custom settings source that provides values loaded from config.yaml (TF-CONFIG-001-R1)."""

    def __init__(
        self,
        settings_cls: type[BaseSettings],
        data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(settings_cls)
        self.data = data or {}

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        return self.data.get(field_name), field_name, False

    def __call__(self) -> dict[str, Any]:
        return self.data


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
    embedding_provider: str = "fast_local"
    academic_apis: dict[str, bool] = Field(
        default_factory=lambda: {
            "semantic_scholar": True,
            "arxiv": True,
            "crossref": True,
            "openalex": True,
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

    _active_yaml_data: ClassVar[dict[str, Any]] = {}

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Precedence: defaults < config.yaml < .env < environment variables < explicit code kwargs (TF-CONFIG-001-R1)
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlDictSettingsSource(settings_cls, cls._active_yaml_data),
            file_secret_settings,
        )

    # Core Application Settings
    app_name: str = "ThesisForge"
    language: str = "es"
    theme: str = "system"
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

    # Instance authentication (local-first)
    # Set THESISFORGE_INSTANCE_TOKEN to a secret string to require Bearer auth on all API routes.
    # Leave empty to disable auth (default: dev mode only; always set in Docker/network deployments).
    instance_token: str | None = Field(default=None, alias="THESISFORGE_INSTANCE_TOKEN")
    auth_disabled: bool = False  # Only honoured when environment == "development"

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
    """Obtain cached AppSettings instance merged with optional YAML overrides.

    Follows strict precedence: defaults < config.yaml < environment variables (TF-CONFIG-001-R1).
    """
    yaml_data = load_yaml_config(config_yaml_path)
    if not yaml_data:
        yaml_data = load_yaml_config("config.yaml.example")
        if yaml_data:
            logger.warning(
                "No se encontró '%s'; cargando configuración predeterminada desde 'config.yaml.example'.",
                config_yaml_path,
            )

    yaml_kwargs: dict[str, Any] = {}
    if yaml_data:
        # Merge App metadata settings if present (TF-CONFIG-001)
        if "app" in yaml_data and isinstance(yaml_data["app"], dict):
            app_dict = yaml_data["app"]
            if "name" in app_dict:
                yaml_kwargs["app_name"] = str(app_dict["name"])
            if "language" in app_dict:
                yaml_kwargs["language"] = str(app_dict["language"])
            if "theme" in app_dict:
                yaml_kwargs["theme"] = str(app_dict["theme"])

        # Merge RAG settings if present
        if "rag" in yaml_data and isinstance(yaml_data["rag"], dict):
            yaml_kwargs["rag"] = RAGSettings.model_validate(yaml_data["rag"])

        # Merge Providers settings if present
        if "providers" in yaml_data and isinstance(yaml_data["providers"], dict):
            providers_dict = yaml_data["providers"]
            if "default_provider" in providers_dict:
                yaml_kwargs["default_provider"] = str(providers_dict["default_provider"])
            if "default_model" in providers_dict:
                yaml_kwargs["default_model"] = str(providers_dict["default_model"])
            if "timeout_seconds" in providers_dict:
                yaml_kwargs["timeout_seconds"] = int(providers_dict["timeout_seconds"])
            if "max_retries" in providers_dict:
                yaml_kwargs["max_retries"] = int(providers_dict["max_retries"])

            providers_map: dict[str, ProviderSettings] = {}
            for p_name, p_data in providers_dict.items():
                if isinstance(p_data, dict):
                    providers_map[p_name] = ProviderSettings.model_validate(p_data)
            if providers_map:
                yaml_kwargs["providers"] = providers_map

    AppSettings._active_yaml_data = yaml_kwargs
    return AppSettings()
