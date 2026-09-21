"""Integration tests for thesis export API endpoints."""

import io

import pytest
from docx import Document
from httpx import ASGITransport, AsyncClient

from thesisforge.api.app import app
from thesisforge.api.deps import get_db_manager
from thesisforge.models import (
    AcademicLevel,
    ProjectPhase,
    ProjectStateDTO,
    SectionDraftDTO,
    SectionStatus,
)
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


@pytest.fixture
def override_db(in_memory_db: DatabaseManager):
    app.dependency_overrides[get_db_manager] = lambda: in_memory_db
    yield in_memory_db
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_export_project_docx(override_db: DatabaseManager):
    """Verify POST /api/export/projects/{id}/docx returns valid Word file attachment."""
    repo = ProjectRepository(override_db)
    project = ProjectStateDTO(
        id="proj-export-api-01",
        title="Tesis de Exportación APA 7",
        academic_level=AcademicLevel.PREGRADO,
        phase=ProjectPhase.DRAFTING,
        sections=[
            SectionDraftDTO(
                section_id="sec_1_1",
                chapter_number=1,
                order_index=1,
                title="Planteamiento",
                content="Contenido de prueba para exportación.",
                status=SectionStatus.APPROVED,
            )
        ],
    )
    await repo.create_project(project)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/export/projects/proj-export-api-01/docx",
            json={
                "author_name": "Ana Gómez",
                "institution_name": "Universidad Central",
                "advisor_name": "Dr. Fernando Ruiz",
            },
        )
        assert resp.status_code == 200
        assert (
            resp.headers["content-type"]
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert (
            'attachment; filename="tesis_proj-export-api-01.docx"'
            in resp.headers["content-disposition"]
        )

        # Parse returned bytes as valid docx
        doc = Document(io.BytesIO(resp.content))
        assert doc.core_properties.title == "Tesis de Exportación APA 7"
        assert doc.core_properties.author == "Ana Gómez"


@pytest.mark.asyncio
async def test_api_export_project_not_found(override_db: DatabaseManager):
    """Verify 404 response for non-existent project export."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/export/projects/non-existent-proj/docx")
        assert resp.status_code == 404
        assert resp.json()["error"] == "PROJECT_NOT_FOUND"
