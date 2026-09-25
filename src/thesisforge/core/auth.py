"""Instance-level authentication for ThesisForge local-first deployments.

Design rationale
----------------
ThesisForge is local-first: it is designed to run on a single user's machine.
However, the Docker image binds to 0.0.0.0:8000, which exposes the API to any
host on the local network (and potentially the internet if port-forwarded).

To close that surface without building a full multi-user auth system, we use a
**static instance token** approach:

- On first startup, ``resolve_instance_token()`` generates a cryptographically
  random token and persists it to ``~/.thesisforge/instance.token`` (mode 0o600).
- The token is also printed to stdout so the user can copy it into the GUI or
  API client on first run.
- Every subsequent API request must include ``Authorization: Bearer <token>``.
- The ``/health`` and ``/api/version`` endpoints are always public.
- In ``environment=development`` with ``auth_disabled=True``, the check is
  skipped entirely (useful for automated tests and local dev without env vars).

Future multi-user upgrade path
-------------------------------
Replace the ``get_current_owner`` dependency with a JWT/OAuth2 implementation.
The ``owner_id`` field already present in ``ProjectStateDTO`` will propagate
to the repository layer without further model changes.
"""

import os
import secrets
from pathlib import Path

from fastapi import Depends, HTTPException, status
from starlette.requests import HTTPConnection

from thesisforge.config import AppSettings, get_settings
from thesisforge.core.logging import get_logger

logger = get_logger(__name__)

# Routes that bypass authentication entirely
PUBLIC_PATHS: frozenset[str] = frozenset({"/health", "/api/version"})

# Constant owner ID used in local-first (single-user) mode.
LOCAL_OWNER_ID = "local"


def resolve_instance_token(token_file: Path | None = None) -> str:
    """Return the instance token, generating and persisting it on first call.

    Resolution order:
    1. ``THESISFORGE_INSTANCE_TOKEN`` environment variable (highest priority).
    2. Token file at ``~/.thesisforge/instance.token`` (generated if absent).
    """
    env_token = os.environ.get("THESISFORGE_INSTANCE_TOKEN", "").strip()
    if env_token:
        return env_token

    target = token_file or (Path.home() / ".thesisforge" / "instance.token")

    if target.is_file():
        stored = target.read_text(encoding="utf-8").strip()
        if stored:
            return stored

    new_token = secrets.token_urlsafe(32)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(new_token, encoding="utf-8")
        if os.name != "nt":
            target.chmod(0o600)
        logger.info(
            "Generated new instance token and persisted it to disk.",
            extra={"token_path": str(target)},
        )
        print(  # noqa: T201
            f"\n[ThesisForge] Instance token generated.\n"
            f"  Token : {new_token}\n"
            f"  Saved : {target}\n"
            f"  Add 'Authorization: Bearer <token>' to all API requests,\n"
            f"  or set THESISFORGE_INSTANCE_TOKEN in your environment.\n"
        )
    except OSError as err:
        logger.warning(
            "Could not persist instance token to disk; token is session-only.",
            extra={"error": str(err)},
        )

    return new_token


_instance_token: str | None = None


def get_instance_token() -> str:
    """Return the cached instance token, resolving it on first access."""
    global _instance_token  # noqa: PLW0603
    if _instance_token is None:
        _instance_token = resolve_instance_token()
    return _instance_token


def _auth_is_disabled(settings: AppSettings) -> bool:
    """Return True in test environments, or when explicitly disabled in development."""
    if settings.environment == "test":
        return True
    return settings.environment == "development" and settings.auth_disabled


async def get_current_owner(
    connection: HTTPConnection,
    settings: AppSettings = Depends(get_settings),
) -> str:
    """FastAPI dependency that validates the instance token and returns the owner ID.

    Works seamlessly with both standard HTTP requests and WebSocket connections.

    Returns:
        ``"local"`` -- the only owner in single-user mode.

    Raises:
        HTTP 401 if the token is missing or incorrect.
    """
    if connection.url.path in PUBLIC_PATHS:
        return LOCAL_OWNER_ID

    if _auth_is_disabled(settings):
        return LOCAL_OWNER_ID

    auth_header = connection.headers.get("Authorization", "").strip()
    token: str | None = None
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
    elif "token" in connection.query_params:
        token = connection.query_params.get("token")

    expected_token = get_instance_token()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "MISSING_TOKEN",
                "message": (
                    "Se requiere autenticacion. Incluya 'Authorization: Bearer <token>' "
                    "en la peticion. El token se muestra en la consola del servidor al "
                    "arrancar por primera vez, o puede definirse con "
                    "THESISFORGE_INSTANCE_TOKEN."
                ),
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not secrets.compare_digest(token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_TOKEN",
                "message": "Token de instancia invalido.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    return LOCAL_OWNER_ID
