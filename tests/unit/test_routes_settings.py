"""Unit tests for /api/settings/keys encrypted BYOK endpoints."""

from collections.abc import AsyncGenerator
from pathlib import Path

import httpx
import pytest
import pytest_asyncio

from thesisforge.api.app import create_app
from thesisforge.api.deps import get_keystore_repository
from thesisforge.core.auth import LOCAL_OWNER_ID, get_current_owner
from thesisforge.core.security import LocalKeyVault
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.keystore_repository import SecureKeyStoreRepository


@pytest_asyncio.fixture
async def test_app(tmp_path: Path) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create a hermetic FastAPI test client with in-memory keystore and mocked owner auth."""
    db_path = str(tmp_path / "test_keystore.db")
    db_manager = DatabaseManager(db_path=db_path)
    await db_manager.initialize()

    from cryptography.fernet import Fernet

    vault = LocalKeyVault(master_key=Fernet.generate_key(), persist=False)
    keystore_repo = SecureKeyStoreRepository(db_manager, vault)

    app = create_app()
    app.dependency_overrides[get_keystore_repository] = lambda: keystore_repo
    app.dependency_overrides[get_current_owner] = lambda: LOCAL_OWNER_ID

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    await db_manager.close()


@pytest.mark.asyncio
async def test_keystore_crud_endpoints(test_app: httpx.AsyncClient) -> None:
    """Test listing, storing, and deleting encrypted BYOK API keys via API."""
    # 1. Initially empty
    res = await test_app.get("/api/settings/keys")
    assert res.status_code == 200
    data = res.json()
    assert data["configured_providers"] == []

    # 2. Store OpenRouter key
    store_res = await test_app.post(
        "/api/settings/keys",
        json={"provider": "openrouter", "api_key": "sk-or-v1-secret-test-key-12345"},
    )
    assert store_res.status_code == 200
    assert store_res.json()["status"] == "ok"
    assert store_res.json()["provider"] == "openrouter"

    # 3. Store Gemini key
    store_res2 = await test_app.post(
        "/api/settings/keys",
        json={"provider": "gemini", "api_key": "AIzaSyTestKey67890"},
    )
    assert store_res2.status_code == 200

    # 4. List configured providers - should return names, never raw secrets
    list_res = await test_app.get("/api/settings/keys")
    assert list_res.status_code == 200
    configured = list_res.json()["configured_providers"]
    assert "gemini" in configured
    assert "openrouter" in configured
    # Ensure raw secret is not leaked in the response JSON
    assert "sk-or-v1" not in str(list_res.json())

    # 5. Delete a provider key
    del_res = await test_app.delete("/api/settings/keys/openrouter")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "ok"

    # 6. Verify it is removed
    list_res2 = await test_app.get("/api/settings/keys")
    assert list_res2.status_code == 200
    assert list_res2.json()["configured_providers"] == ["gemini"]

    # 7. Delete non-existent key returns 404
    del_res_404 = await test_app.delete("/api/settings/keys/nonexistent")
    assert del_res_404.status_code == 404


@pytest.mark.asyncio
async def test_keystore_store_empty_key_rejected(test_app: httpx.AsyncClient) -> None:
    """Storing an empty or whitespace key returns 400."""
    res = await test_app.post(
        "/api/settings/keys",
        json={"provider": "openai", "api_key": "   "},
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_test_connection_endpoint_without_key(test_app: httpx.AsyncClient) -> None:
    """Test connection endpoint returns error when no key is configured."""
    res = await test_app.post(
        "/api/settings/test-connection",
        json={"provider": "openrouter", "model": "anthropic/claude-3.5-sonnet"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "error"
    assert "No se encontró clave" in data["message"]
