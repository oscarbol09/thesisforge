"""Regression coverage for temporary credentials on the settings connection test."""

from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI

from thesisforge.api.deps import get_keystore_repository
from thesisforge.api.routes_settings import router
from thesisforge.core.auth import LOCAL_OWNER_ID, get_current_owner
from thesisforge.core.security import LocalKeyVault
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.keystore_repository import SecureKeyStoreRepository


@pytest.mark.asyncio
@pytest.mark.parametrize("expected_status", ["error", "ok"])
async def test_connection_with_unsaved_key_preserves_vault(
    in_memory_db: DatabaseManager,
    master_key: str,
    monkeypatch: pytest.MonkeyPatch,
    expected_status: str,
) -> None:
    keystore = SecureKeyStoreRepository(
        in_memory_db, LocalKeyVault(master_key=master_key, persist=False)
    )
    await keystore.store_key("openrouter", "saved-key")
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_keystore_repository] = lambda: keystore
    app.dependency_overrides[get_current_owner] = lambda: LOCAL_OWNER_ID

    dispatched_keys: list[tuple[str, str | None]] = []

    async def complete(*, api_key: str, **_kwargs: object) -> SimpleNamespace:
        dispatched_keys.append((api_key, await keystore.get_key("openrouter")))
        if expected_status == "error":
            raise RuntimeError("Provider rejected the test key")
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="OK"))])

    monkeypatch.setattr("thesisforge.llm.router.litellm.acompletion", complete)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        result = await client.post(
            "/api/settings/test-connection",
            json={"provider": "openrouter", "model": "test-model", "api_key": " trial-key "},
        )

    assert result.status_code == 200
    assert result.json()["status"] == expected_status
    assert await keystore.get_key("openrouter") == "saved-key", (
        "Connection test replaced the stored key"
    )
    assert dispatched_keys == [("trial-key", "saved-key")]
