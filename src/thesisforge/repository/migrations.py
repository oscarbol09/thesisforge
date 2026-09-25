"""Lightweight, versioned schema migration manager for SQLite using PRAGMA user_version."""

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

import aiosqlite

from thesisforge.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class Migration:
    """An atomic, versioned schema migration."""

    version: int
    name: str
    up_sql: str | None = None
    up_callable: Callable[[aiosqlite.Connection], Coroutine[Any, Any, None]] | None = None


V1_INITIAL_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    academic_level TEXT NOT NULL,
    phase TEXT NOT NULL,
    state_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_projects_phase ON projects(phase);
CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects(updated_at DESC);

CREATE TABLE IF NOT EXISTS keystore (
    provider TEXT PRIMARY KEY,
    encrypted_key TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS literature_cache (
    cache_key TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    data_json TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_literature_cache_expires ON literature_cache(expires_at);

CREATE TABLE IF NOT EXISTS document_chunks (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    section_name TEXT NOT NULL,
    text TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_project ON document_chunks(project_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_doc ON document_chunks(document_id);

CREATE TABLE IF NOT EXISTS jury_evaluations (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    verdict TEXT NOT NULL,
    score REAL NOT NULL,
    evaluation_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_jury_evaluations_project ON jury_evaluations(project_id);
CREATE INDEX IF NOT EXISTS idx_jury_evaluations_created_at ON jury_evaluations(created_at DESC);

CREATE TABLE IF NOT EXISTS defense_sessions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    status TEXT NOT NULL,
    current_turn INTEGER NOT NULL,
    session_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_defense_sessions_project ON defense_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_defense_sessions_status ON defense_sessions(status);
"""

V2_SCHEMA_EXTENSIONS = """
-- Migration v2: Optimizations for project queries and backup support
CREATE INDEX IF NOT EXISTS idx_projects_academic_level ON projects(academic_level);
CREATE INDEX IF NOT EXISTS idx_document_chunks_section ON document_chunks(section_name);
"""

V3_OPTIMISTIC_CONCURRENCY = """
-- Migration v3: Optimistic concurrency control column for projects
-- SQLite does not support ADD COLUMN IF NOT EXISTS, so we use a safe guard.
CREATE TABLE IF NOT EXISTS _migration_v3_guard (id INTEGER PRIMARY KEY);
"""

V4_DOCUMENT_INDEX_STATUS = """
-- Migration v4: Document-level vector-index lifecycle tracking.
--
-- Rationale: previously, once a PDF was indexed in ChromaDB there was no
-- SQLite record of *which* documents were indexed for a given project.
-- This meant:
--   1. There was no way to detect partially-indexed documents (PENDING/FAILED).
--   2. ChromaDB could not be rebuilt from SQLite after a data loss event.
--
-- The new table `document_index_status` stores one row per document_id / project_id
-- pair with its indexing state and chunk count.  The RAGService writes a PENDING row
-- before calling ChromaDB, transitions to INDEXED on success, and FAILED on error.
-- A future rebuild command can scan INDEXED rows and re-call add_chunks() using the
-- existing `document_chunks` SQLite data — making ChromaDB fully reconstructible.
CREATE TABLE IF NOT EXISTS document_index_status (
    document_id  TEXT NOT NULL,
    project_id   TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'pending',   -- pending | indexed | failed
    chunk_count  INTEGER NOT NULL DEFAULT 0,
    title        TEXT NOT NULL DEFAULT '',
    doi          TEXT,
    error_msg    TEXT,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL,
    PRIMARY KEY (document_id, project_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_doc_index_status_project
    ON document_index_status(project_id);

CREATE INDEX IF NOT EXISTS idx_doc_index_status_status
    ON document_index_status(project_id, status);
"""


async def _v3_add_version_column(db: aiosqlite.Connection) -> None:
    """Safely add the version column to projects if it does not already exist."""
    async with db.execute("PRAGMA table_info(projects);") as cursor:
        cols = [row[1] async for row in cursor]
    if "version" not in cols:
        await db.execute("ALTER TABLE projects ADD COLUMN version INTEGER NOT NULL DEFAULT 1;")
        logger.info("Migration v3: added 'version' column to projects table.")


ALL_MIGRATIONS: list[Migration] = [
    Migration(version=1, name="v1_initial_schema", up_sql=V1_INITIAL_SCHEMA),
    Migration(version=2, name="v2_schema_extensions", up_sql=V2_SCHEMA_EXTENSIONS),
    Migration(
        version=3,
        name="v3_optimistic_concurrency",
        up_sql=V3_OPTIMISTIC_CONCURRENCY,
        up_callable=_v3_add_version_column,
    ),
    Migration(
        version=4,
        name="v4_document_index_status",
        up_sql=V4_DOCUMENT_INDEX_STATUS,
    ),
]

CURRENT_SCHEMA_VERSION: int = max((m.version for m in ALL_MIGRATIONS), default=0)


class DatabaseMigrator:
    """Manages sequential, forward-only schema migrations using PRAGMA user_version."""

    def __init__(self, migrations: list[Migration] | None = None) -> None:
        self.migrations = sorted(
            migrations or ALL_MIGRATIONS,
            key=lambda m: m.version,
        )

    @staticmethod
    async def get_current_version(db: aiosqlite.Connection) -> int:
        """Fetch the current PRAGMA user_version."""
        async with db.execute("PRAGMA user_version;") as cursor:
            row = await cursor.fetchone()
            return int(row[0]) if row else 0

    get_version = get_current_version

    @staticmethod
    async def set_version(db: aiosqlite.Connection, version: int) -> None:
        """Atomically set the PRAGMA user_version."""
        await db.execute(f"PRAGMA user_version = {int(version)};")

    async def apply_migrations(self, db: aiosqlite.Connection) -> int:
        """Apply all pending migrations for this instance, returning the final version."""
        current_version = await self.get_current_version(db)
        applied_count = 0

        for migration in self.migrations:
            if migration.version > current_version:
                logger.info(
                    "Applying database migration.",
                    extra={
                        "migration_version": migration.version,
                        "migration_name": migration.name,
                    },
                )
                if migration.up_sql:
                    await db.executescript(migration.up_sql)
                if migration.up_callable:
                    await migration.up_callable(db)

                await self.set_version(db, migration.version)
                await db.commit()
                current_version = migration.version
                applied_count += 1

        if applied_count > 0:
            logger.info(
                "Database migrations completed.",
                extra={"target_version": current_version, "applied_count": applied_count},
            )

        return current_version

    @classmethod
    async def apply_all(
        cls,
        db: aiosqlite.Connection,
        migrations: list[Migration] | None = None,
    ) -> int:
        """Convenience classmethod to instantiate and apply all pending migrations."""
        migrator = cls(migrations=migrations)
        return await migrator.apply_migrations(db)
