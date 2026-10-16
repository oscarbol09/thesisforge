"""Unit tests for configuration loading and validation."""

from pathlib import Path

import pytest

from thesisforge.config import AppSettings, load_yaml_config
from thesisforge.exceptions import ConfigurationError


def test_default_app_settings(monkeypatch: pytest.MonkeyPatch):
    """Test default settings instantiation."""
    monkeypatch.delenv("THESISFORGE_ENVIRONMENT", raising=False)
    settings = AppSettings()
    assert settings.app_name == "ThesisForge"
    assert settings.environment == "development"
    assert settings.port == 8000
    assert settings.default_provider == "openrouter"
    assert settings.rag.chunk_size == 1500
    assert settings.rag.evidence_candidate_threshold == 0.25
    assert settings.rag.evidence_support_threshold == 0.40


def test_load_yaml_config_non_existent():
    """Test loading a non-existent YAML returns empty dict."""
    result = load_yaml_config("non_existent_file_12345.yaml")
    assert result == {}


def test_load_yaml_config_valid(tmp_path: Path):
    """Test loading valid YAML configuration."""
    yaml_file = tmp_path / "test_config.yaml"
    yaml_file.write_text(
        """
providers:
  default_provider: "gemini"
  default_model: "gemini-2.0-flash"
  timeout_seconds: 45
rag:
  chunk_size: 1000
  chunk_overlap: 150
  evidence_candidate_threshold: 0.30
  evidence_support_threshold: 0.50
""",
        encoding="utf-8",
    )

    data = load_yaml_config(yaml_file)
    assert data["providers"]["default_provider"] == "gemini"
    assert data["rag"]["chunk_size"] == 1000
    assert data["rag"]["evidence_candidate_threshold"] == 0.30
    assert data["rag"]["evidence_support_threshold"] == 0.50


def test_load_yaml_config_malformed(tmp_path: Path):
    """Test loading malformed YAML raises ConfigurationError."""
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("providers: [unclosed list", encoding="utf-8")

    with pytest.raises(ConfigurationError):
        load_yaml_config(bad_yaml)


def test_get_settings_integration():
    """Test get_settings merges YAML defaults appropriately."""
    from thesisforge.config import get_settings

    settings = get_settings("config.yaml.example")
    assert settings.app_name == "ThesisForge"
    assert "openrouter" in settings.providers
    assert settings.rag.chunk_size == 1500
    assert settings.rag.evidence_candidate_threshold == 0.25
    assert settings.rag.evidence_support_threshold == 0.40
    assert settings.rag.embedding_provider == "fast_local"
    assert settings.rag.academic_apis.get("openalex") is True


def test_get_settings_fallback_warning(caplog: pytest.LogCaptureFixture):
    """Test get_settings logs a warning when falling back to config.yaml.example."""
    import logging

    from thesisforge.config import get_settings

    get_settings.cache_clear()
    with caplog.at_level(logging.WARNING):
        settings = get_settings("non_existent_config_file_9999.yaml")
        assert settings is not None
        assert "cargando configuración predeterminada desde 'config.yaml.example'" in caplog.text
    get_settings.cache_clear()


def test_get_settings_parses_app_metadata_and_max_retries(tmp_path: Path):
    """Test get_settings properly parses app metadata (name, language, theme) and max_retries (TF-CONFIG-001)."""
    from thesisforge.config import get_settings

    custom_yaml = tmp_path / "custom_config.yaml"
    custom_yaml.write_text(
        """
app:
  name: "CustomForge"
  language: "en"
  theme: "dark"

providers:
  default_provider: "groq"
  default_model: "llama-3.3-70b-versatile"
  timeout_seconds: 90
  max_retries: 5
""",
        encoding="utf-8",
    )

    get_settings.cache_clear()
    settings = get_settings(str(custom_yaml))
    assert settings.app_name == "CustomForge"
    assert settings.language == "en"
    assert settings.theme == "dark"
    assert settings.default_provider == "groq"
    assert settings.timeout_seconds == 90
    assert settings.max_retries == 5
    get_settings.cache_clear()
