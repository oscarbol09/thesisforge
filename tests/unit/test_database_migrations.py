"""Unit tests for SQLite schema migrations and PRAGMA user_version tracking."""

import aiosqlite
import pytest

from thesisforge.repository.migrations import CURRENT_SCHEMA_VERSION, DatabaseMigrator


@pytest.mark.asyncio
async def test_migration_on_fresh_database() -> None:
    """A new in-memory database starts at version 0 and migrates to CURRENT_SCHEMA_VERSION."""
    async with aiosqlite.connect(":memory:") as conn:
        initial_ver = await DatabaseMigrator.get_version(conn)
        assert initial_ver == 0

        applied_ver = await DatabaseMigrator.apply_all(conn)
        assert applied_ver == CURRENT_SCHEMA_VERSION

        current_ver = await DatabaseMigrator.get_version(conn)
        assert current_ver == CURRENT_SCHEMA_VERSION

        # Verify essential tables exist
        tables_to_check = [
            "projects",
            "keystore",
            "literature_cache",
            "document_chunks",
            "jury_evaluations",
            "defense_sessions",
        ]
        for tbl in tables_to_check:
            async with conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tbl,)
            ) as cursor:
                row = await cursor.fetchone()
                assert row is not None, f"Table '{tbl}' was not created by migrations"


@pytest.mark.asyncio
async def test_migration_idempotency() -> None:
    """Running apply_all multiple times has no side effects and preserves schema."""
    async with aiosqlite.connect(":memory:") as conn:
        ver1 = await DatabaseMigrator.apply_all(conn)
        assert ver1 == CURRENT_SCHEMA_VERSION

        # Run again
        ver2 = await DatabaseMigrator.apply_all(conn)
        assert ver2 == CURRENT_SCHEMA_VERSION


@pytest.mark.asyncio
async def test_set_and_get_version() -> None:
    """Test manual version setting and reading with PRAGMA user_version."""
    async with aiosqlite.connect(":memory:") as conn:
        assert await DatabaseMigrator.get_version(conn) == 0
        await DatabaseMigrator.set_version(conn, 42)
        assert await DatabaseMigrator.get_version(conn) == 42
