"""Unit tests for LLMRouter and BYOK provider management."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from thesisforge.config import AppSettings
from thesisforge.exceptions import LLMProviderError
from thesisforge.llm.router import LLMRouter
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.keystore_repository import SecureKeyStoreRepository


def test_normalize_model_name():
    """Test model routing prefix resolution."""
    router = LLMRouter()
    assert (
        router._normalize_model_name("claude-3.5-sonnet", "openrouter")
        == "openrouter/claude-3.5-sonnet"
    )
    assert router._normalize_model_name("gemini-2.0-flash", "gemini") == "gemini/gemini-2.0-flash"
    assert router._normalize_model_name("custom/model", "any") == "custom/model"


@pytest.mark.asyncio
async def test_resolve_api_key_from_settings():
    """Test resolving API key from AppSettings."""
    settings = AppSettings(
        OPENROUTER_API_KEY="mock-openrouter-env-key",
        GEMINI_API_KEY="mock-gemini-env-key",
    )
    router = LLMRouter(settings=settings)

    assert await router.resolve_api_key("openrouter") == "mock-openrouter-env-key"
    assert await router.resolve_api_key("gemini") == "mock-gemini-env-key"
    assert await router.resolve_api_key("unknown_provider") is None


@pytest.mark.asyncio
async def test_resolve_api_key_from_keystore_priority(
    in_memory_db: DatabaseManager, vault: MagicMock
):
    """Test that keystore repository takes priority over static settings."""
    keystore = SecureKeyStoreRepository(in_memory_db, vault)
    await keystore.store_key("openrouter", "mock-openrouter-database-key")

    settings = AppSettings(OPENROUTER_API_KEY="mock-openrouter-env-fallback")
    router = LLMRouter(settings=settings, keystore_repo=keystore)

    resolved = await router.resolve_api_key("openrouter")
    assert resolved == "mock-openrouter-database-key"


@pytest.mark.asyncio
async def test_complete_json_success():
    """Test successful JSON completion parsing."""
    router = LLMRouter()

    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = (
        '```json\n{"refined_problem": "Problema formalizado", "is_viable": true}\n```'
    )
    mock_resp.choices = [mock_choice]

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.return_value = mock_resp
        data = await router.complete_json("Prompt de prueba")

        assert data["refined_problem"] == "Problema formalizado"
        assert data["is_viable"] is True


@pytest.mark.asyncio
async def test_complete_json_with_conversational_preamble():
    """Test JSON completion parsing when response includes surrounding conversation."""
    router = LLMRouter()

    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = (
        "Claro, a continuación presento el JSON solicitado:\n"
        '```json\n{"verdict": "aprobado", "score": 92.5}\n```\n'
        "Espero que te sea de utilidad."
    )
    mock_resp.choices = [mock_choice]

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.return_value = mock_resp
        data = await router.complete_json("Prompt con preámbulo")

        assert data["verdict"] == "aprobado"
        assert data["score"] == 92.5


@pytest.mark.asyncio
async def test_complete_llm_error_handling():
    """Test LLM exception is wrapped into sanitized LLMProviderError without leaking raw secrets or URLs (TF-LLM-001)."""
    router = LLMRouter()

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.side_effect = RuntimeError(
            "Connection refused to https://api.internal.corp:8443/v1/models with auth header Bearer secret_123"
        )

        with pytest.raises(LLMProviderError) as exc_info:
            await router.complete("Hola")

        # The public error message must be sanitized and must NOT leak sensitive endpoints or secrets
        assert "secret_123" not in str(exc_info.value)
        assert "https://api.internal.corp:8443" not in str(exc_info.value)
        assert "El proveedor LLM no pudo completar la solicitud" in str(exc_info.value)
