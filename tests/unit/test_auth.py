"""Unit tests for instance-level authentication and owner verification."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

import thesisforge.core.auth as auth_mod
from thesisforge.config import AppSettings
from thesisforge.core.auth import (
    LOCAL_OWNER_ID,
    get_current_owner,
    get_instance_token,
    resolve_instance_token,
)


def test_resolve_instance_token_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """When THESISFORGE_INSTANCE_TOKEN is set in env, it is used directly."""
    monkeypatch.setenv("THESISFORGE_INSTANCE_TOKEN", "custom_secret_token_123")
    token = resolve_instance_token()
    assert token == "custom_secret_token_123"


def test_resolve_instance_token_from_disk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When a token file already exists on disk, its content is read."""
    monkeypatch.delenv("THESISFORGE_INSTANCE_TOKEN", raising=False)
    token_file = tmp_path / "instance.token"
    token_file.write_text("persisted_token_xyz", encoding="utf-8")

    token = resolve_instance_token(token_file=token_file)
    assert token == "persisted_token_xyz"


def test_resolve_instance_token_generates_and_persists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When no token exists, a new cryptographic token is generated and saved."""
    monkeypatch.delenv("THESISFORGE_INSTANCE_TOKEN", raising=False)
    token_file = tmp_path / "subdir" / "instance.token"
    assert not token_file.exists()

    token = resolve_instance_token(token_file=token_file)
    assert len(token) > 20
    assert token_file.is_file()
    assert token_file.read_text(encoding="utf-8").strip() == token


def test_get_instance_token_caches(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_instance_token caches the token after first resolution."""
    monkeypatch.setattr(auth_mod, "_instance_token", None)
    monkeypatch.setenv("THESISFORGE_INSTANCE_TOKEN", "cached_token_abc")

    t1 = get_instance_token()
    monkeypatch.setenv("THESISFORGE_INSTANCE_TOKEN", "different_token")
    t2 = get_instance_token()

    assert t1 == "cached_token_abc"
    assert t2 == "cached_token_abc"
    monkeypatch.setattr(auth_mod, "_instance_token", None)


@pytest.mark.asyncio
async def test_public_paths_bypass_auth() -> None:
    """Public paths like /health and /api/version always return LOCAL_OWNER_ID without auth."""
    mock_conn = MagicMock()
    mock_conn.url.path = "/health"
    mock_conn.headers = {}
    mock_conn.query_params = {}
    settings = AppSettings(environment="production")

    owner = await get_current_owner(connection=mock_conn, settings=settings)
    assert owner == LOCAL_OWNER_ID

    mock_conn.url.path = "/api/version"
    owner_ver = await get_current_owner(connection=mock_conn, settings=settings)
    assert owner_ver == LOCAL_OWNER_ID


@pytest.mark.asyncio
async def test_auth_disabled_in_development_bypasses() -> None:
    """When environment=development and auth_disabled=True, auth is bypassed."""
    mock_conn = MagicMock()
    mock_conn.url.path = "/api/projects"
    mock_conn.headers = {}
    mock_conn.query_params = {}
    settings = AppSettings(environment="development", auth_disabled=True)

    owner = await get_current_owner(connection=mock_conn, settings=settings)
    assert owner == LOCAL_OWNER_ID


@pytest.mark.asyncio
async def test_auth_disabled_in_test_environment_bypasses() -> None:
    """When environment=test, auth is bypassed for test isolation."""
    mock_conn = MagicMock()
    mock_conn.url.path = "/api/projects"
    mock_conn.headers = {}
    mock_conn.query_params = {}
    settings = AppSettings(environment="test")

    owner = await get_current_owner(connection=mock_conn, settings=settings)
    assert owner == LOCAL_OWNER_ID


@pytest.mark.asyncio
async def test_missing_credentials_in_production_raises_401(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """In production, missing Bearer token raises HTTP 401 with MISSING_TOKEN."""
    monkeypatch.setenv("THESISFORGE_INSTANCE_TOKEN", "prod_token_123")
    monkeypatch.setattr(auth_mod, "_instance_token", "prod_token_123")

    mock_conn = MagicMock()
    mock_conn.url.path = "/api/projects"
    mock_conn.headers = {}
    mock_conn.query_params = {}
    settings = AppSettings(environment="production")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_owner(connection=mock_conn, settings=settings)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["error"] == "MISSING_TOKEN"


@pytest.mark.asyncio
async def test_invalid_credentials_in_production_raises_401(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """In production, invalid Bearer token raises HTTP 401 with INVALID_TOKEN."""
    monkeypatch.setenv("THESISFORGE_INSTANCE_TOKEN", "correct_token_123")
    monkeypatch.setattr(auth_mod, "_instance_token", "correct_token_123")

    mock_conn = MagicMock()
    mock_conn.url.path = "/api/projects"
    mock_conn.headers = {"Authorization": "Bearer wrong_token_456"}
    mock_conn.query_params = {}
    settings = AppSettings(environment="production")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_owner(connection=mock_conn, settings=settings)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["error"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_valid_credentials_in_production_returns_owner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """In production, valid Bearer token returns LOCAL_OWNER_ID."""
    monkeypatch.setenv("THESISFORGE_INSTANCE_TOKEN", "valid_secret_789")
    monkeypatch.setattr(auth_mod, "_instance_token", "valid_secret_789")

    mock_conn = MagicMock()
    mock_conn.url.path = "/api/projects"
    mock_conn.headers = {"Authorization": "Bearer valid_secret_789"}
    mock_conn.query_params = {}
    settings = AppSettings(environment="production")

    owner = await get_current_owner(connection=mock_conn, settings=settings)
    assert owner == LOCAL_OWNER_ID


@pytest.mark.asyncio
async def test_valid_token_in_query_params_returns_owner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """In production, token passed via query param (e.g. for WebSockets) returns LOCAL_OWNER_ID."""
    monkeypatch.setenv("THESISFORGE_INSTANCE_TOKEN", "ws_secret_999")
    monkeypatch.setattr(auth_mod, "_instance_token", "ws_secret_999")

    mock_conn = MagicMock()
    mock_conn.url.path = "/api/defense/ws/proj-123/session-456"
    mock_conn.headers = {}
    mock_conn.query_params = {"token": "ws_secret_999"}
    settings = AppSettings(environment="production")

    owner = await get_current_owner(connection=mock_conn, settings=settings)
    assert owner == LOCAL_OWNER_ID
