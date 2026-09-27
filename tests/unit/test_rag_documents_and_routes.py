"""Unit tests for document indexing status, citation registration, and document deletion."""

import fitz  # PyMuPDF
import pytest
import respx

from thesisforge.models import (
    AcademicLevel,
    ProjectPhase,
    ProjectStateDTO,
)
from thesisforge.rag.service import RAGService
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


def _create_sample_pdf_bytes(title: str = "Test PDF Document") -> bytes:
    """Generate a valid single-page PDF in-memory using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 72),
        f"{title}\n\nResumen: Este estudio examina el impacto de los sistemas RAG en la reducción de alucinaciones bibliográficas.",
        fontsize=11,
    )
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.mark.asyncio
async def test_index_pdf_creates_citation_and_records_document_status(
    in_memory_db: DatabaseManager,
):
    """Verify that indexing a PDF creates a CitationDTO in project.validated_citations and persists document status."""
    repo = ProjectRepository(in_memory_db)
    rag = RAGService(
        db_manager=in_memory_db,
        project_repo=repo,
        is_memory=True,
    )

    # 1. Create a project
    project = ProjectStateDTO(
        id="proj-doc-test-1",
        title="Proyecto de Prueba RAG",
        academic_level=AcademicLevel.PREGRADO,
        phase=ProjectPhase.ORIENTATION,
        area_of_study="Ciencias de la Computación",
        topic="RAG y Memoria Semántica",
    )
    await repo.create_project(project)

    # 2. Index a PDF
    pdf_bytes = _create_sample_pdf_bytes("Sistemas RAG en la Educación Superior")
    chunks = await rag.index_pdf_document(
        project_id="proj-doc-test-1",
        document_id="doc-test-01",
        pdf_bytes=pdf_bytes,
        title="Sistemas RAG en la Educación Superior",
        doi="10.1234/rag.edu.2024",
    )

    assert len(chunks) >= 1

    # 3. Verify document index statuses
    statuses = await rag.get_document_index_statuses("proj-doc-test-1")
    assert len(statuses) == 1
    assert statuses[0]["document_id"] == "doc-test-01"
    assert statuses[0]["status"] == "indexed"
    assert statuses[0]["title"] == "Sistemas RAG en la Educación Superior"
    assert statuses[0]["doi"] == "10.1234/rag.edu.2024"
    assert statuses[0]["chunk_count"] == len(chunks)

    # 4. Verify project citations updated
    updated_project = await repo.get_project("proj-doc-test-1")
    assert len(updated_project.validated_citations) == 1
    citation = updated_project.validated_citations[0]
    assert citation.title == "Sistemas RAG en la Educación Superior"
    assert citation.doi == "10.1234/rag.edu.2024"
    assert citation.source == "local_pdf"
    assert "Sistemas RAG en la Educación Superior" in citation.apa_formatted

    # 5. Delete document
    await rag.delete_document("proj-doc-test-1", "doc-test-01")

    # Document status should be deleted
    remaining_statuses = await rag.get_document_index_statuses("proj-doc-test-1")
    assert len(remaining_statuses) == 0


@pytest.mark.asyncio
@respx.mock
async def test_add_and_delete_citation_lifecycle(
    in_memory_db: DatabaseManager,
):
    """Verify manual citation adding and removal from project."""
    respx.head("https://doi.org/10.1000/182").respond(status_code=200)
    respx.get("https://api.crossref.org/works/10.1000%2F182").respond(
        status_code=200,
        json={
            "message": {
                "title": ["Manual de Redacción APA 7"],
                "author": [{"family": "American Psychological Association"}],
                "published-print": {"date-parts": [[2020]]},
            }
        },
    )

    repo = ProjectRepository(in_memory_db)
    rag = RAGService(
        db_manager=in_memory_db,
        project_repo=repo,
        is_memory=True,
    )

    project = ProjectStateDTO(
        id="proj-doc-test-2",
        title="Proyecto de Citaciones",
        academic_level=AcademicLevel.MAESTRIA,
        phase=ProjectPhase.CONTEXT,
    )
    await repo.create_project(project)

    # Add citation
    citation = await rag.add_citation_to_project(
        project_id="proj-doc-test-2",
        doi="10.1000/182",
        title="Manual de Redacción APA 7",
        authors=["American Psychological Association"],
        year=2020,
    )
    assert citation.id is not None
    assert citation.apa_formatted != ""

    proj_after_add = await repo.get_project("proj-doc-test-2")
    assert len(proj_after_add.validated_citations) == 1

    # Remove citation
    proj_after_add.validated_citations = [
        c for c in proj_after_add.validated_citations if c.id != citation.id
    ]
    await repo.update_project(proj_after_add)

    proj_after_del = await repo.get_project("proj-doc-test-2")
    assert len(proj_after_del.validated_citations) == 0
