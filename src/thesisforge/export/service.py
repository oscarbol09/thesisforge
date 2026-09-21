"""Export service coordinating document compilation for thesis projects."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from thesisforge.exceptions import ConfigurationError, ExportError, ProjectNotFoundError
from thesisforge.export.docx_compiler import APA7DocxCompiler
from thesisforge.models import ExportFormat, ExportOptionsDTO, ProjectStateDTO
from thesisforge.repository.project_repository import ProjectRepository

if TYPE_CHECKING:
    from thesisforge.repository.database import DatabaseManager


class ExportService:
    """Service responsible for compiling projects into distributable academic documents."""

    def __init__(
        self,
        db_manager: DatabaseManager | None = None,
        project_repo: ProjectRepository | None = None,
        compiler: APA7DocxCompiler | None = None,
    ) -> None:
        self.db = db_manager
        self.project_repo = project_repo or (ProjectRepository(db_manager) if db_manager else None)
        self.compiler = compiler or APA7DocxCompiler()

    async def compile_project_docx(
        self,
        project_id: str,
        options: ExportOptionsDTO | None = None,
    ) -> bytes:
        """Fetch project from repository and compile to DOCX bytes."""
        if not self.project_repo:
            raise ConfigurationError("ProjectRepository no está inicializado en ExportService.")

        project = await self.project_repo.get_project(project_id)
        if not project:
            raise ProjectNotFoundError(f"Proyecto con ID '{project_id}' no encontrado para exportación.")

        return self.compile_project_state_docx(project, options)

    def compile_project_state_docx(
        self,
        project: ProjectStateDTO,
        options: ExportOptionsDTO | None = None,
    ) -> bytes:
        """Compile a ProjectStateDTO instance directly into APA 7 DOCX bytes."""
        opts = options or ExportOptionsDTO()
        if opts.format != ExportFormat.DOCX:
            raise ExportError(f"Formato de exportación no soportado por este compilador: {opts.format}")

        return self.compiler.compile_to_bytes(project, opts)

    async def save_project_docx(
        self,
        project_id: str,
        output_path: str | Path,
        options: ExportOptionsDTO | None = None,
    ) -> Path:
        """Compile and save thesis document to a local filesystem destination."""
        target_path = Path(output_path)
        docx_bytes = await self.compile_project_docx(project_id, options)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(docx_bytes)
        return target_path
