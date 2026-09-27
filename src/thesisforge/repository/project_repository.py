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

    def __init__(self, db_manager: DatabaseManager, owner_id: str) -> None:
        self.db = db_manager
        self.owner_id = owner_id

    async def create_project(self, project: ProjectStateDTO) -> ProjectStateDTO:
        """Persist a new project state in the database."""
        now_str = format_iso_utc(project.created_at)
        updated_str = format_iso_utc(project.updated_at)

        project.owner_id = self.owner_id
        state_json = project.model_dump_json()

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
                    self.owner_id,
                    now_str,
                    updated_str,
                ),
            )
            await conn.commit()

        logger.info(
            "Project created successfully.",
            extra={"project_id": project.id, "owner_id": self.owner_id},
        )
        return project

    async def get_project(self, project_id: str) -> ProjectStateDTO:
        """Retrieve a project by ID with tenant scoping or raise ProjectNotFoundError."""
        query = "SELECT state_json FROM projects WHERE id = ? AND owner_id = ?"
        params: tuple[Any, ...] = (project_id, self.owner_id)

        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, params)
            row = await cursor.fetchone()
            if row is None:
                raise ProjectNotFoundError(f"Proyecto con ID '{project_id}' no encontrado.")

            state_json = str(row["state_json"])
            return ProjectStateDTO.model_validate_json(state_json)

    async def get_project_with_version(self, project_id: str) -> tuple[ProjectStateDTO, int]:
        """Retrieve a project and its current optimistic-lock version.

        Returns:
            Tuple of (ProjectStateDTO, version) where version is used for
            optimistic concurrency control in subsequent update_project_versioned calls.
        """
        query = "SELECT state_json, version FROM projects WHERE id = ? AND owner_id = ?"
        params: tuple[Any, ...] = (project_id, self.owner_id)

        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, params)
            row = await cursor.fetchone()
            if row is None:
                raise ProjectNotFoundError(f"Proyecto con ID '{project_id}' no encontrado.")

            state_json = str(row["state_json"])
            version = int(row["version"])
            return ProjectStateDTO.model_validate_json(state_json), version

    async def update_project(self, project: ProjectStateDTO) -> ProjectStateDTO:
        """Update an existing project state (blind write — use update_project_versioned
        when concurrent access from the GUI or WebSocket is possible).
        """
        project.updated_at = utc_now()
        project.owner_id = self.owner_id
        updated_str = format_iso_utc(project.updated_at)
        state_json = project.model_dump_json()

        query = """
            UPDATE projects
            SET title = ?, academic_level = ?, phase = ?, state_json = ?, owner_id = ?,
                version = version + 1, updated_at = ?
            WHERE id = ? AND owner_id = ?
        """
        params: tuple[Any, ...] = (
            project.title or "Proyecto sin título",
            project.academic_level.value,
            project.phase.value,
            state_json,
            self.owner_id,
            updated_str,
            project.id,
            self.owner_id,
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
    ) -> ProjectStateDTO:
        """Update a project with optimistic concurrency control and owner isolation.

        Raises ProjectVersionConflictError (HTTP 409) if another write has
        already incremented the version since the caller last read it.
        """
        project.updated_at = utc_now()
        project.owner_id = self.owner_id
        updated_str = format_iso_utc(project.updated_at)
        state_json = project.model_dump_json()

        query = """
            UPDATE projects
            SET title = ?, academic_level = ?, phase = ?, state_json = ?, owner_id = ?,
                version = version + 1, updated_at = ?
            WHERE id = ? AND version = ? AND owner_id = ?
        """
        params: tuple[Any, ...] = (
            project.title or "Proyecto sin título",
            project.academic_level.value,
            project.phase.value,
            state_json,
            self.owner_id,
            updated_str,
            project.id,
            expected_version,
            self.owner_id,
        )

        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, params)
            await conn.commit()

            if cursor.rowcount == 0:
                # Distinguish between project not found and version conflict
                check_query = "SELECT version FROM projects WHERE id = ? AND owner_id = ?"
                check_params = (project.id, self.owner_id)
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

    async def delete_project(self, project_id: str) -> bool:
        """Delete a project by ID with owner scoping. ChromaDB collection cleanup is handled by caller."""
        query = "DELETE FROM projects WHERE id = ? AND owner_id = ?"
        params: tuple[Any, ...] = (project_id, self.owner_id)

        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, params)
            await conn.commit()
            if cursor.rowcount == 0:
                raise ProjectNotFoundError(
                    f"No se pudo eliminar. Proyecto '{project_id}' no existe o no tiene permisos."
                )

        logger.info("Project deleted successfully.", extra={"project_id": project_id})
        return True

    async def list_projects(self) -> list[ProjectSummaryDTO]:
        """Return list of project summaries filtered by owner ordered by updated_at descending."""
        query = "SELECT state_json FROM projects WHERE owner_id = ? ORDER BY updated_at DESC"
        params: tuple[Any, ...] = (self.owner_id,)

        summaries: list[ProjectSummaryDTO] = []
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            for row in rows:
                state_json = str(row["state_json"])
                proj = ProjectStateDTO.model_validate_json(state_json)
                summaries.append(proj.to_summary())
        return summaries

    async def list_by_phase(self, phase: ProjectPhase) -> list[ProjectSummaryDTO]:
        """Filter project summaries by current phase and owner."""
        query = "SELECT state_json FROM projects WHERE phase = ? AND owner_id = ? ORDER BY updated_at DESC"
        params: tuple[Any, ...] = (phase.value, self.owner_id)

        summaries: list[ProjectSummaryDTO] = []
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            for row in rows:
                proj = ProjectStateDTO.model_validate_json(str(row["state_json"]))
                summaries.append(proj.to_summary())
        return summaries
