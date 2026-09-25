"""Async SQLite database manager with WAL mode and schema initialization."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

from thesisforge.core.logging import get_logger

logger = get_logger(__name__)

INIT_SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    academic_level TEXT NOT NULL,
    phase TEXT NOT NULL,
    state_json TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_projects_phase ON projects(phase);
CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_projects_academic_level ON projects(academic_level);

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
CREATE INDEX IF NOT EXISTS idx_document_chunks_section ON document_chunks(section_name);

-- document_index_status tracks the Chroma vector-index lifecycle for each document.
-- It allows rebuilding ChromaDB from SQLite and surfacing PENDING/INDEXED/FAILED
-- state to the UI without polling ChromaDB directly.
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


class DatabaseManager:
    """Manages async SQLite connections and ensures table initialization."""

    def __init__(self, db_path: str = "thesisforge.db") -> None:
        """Normalize SQLite connection string or file path."""
        clean_path = db_path
        if clean_path.startswith("sqlite+aiosqlite:///"):
            clean_path = clean_path.replace("sqlite+aiosqlite:///", "")
        elif clean_path.startswith("sqlite:///"):
            clean_path = clean_path.replace("sqlite:///", "")

        self.db_path = clean_path
        self._is_memory = self.db_path == ":memory:" or "mode=memory" in self.db_path
        self._is_uri = False
        self._keepalive_conn: aiosqlite.Connection | None = None

        if self._is_memory:
            # Use shared in-memory URI so multiple connections share the same in-memory DB
            self.connection_string = f"file:memdb_{id(self)}?mode=memory&cache=shared"
            self._is_uri = True
        else:
            self.connection_string = self.db_path

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Yield an aiosqlite connection with row factory and WAL mode configured."""
        if not self._is_memory and not self._is_uri:
            parent_dir = Path(self.db_path).parent
            if not parent_dir.exists() and str(parent_dir) not in ("", "."):
                parent_dir.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.connection_string, uri=self._is_uri) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.execute("PRAGMA busy_timeout = 5000;")
            if not self._is_memory:
                await db.execute("PRAGMA journal_mode = WAL;")
            yield db

    async def initialize(self) -> None:
        """Execute initial schema migrations and create required tables."""
        if self._is_memory and self._keepalive_conn is None:
            # Hold a connection open to prevent in-memory shared database from being destroyed
            self._keepalive_conn = await aiosqlite.connect(self.connection_string, uri=self._is_uri)

        async with self.get_connection() as db:
            from thesisforge.repository.migrations import DatabaseMigrator

            await DatabaseMigrator.apply_all(db)
            logger.info(
                "Database schema initialized successfully.", extra={"db_path": self.db_path}
            )

    async def close(self) -> None:
        """Close keepalive connection if one was maintained."""
        if self._keepalive_conn is not None:
            await self._keepalive_conn.close()
            self._keepalive_conn = None


async def init_db(db_path: str = "thesisforge.db") -> DatabaseManager:
    """Helper function to initialize and return a DatabaseManager instance."""
    manager = DatabaseManager(db_path)
    await manager.initialize()
    return manager
