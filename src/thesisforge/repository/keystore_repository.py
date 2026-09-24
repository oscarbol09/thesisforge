"""Encrypted repository for managing local BYOK API keys."""

from thesisforge.core.logging import get_logger
from thesisforge.core.security import LocalKeyVault
from thesisforge.core.time import format_iso_utc, utc_now
from thesisforge.repository.database import DatabaseManager

logger = get_logger(__name__)


class SecureKeyStoreRepository:
    """Repository for storing and retrieving encrypted API keys."""

    def __init__(self, db_manager: DatabaseManager, vault: LocalKeyVault) -> None:
        self.db = db_manager
        self.vault = vault

    async def store_key(self, provider: str, raw_api_key: str) -> None:
        """Encrypt and persist an API key for a given provider."""
        normalized_provider = provider.strip().lower()
        encrypted_val = self.vault.encrypt(raw_api_key)
        now_str = format_iso_utc(utc_now())

        query = """
            INSERT INTO keystore (provider, encrypted_key, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(provider) DO UPDATE SET
                encrypted_key = excluded.encrypted_key,
                updated_at = excluded.updated_at
        """

        async with self.db.get_connection() as conn:
            await conn.execute(
                query,
                (normalized_provider, encrypted_val, now_str, now_str),
            )
            await conn.commit()

        logger.info(
            "API key encrypted and stored successfully.",
            extra={"provider": normalized_provider},
        )

    async def get_key(self, provider: str) -> str | None:
        """Retrieve and decrypt an API key for a given provider."""
        normalized_provider = provider.strip().lower()
        query = "SELECT encrypted_key FROM keystore WHERE provider = ?"

        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, (normalized_provider,))
            row = await cursor.fetchone()
            if row is None:
                return None

            encrypted_token = str(row["encrypted_key"])
            return self.vault.decrypt(encrypted_token)

    async def delete_key(self, provider: str) -> bool:
        """Remove a stored API key for a provider."""
        normalized_provider = provider.strip().lower()
        query = "DELETE FROM keystore WHERE provider = ?"

        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, (normalized_provider,))
            await conn.commit()
            deleted = int(cursor.rowcount) > 0

        if deleted:
            logger.info("API key deleted.", extra={"provider": normalized_provider})
        return bool(deleted)

    async def list_configured_providers(self) -> list[str]:
        """List all provider names that have an encrypted key stored."""
        query = "SELECT provider FROM keystore ORDER BY provider ASC"
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query)
            rows = await cursor.fetchall()
            return [str(row["provider"]) for row in rows]
