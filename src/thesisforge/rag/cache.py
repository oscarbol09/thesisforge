"""Persistent SQLite cache with TTL for academic queries and DOI metadata."""

import hashlib
import json
from datetime import timedelta
from typing import Any

from thesisforge.core.logging import get_logger
from thesisforge.core.time import format_iso_utc, utc_now
from thesisforge.repository.database import DatabaseManager

logger = get_logger(__name__)


class LiteratureCache:
    """Manages persistent caching of external academic API responses."""

    def __init__(self, db: DatabaseManager, default_ttl_hours: int = 48) -> None:
        self.db = db
        self.default_ttl = timedelta(hours=default_ttl_hours)

    @staticmethod
    def generate_key(source: str, identifier: str) -> str:
        """Create a deterministic SHA-256 cache key."""
        normalized = f"{source.strip().lower()}:{identifier.strip().lower()}"
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    async def get(self, source: str, identifier: str) -> Any | None:
        """Retrieve cached response if not expired."""
        key = self.generate_key(source, identifier)
        now_iso = format_iso_utc(utc_now())

        query = """
            SELECT data_json, expires_at
            FROM literature_cache
            WHERE cache_key = ? AND expires_at > ?
        """
        async with (
            self.db.get_connection() as conn,
            conn.execute(query, (key, now_iso)) as cursor,
        ):
            row = await cursor.fetchone()
            if row:
                try:
                    return json.loads(row["data_json"])
                except json.JSONDecodeError:
                    return None
        return None

    async def set(
        self,
        source: str,
        identifier: str,
        data: Any,
        ttl_hours: int | None = None,
    ) -> None:
        """Store or update cached API response with TTL."""
        key = self.generate_key(source, identifier)
        ttl = timedelta(hours=ttl_hours) if ttl_hours is not None else self.default_ttl
        now = utc_now()
        expires = now + ttl

        query = """
            INSERT OR REPLACE INTO literature_cache (
                cache_key, source, data_json, expires_at, created_at
            ) VALUES (?, ?, ?, ?, ?)
        """
        data_json = json.dumps(data, ensure_ascii=False)
        async with self.db.get_connection() as conn:
            await conn.execute(
                query,
                (
                    key,
                    source.lower(),
                    data_json,
                    format_iso_utc(expires),
                    format_iso_utc(now),
                ),
            )
            await conn.commit()

    async def prune_expired(self) -> int:
        """Remove expired cache entries from database."""
        now_iso = format_iso_utc(utc_now())
        query = "DELETE FROM literature_cache WHERE expires_at <= ?"
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, (now_iso,))
            deleted = int(cursor.rowcount)
            await conn.commit()
            if deleted > 0:
                logger.info(
                    "Pruned expired literature cache entries.",
                    extra={"deleted_count": deleted},
                )
            return deleted
