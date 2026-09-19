"""Async CRUD repository for research project entities."""

from thesisforge.core.logging import get_logger
from thesisforge.core.time import format_iso_utc, utc_now
from thesisforge.exceptions import ProjectNotFoundError
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
            INSERT INTO projects (id, title, academic_level, phase, state_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
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

    async def update_project(self, project: ProjectStateDTO) -> ProjectStateDTO:
        """Update an existing project state."""
        project.updated_at = utc_now()
        updated_str = format_iso_utc(project.updated_at)
        state_json = project.model_dump_json()

        query = """
            UPDATE projects
            SET title = ?, academic_level = ?, phase = ?, state_json = ?, updated_at = ?
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

    async def delete_project(self, project_id: str) -> bool:
        """Delete a project by ID."""
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
