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
        OPENROUTER_API_KEY="sk-or-env-key-12345",
        GEMINI_API_KEY="AIzaSyEnvKey-67890",
    )
    router = LLMRouter(settings=settings)

    assert await router.resolve_api_key("openrouter") == "sk-or-env-key-12345"
    assert await router.resolve_api_key("gemini") == "AIzaSyEnvKey-67890"
    assert await router.resolve_api_key("unknown_provider") is None


@pytest.mark.asyncio
async def test_resolve_api_key_from_keystore_priority(
    in_memory_db: DatabaseManager, vault: MagicMock
):
    """Test that keystore repository takes priority over static settings."""
    keystore = SecureKeyStoreRepository(in_memory_db, vault)
    await keystore.store_key("openrouter", "sk-or-database-key-priority")

    settings = AppSettings(OPENROUTER_API_KEY="sk-or-env-fallback")
    router = LLMRouter(settings=settings, keystore_repo=keystore)

    resolved = await router.resolve_api_key("openrouter")
    assert resolved == "sk-or-database-key-priority"


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
    """Test LLM exception is wrapped into LLMProviderError."""
    router = LLMRouter()

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.side_effect = RuntimeError("Conexión rechazada por API externa")

        with pytest.raises(LLMProviderError):
            await router.complete("Hola")
