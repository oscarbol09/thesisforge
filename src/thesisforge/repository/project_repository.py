"""Async CRUD repository for research project entities."""

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

        query = """
            INSERT INTO projects (id, title, academic_level, phase, state_json, version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)
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
                    now_str,
                    updated_str,
                ),
            )
            await conn.commit()

        logger.info("Project created successfully.", extra={"project_id": project.id})
        return project

    async def get_project(self, project_id: str) -> ProjectStateDTO:
        """Retrieve a project by ID or raise ProjectNotFoundError."""
        query = "SELECT state_json FROM projects WHERE id = ?"
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, (project_id,))
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
        query = "SELECT state_json, version FROM projects WHERE id = ?"
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, (project_id,))
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
        updated_str = format_iso_utc(project.updated_at)
        state_json = project.model_dump_json()

        query = """
            UPDATE projects
            SET title = ?, academic_level = ?, phase = ?, state_json = ?,
                version = version + 1, updated_at = ?
            WHERE id = ?
        """

        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                query,
                (
                    project.title or "Proyecto sin título",
                    project.academic_level.value,
                    project.phase.value,
                    state_json,
                    updated_str,
                    project.id,
                ),
            )
            await conn.commit()
            if cursor.rowcount == 0:
                raise ProjectNotFoundError(
                    f"No se pudo actualizar. Proyecto '{project.id}' no existe."
                )

        logger.info("Project updated successfully.", extra={"project_id": project.id})
        return project

    async def update_project_versioned(
        self, project: ProjectStateDTO, expected_version: int
    ) -> ProjectStateDTO:
        """Update a project with optimistic concurrency control.

        Raises ProjectVersionConflictError (HTTP 409) if another write has
        already incremented the version since the caller last read it.

        Usage:
            project, version = await repo.get_project_with_version(project_id)
            # ... mutate project ...
            project = await repo.update_project_versioned(project, expected_version=version)
        """
        project.updated_at = utc_now()
        updated_str = format_iso_utc(project.updated_at)
        state_json = project.model_dump_json()

        query = """
            UPDATE projects
            SET title = ?, academic_level = ?, phase = ?, state_json = ?,
                version = version + 1, updated_at = ?
            WHERE id = ? AND version = ?
        """

        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                query,
                (
                    project.title or "Proyecto sin título",
                    project.academic_level.value,
                    project.phase.value,
                    state_json,
                    updated_str,
                    project.id,
                    expected_version,
                ),
            )
            await conn.commit()

            if cursor.rowcount == 0:
                # Distinguish between project not found and version conflict
                check_cursor = await conn.execute(
                    "SELECT version FROM projects WHERE id = ?", (project.id,)
                )
                check_row = await check_cursor.fetchone()
                if check_row is None:
                    raise ProjectNotFoundError(
                        f"No se pudo actualizar. Proyecto '{project.id}' no existe."
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
        """Delete a project by ID. ChromaDB collection cleanup is handled by the caller."""
        query = "DELETE FROM projects WHERE id = ?"
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, (project_id,))
            await conn.commit()
            if cursor.rowcount == 0:
                raise ProjectNotFoundError(
                    f"No se pudo eliminar. Proyecto '{project_id}' no existe."
                )

        logger.info("Project deleted successfully.", extra={"project_id": project_id})
        return True

    async def list_projects(self) -> list[ProjectSummaryDTO]:
        """Return list of project summaries ordered by updated_at descending."""
        query = "SELECT state_json FROM projects ORDER BY updated_at DESC"
        summaries: list[ProjectSummaryDTO] = []
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query)
            rows = await cursor.fetchall()
            for row in rows:
                state_json = str(row["state_json"])
                proj = ProjectStateDTO.model_validate_json(state_json)
                summaries.append(proj.to_summary())
        return summaries

    async def list_by_phase(self, phase: ProjectPhase) -> list[ProjectSummaryDTO]:
        """Filter project summaries by current phase."""
        query = "SELECT state_json FROM projects WHERE phase = ? ORDER BY updated_at DESC"
        summaries: list[ProjectSummaryDTO] = []
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, (phase.value,))
            rows = await cursor.fetchall()
            for row in rows:
                proj = ProjectStateDTO.model_validate_json(str(row["state_json"]))
                summaries.append(proj.to_summary())
        return summaries
