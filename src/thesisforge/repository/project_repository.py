"""Async CRUD repository for research project entities."""

from typing import Any

from thesisforge.core.logging import get_logger
from thesisforge.core.time import format_iso_utc, utc_now
from thesisforge.exceptions import ProjectNotFoundError, ProjectVersionConflictError
from thesisforge.models import ProjectPhase, ProjectStateDTO, ProjectSummaryDTO
from thesisforge.repository.database import DatabaseManager

logger = get_logger(__name__)


class ProjectRepository:
    """Repository for managing ProjectStateDTO persistence in SQLite."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    async def create_project(self, project: ProjectStateDTO) -> ProjectStateDTO:
        """Persist a new project state in the database."""
        now_str = format_iso_utc(project.created_at)
        updated_str = format_iso_utc(project.updated_at)
        state_json = project.model_dump_json()
        owner_id = project.owner_id or "local"

        query = """
            INSERT INTO projects (id, title, academic_level, phase, state_json, owner_id, version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
        """

        async with self.db.get_connection() as conn:
            await conn.execute(
                query,
                (
                    project.id,
                    project.title or "Proyecto sin título",
                    project.academic_level.value,
                    project.phase.value,
                    state_json,
                    owner_id,
                    now_str,
                    updated_str,
                ),
            )
            await conn.commit()

        logger.info(
            "Project created successfully.",
            extra={"project_id": project.id, "owner_id": owner_id},
        )
        return project

    async def get_project(self, project_id: str, owner_id: str | None = None) -> ProjectStateDTO:
        """Retrieve a project by ID with optional owner tenant scoping or raise ProjectNotFoundError."""
        if owner_id is not None:
            query = "SELECT state_json FROM projects WHERE id = ? AND (owner_id = ? OR owner_id = 'local')"
            params: tuple[Any, ...] = (project_id, owner_id)
        else:
            query = "SELECT state_json FROM projects WHERE id = ?"
            params = (project_id,)

        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, params)
            row = await cursor.fetchone()
            if row is None:
                raise ProjectNotFoundError(f"Proyecto con ID '{project_id}' no encontrado.")

            state_json = str(row["state_json"])
            return ProjectStateDTO.model_validate_json(state_json)

    async def get_project_with_version(
        self, project_id: str, owner_id: str | None = None
    ) -> tuple[ProjectStateDTO, int]:
        """Retrieve a project and its current optimistic-lock version.

        Returns:
            Tuple of (ProjectStateDTO, version) where version is used for
            optimistic concurrency control in subsequent update_project_versioned calls.
        """
        if owner_id is not None:
            query = "SELECT state_json, version FROM projects WHERE id = ? AND (owner_id = ? OR owner_id = 'local')"
            params: tuple[Any, ...] = (project_id, owner_id)
        else:
            query = "SELECT state_json, version FROM projects WHERE id = ?"
            params = (project_id,)

        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, params)
            row = await cursor.fetchone()
            if row is None:
                raise ProjectNotFoundError(f"Proyecto con ID '{project_id}' no encontrado.")

            state_json = str(row["state_json"])
            version = int(row["version"])
            return ProjectStateDTO.model_validate_json(state_json), version

    async def update_project(
        self, project: ProjectStateDTO, owner_id: str | None = None
    ) -> ProjectStateDTO:
        """Update an existing project state (blind write — use update_project_versioned
        when concurrent access from the GUI or WebSocket is possible).
        """
        project.updated_at = utc_now()
        updated_str = format_iso_utc(project.updated_at)
        state_json = project.model_dump_json()
        target_owner = project.owner_id or owner_id or "local"

        if owner_id is not None:
            query = """
                UPDATE projects
                SET title = ?, academic_level = ?, phase = ?, state_json = ?, owner_id = ?,
                    version = version + 1, updated_at = ?
                WHERE id = ? AND (owner_id = ? OR owner_id = 'local')
            """
            params: tuple[Any, ...] = (
                project.title or "Proyecto sin título",
                project.academic_level.value,
                project.phase.value,
                state_json,
                target_owner,
                updated_str,
                project.id,
                owner_id,
            )
        else:
            query = """
                UPDATE projects
                SET title = ?, academic_level = ?, phase = ?, state_json = ?, owner_id = ?,
                    version = version + 1, updated_at = ?
                WHERE id = ?
            """
            params = (
                project.title or "Proyecto sin título",
                project.academic_level.value,
                project.phase.value,
                state_json,
                target_owner,
                updated_str,
                project.id,
            )

        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, params)
            await conn.commit()
            if cursor.rowcount == 0:
                raise ProjectNotFoundError(
                    f"No se pudo actualizar. Proyecto '{project.id}' no existe o pertenece a otro usuario."
                )

        logger.info("Project updated successfully.", extra={"project_id": project.id})
        return project

    async def update_project_versioned(
        self,
        project: ProjectStateDTO,
        expected_version: int,
        owner_id: str | None = None,
    ) -> ProjectStateDTO:
        """Update a project with optimistic concurrency control and owner isolation.

        Raises ProjectVersionConflictError (HTTP 409) if another write has
        already incremented the version since the caller last read it.
        """
        project.updated_at = utc_now()
        updated_str = format_iso_utc(project.updated_at)
        state_json = project.model_dump_json()
        target_owner = project.owner_id or owner_id or "local"

        if owner_id is not None:
            query = """
                UPDATE projects
                SET title = ?, academic_level = ?, phase = ?, state_json = ?, owner_id = ?,
                    version = version + 1, updated_at = ?
                WHERE id = ? AND version = ? AND (owner_id = ? OR owner_id = 'local')
            """
            params: tuple[Any, ...] = (
                project.title or "Proyecto sin título",
                project.academic_level.value,
                project.phase.value,
                state_json,
                target_owner,
                updated_str,
                project.id,
                expected_version,
                owner_id,
            )
        else:
            query = """
                UPDATE projects
                SET title = ?, academic_level = ?, phase = ?, state_json = ?, owner_id = ?,
                    version = version + 1, updated_at = ?
                WHERE id = ? AND version = ?
            """
            params = (
                project.title or "Proyecto sin título",
                project.academic_level.value,
                project.phase.value,
                state_json,
                target_owner,
                updated_str,
                project.id,
                expected_version,
            )

        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, params)
            await conn.commit()

            if cursor.rowcount == 0:
                # Distinguish between project not found and version conflict
                check_query = (
                    "SELECT version FROM projects WHERE id = ? AND (owner_id = ? OR owner_id = 'local')"
                    if owner_id is not None
                    else "SELECT version FROM projects WHERE id = ?"
                )
                check_params = (project.id, owner_id) if owner_id is not None else (project.id,)
                check_cursor = await conn.execute(check_query, check_params)
                check_row = await check_cursor.fetchone()
                if check_row is None:
                    raise ProjectNotFoundError(
                        f"No se pudo actualizar. Proyecto '{project.id}' no existe o no tiene permisos."
                    )
                actual_version = int(check_row["version"])
                raise ProjectVersionConflictError(
                    project_id=project.id,
                    expected_version=expected_version,
                    actual_version=actual_version,
                )

        logger.info(
            "Project updated (versioned).",
            extra={"project_id": project.id, "new_version": expected_version + 1},
        )
        return project

    async def delete_project(self, project_id: str, owner_id: str | None = None) -> bool:
        """Delete a project by ID with owner scoping. ChromaDB collection cleanup is handled by caller."""
        if owner_id is not None:
            query = "DELETE FROM projects WHERE id = ? AND (owner_id = ? OR owner_id = 'local')"
            params: tuple[Any, ...] = (project_id, owner_id)
        else:
            query = "DELETE FROM projects WHERE id = ?"
            params = (project_id,)

        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, params)
            await conn.commit()
            if cursor.rowcount == 0:
                raise ProjectNotFoundError(
                    f"No se pudo eliminar. Proyecto '{project_id}' no existe o no tiene permisos."
                )

        logger.info("Project deleted successfully.", extra={"project_id": project_id})
        return True

    async def list_projects(self, owner_id: str | None = None) -> list[ProjectSummaryDTO]:
        """Return list of project summaries filtered by owner ordered by updated_at descending."""
        if owner_id is not None:
            query = "SELECT state_json FROM projects WHERE (owner_id = ? OR owner_id = 'local') ORDER BY updated_at DESC"
            params: tuple[Any, ...] = (owner_id,)
        else:
            query = "SELECT state_json FROM projects ORDER BY updated_at DESC"
            params = ()

        summaries: list[ProjectSummaryDTO] = []
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            for row in rows:
                state_json = str(row["state_json"])
                proj = ProjectStateDTO.model_validate_json(state_json)
                summaries.append(proj.to_summary())
        return summaries

    async def list_by_phase(
        self, phase: ProjectPhase, owner_id: str | None = None
    ) -> list[ProjectSummaryDTO]:
        """Filter project summaries by current phase and owner."""
        if owner_id is not None:
            query = "SELECT state_json FROM projects WHERE phase = ? AND (owner_id = ? OR owner_id = 'local') ORDER BY updated_at DESC"
            params: tuple[Any, ...] = (phase.value, owner_id)
        else:
            query = "SELECT state_json FROM projects WHERE phase = ? ORDER BY updated_at DESC"
            params = (phase.value,)

        summaries: list[ProjectSummaryDTO] = []
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            for row in rows:
                proj = ProjectStateDTO.model_validate_json(str(row["state_json"]))
                summaries.append(proj.to_summary())
        return summaries
