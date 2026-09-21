"""Unit tests for ExportService."""

from pathlib import Path

import pytest

from thesisforge.exceptions import ExportError, ProjectNotFoundError
from thesisforge.export.service import ExportService
from thesisforge.models import (
    AcademicLevel,
    ExportFormat,
    ExportOptionsDTO,
    ProjectPhase,
    ProjectStateDTO,
    SectionDraftDTO,
    SectionStatus,
)
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


@pytest.mark.asyncio
async def test_export_service_compile_project_docx(in_memory_db: DatabaseManager):
    """Verify ExportService compiles project by ID from database."""
    repo = ProjectRepository(in_memory_db)
    project = ProjectStateDTO(
        id="proj-export-svc-01",
        title="Tesis de Inteligencia Artificial",
        academic_level=AcademicLevel.MAESTRIA,
        phase=ProjectPhase.DRAFTING,
        sections=[
            SectionDraftDTO(
                section_id="sec_1_1",
                chapter_number=1,
                order_index=1,
                title="Introducción",
                content="Texto introductorio riguroso.",
                status=SectionStatus.APPROVED,
            )
        ],
    )
    await repo.create_project(project)

    service = ExportService(db_manager=in_memory_db, project_repo=repo)
    docx_bytes = await service.compile_project_docx("proj-export-svc-01")

    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 0


@pytest.mark.asyncio
async def test_export_service_project_not_found(in_memory_db: DatabaseManager):
    """Verify ExportService raises ProjectNotFoundError for non-existent ID."""
    repo = ProjectRepository(in_memory_db)
    service = ExportService(db_manager=in_memory_db, project_repo=repo)

    with pytest.raises(ProjectNotFoundError):
        await service.compile_project_docx("non-existent-proj")


@pytest.mark.asyncio
async def test_export_service_unsupported_format(in_memory_db: DatabaseManager):
    """Verify ExportService raises ExportError when unsupported format requested."""
    repo = ProjectRepository(in_memory_db)
    service = ExportService(db_manager=in_memory_db, project_repo=repo)
    project = ProjectStateDTO(id="proj-format-01", title="Test Format")

    with pytest.raises(ExportError):
        service.compile_project_state_docx(project, ExportOptionsDTO(format=ExportFormat.PDF))


@pytest.mark.asyncio
async def test_export_service_save_project_docx(in_memory_db: DatabaseManager, tmp_path: Path):
    """Verify save_project_docx writes compiled document to target filesystem path."""
    repo = ProjectRepository(in_memory_db)
    project = ProjectStateDTO(
        id="proj-export-save-01",
        title="Tesis Guardada en Disco",
        academic_level=AcademicLevel.PREGRADO,
        phase=ProjectPhase.DRAFTING,
    )
    await repo.create_project(project)

    service = ExportService(db_manager=in_memory_db, project_repo=repo)
    target_file = tmp_path / "thesis_output.docx"

    saved_path = await service.save_project_docx("proj-export-save-01", target_file)

    assert saved_path == target_file
    assert target_file.exists()
    assert target_file.stat().st_size > 0
