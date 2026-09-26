"""API routes for managing encrypted BYOK API keys and runtime provider configuration."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from thesisforge.api.deps import get_keystore_repository
from thesisforge.core.auth import get_current_owner
from thesisforge.core.logging import get_logger
from thesisforge.repository.keystore_repository import SecureKeyStoreRepository

logger = get_logger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SetApiKeyRequest(BaseModel):
    """Payload for storing or updating an encrypted API key."""

    provider: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Provider identifier, e.g. openrouter, openai, gemini",
    )
    api_key: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Raw API key to be encrypted in the Fernet vault",
    )


class ProviderStatusResponse(BaseModel):
    """Response indicating which providers have an active encrypted key in the vault."""

    configured_providers: list[str] = Field(
        ..., description="List of provider IDs with stored keys"
    )


@router.get(
    "/keys",
    response_model=ProviderStatusResponse,
    dependencies=[Depends(get_current_owner)],
)
async def list_configured_keys(
    keystore: SecureKeyStoreRepository = Depends(get_keystore_repository),
) -> ProviderStatusResponse:
    """List all LLM provider names that currently have an encrypted key in the vault.

    Note: The actual secret key values are never returned in plaintext.
    """
    providers = await keystore.list_configured_providers()
    return ProviderStatusResponse(configured_providers=providers)


@router.post(
    "/keys",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_owner)],
)
async def store_api_key(
    payload: SetApiKeyRequest,
    keystore: SecureKeyStoreRepository = Depends(get_keystore_repository),
) -> dict[str, str]:
    """Encrypt and store an API key into the local Fernet vault database."""
    normalized = payload.provider.strip().lower()
    clean_key = payload.api_key.strip()
    if not clean_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key cannot be empty or whitespace only.",
        )

    await keystore.store_key(normalized, clean_key)
    logger.info("Encrypted API key saved for provider.", extra={"provider": normalized})
    return {
        "status": "ok",
        "provider": normalized,
        "message": "Key securely encrypted and stored in vault.",
    }


@router.delete(
    "/keys/{provider}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_owner)],
)
async def delete_api_key(
    provider: str,
    keystore: SecureKeyStoreRepository = Depends(get_keystore_repository),
) -> dict[str, str]:
    """Remove a stored encrypted API key from the local vault."""
    normalized = provider.strip().lower()
    deleted = await keystore.delete_key(normalized)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No key found for provider '{normalized}'.",
        )

    logger.info("Deleted encrypted API key.", extra={"provider": normalized})
    return {"status": "ok", "provider": normalized, "message": "Key removed from vault."}
