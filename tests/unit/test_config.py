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
