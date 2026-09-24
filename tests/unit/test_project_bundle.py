"""Unit tests for project bundle export and import (.thesisforge format)."""

import io
import json
import zipfile
from pathlib import Path

import pytest

from thesisforge.exceptions import ExportError, ProjectNotFoundError
from thesisforge.export.bundle import ProjectBundleService
from thesisforge.models import (
    AcademicLevel,
    CitationDTO,
    MethodologyDTO,
    ProjectStateDTO,
    ResearchApproach,
    SectionDraftDTO,
    SectionStatus,
)
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


@pytest.fixture
async def db_manager(tmp_path: Path):
    db_file = tmp_path / "test_bundle.db"
    mgr = DatabaseManager(f"sqlite+aiosqlite:///{db_file}")
    await mgr.initialize()
    yield mgr
    await mgr.close()


@pytest.fixture
def project_repo(db_manager: DatabaseManager) -> ProjectRepository:
    return ProjectRepository(db_manager)


@pytest.fixture
def bundle_service(project_repo: ProjectRepository) -> ProjectBundleService:
    return ProjectBundleService(project_repo)


@pytest.mark.asyncio
async def test_export_and_import_bundle_in_memory(
    project_repo: ProjectRepository,
    bundle_service: ProjectBundleService,
) -> None:
    """Test full cycle of exporting to bytes and importing back into database."""
    # 1. Create a rich project
    project = ProjectStateDTO(
        id="proj-bundle-test-01",
        title="Estudio de Redes Neuronales en Diagnóstico Clínico",
        academic_level=AcademicLevel.MAESTRIA,
        field_of_study="Ciencias de la Computación",
        methodology=MethodologyDTO(approach=ResearchApproach.CUANTITATIVO),
        sections=[
            SectionDraftDTO(
                section_id="sec_1_1",
                chapter_number=1,
                order_index=1,
                title="Planteamiento del Problema",
                status=SectionStatus.APPROVED,
                content="Contenido de prueba de la sección 1.1.",
                word_count=7,
            )
        ],
        validated_citations=[
            CitationDTO(
                id="cit-001",
                paper_id="paper-001",
                title="Deep Convolutional Networks in Radiology",
                authors=["LeCun, Yann", "Bengio, Yoshua"],
                year=2023,
                doi="10.1016/j.rad.2023.01",
                source="semantic_scholar",
            )
        ],
    )
    await project_repo.create_project(project)

    # 2. Export bundle to bytes
    bundle_bytes = await bundle_service.export_bundle_bytes(project.id)
    assert len(bundle_bytes) > 0

    # 3. Import bundle into new project ID
    imported_project = await bundle_service.import_bundle_bytes(
        bundle_bytes,
        new_project_id="proj-restored-01",
    )
    assert imported_project.id == "proj-restored-01"
    assert imported_project.title == project.title
    assert imported_project.methodology.approach == ResearchApproach.CUANTITATIVO

    # Verify restored sections
    restored = await project_repo.get_project("proj-restored-01")
    assert restored is not None
    assert len(restored.sections) == 1
    assert restored.sections[0].section_id == "sec_1_1"
    assert restored.sections[0].content == "Contenido de prueba de la sección 1.1."

    # Verify restored citations
    assert len(restored.validated_citations) == 1
    assert restored.validated_citations[0].doi == "10.1016/j.rad.2023.01"


@pytest.mark.asyncio
async def test_export_and_import_bundle_file(
    project_repo: ProjectRepository,
    bundle_service: ProjectBundleService,
    tmp_path: Path,
) -> None:
    """Test exporting to a file on disk and importing from that file."""
    project = ProjectStateDTO(
        id="proj-disk-test",
        title="Investigación de Archivo",
        academic_level=AcademicLevel.DOCTORADO,
        methodology=MethodologyDTO(approach=ResearchApproach.CUALITATIVO),
    )
    await project_repo.create_project(project)

    target_file = tmp_path / "backup.thesisforge"
    saved_path = await bundle_service.export_bundle_file(project.id, str(target_file))
    assert saved_path.exists()
    assert saved_path.stat().st_size > 0

    imported = await bundle_service.import_bundle_file(
        str(saved_path), new_project_id="proj-imported-file"
    )
    assert imported.id == "proj-imported-file"
    assert imported.academic_level.value == "doctorado"


@pytest.mark.asyncio
async def test_export_nonexistent_project_raises_error(
    bundle_service: ProjectBundleService,
) -> None:
    """Exporting a non-existent project raises ProjectNotFoundError."""
    with pytest.raises(ProjectNotFoundError):
        await bundle_service.export_bundle_bytes("non-existent-id")


@pytest.mark.asyncio
async def test_import_corrupted_bundle_rejected(
    bundle_service: ProjectBundleService,
) -> None:
    """Importing random non-zip bytes raises ExportError."""
    corrupted_data = b"This is not a valid zip archive."
    with pytest.raises(ExportError) as exc_info:
        await bundle_service.import_bundle_bytes(corrupted_data)
    assert "no tiene un formato ZIP válido" in str(exc_info.value) or "no es un archivo ZIP" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_import_tampered_payload_rejected(
    project_repo: ProjectRepository,
    bundle_service: ProjectBundleService,
) -> None:
    """Importing a zip where project.json was tampered after manifest hashing raises ExportError."""
    project = ProjectStateDTO(
        id="proj-tamper-test",
        title="Proyecto Original",
        academic_level=AcademicLevel.PREGRADO,
    )
    await project_repo.create_project(project)
    bundle_bytes = await bundle_service.export_bundle_bytes(project.id)

    # Tamper with the zip: modify project.json without updating manifest checksum
    in_mem_in = io.BytesIO(bundle_bytes)
    in_mem_out = io.BytesIO()

    with zipfile.ZipFile(in_mem_in, "r") as zin, zipfile.ZipFile(in_mem_out, "w") as zout:
        for item in zin.infolist():
            content = zin.read(item.filename)
            if item.filename == "project.json":
                proj_data = json.loads(content.decode("utf-8"))
                proj_data["title"] = "Proyecto Alterado Maliciosamente"
                content = json.dumps(proj_data).encode("utf-8")
            zout.writestr(item, content)

    tampered_bytes = in_mem_out.getvalue()
    with pytest.raises(ExportError) as exc_info:
        await bundle_service.import_bundle_bytes(tampered_bytes)
    assert "Fallo de integridad criptográfica" in str(exc_info.value)
