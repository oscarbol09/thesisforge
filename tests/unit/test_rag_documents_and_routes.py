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
    repo = ProjectRepository(in_memory_db, "local")
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

    repo = ProjectRepository(in_memory_db, "local")
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


@pytest.mark.asyncio
async def test_reindex_pdf_document_is_idempotent_and_cleans_old_chunks(
    in_memory_db: DatabaseManager,
):
    """Verify that re-indexing the same document is idempotent and cleans existing chunks (TF-DATA-001)."""
    repo = ProjectRepository(in_memory_db, "local")
    rag = RAGService(
        db_manager=in_memory_db,
        project_repo=repo,
        is_memory=True,
    )

    project = ProjectStateDTO(
        id="proj-idempotent-test",
        title="Proyecto Idempotencia",
        academic_level=AcademicLevel.PREGRADO,
    )
    await repo.create_project(project)

    pdf_bytes = _create_sample_pdf_bytes("Estudio de Idempotencia")

    # 1. First indexing
    chunks_1 = await rag.index_pdf_document(
        project_id="proj-idempotent-test",
        document_id="doc-idempotent-01",
        pdf_bytes=pdf_bytes,
        title="Estudio de Idempotencia v1",
    )
    initial_chunk_count = len(chunks_1)
    assert initial_chunk_count >= 1

    # Check chunks in SQLite
    async with in_memory_db.get_connection() as conn:
        cursor = await conn.execute(
            "SELECT count(*) as cnt FROM document_chunks WHERE project_id = ? AND document_id = ?",
            ("proj-idempotent-test", "doc-idempotent-01"),
        )
        row = await cursor.fetchone()
        assert row["cnt"] == initial_chunk_count

    # 2. Second indexing of the exact same document
    chunks_2 = await rag.index_pdf_document(
        project_id="proj-idempotent-test",
        document_id="doc-idempotent-01",
        pdf_bytes=pdf_bytes,
        title="Estudio de Idempotencia v2",
    )

    # Chunk IDs should be deterministic and chunk count should not double
    assert len(chunks_2) == initial_chunk_count
    assert [c.id for c in chunks_1] == [c.id for c in chunks_2]

    # Verify SQLite still has exactly initial_chunk_count, NOT double
    async with in_memory_db.get_connection() as conn:
        cursor = await conn.execute(
            "SELECT count(*) as cnt FROM document_chunks WHERE project_id = ? AND document_id = ?",
            ("proj-idempotent-test", "doc-idempotent-01"),
        )
        row = await cursor.fetchone()
        assert row["cnt"] == initial_chunk_count


@pytest.mark.asyncio
async def test_reindex_pdf_document_with_different_content(
    in_memory_db: DatabaseManager,
):
    """Verify that re-indexing with different content replaces old chunks and updates citation (TF-TEST-001)."""
    repo = ProjectRepository(in_memory_db, "local")
    rag = RAGService(
        db_manager=in_memory_db,
        project_repo=repo,
        is_memory=True,
    )

    project = ProjectStateDTO(
        id="proj-diff-content-01",
        title="Proyecto Contenido Dinámico",
        academic_level=AcademicLevel.MAESTRIA,
    )
    await repo.create_project(project)

    pdf_v1 = _create_sample_pdf_bytes("Contenido Versión Uno para Evaluación.")
    pdf_v2 = _create_sample_pdf_bytes("Contenido Versión Dos Completamente Modificado.")

    # 1. Index version 1
    chunks_v1 = await rag.index_pdf_document(
        project_id="proj-diff-content-01",
        document_id="doc-diff-01",
        pdf_bytes=pdf_v1,
        title="Estudio Inicial v1",
        doi="10.1234/initial.v1",
    )
    ids_v1 = {c.id for c in chunks_v1}
    assert len(ids_v1) >= 1

    # 2. Index version 2 with different content
    chunks_v2 = await rag.index_pdf_document(
        project_id="proj-diff-content-01",
        document_id="doc-diff-01",
        pdf_bytes=pdf_v2,
        title="Estudio Actualizado v2",
        doi="10.1234/updated.v2",
    )
    ids_v2 = {c.id for c in chunks_v2}
    assert len(ids_v2) >= 1

    # Chunk IDs must differ because content hash changed
    assert ids_v1 != ids_v2

    # Old chunk IDs must no longer exist in SQLite
    async with in_memory_db.get_connection() as conn:
        cursor = await conn.execute(
            "SELECT id FROM document_chunks WHERE project_id = ? AND document_id = ?",
            ("proj-diff-content-01", "doc-diff-01"),
        )
        current_ids = {row["id"] for row in await cursor.fetchall()}
        assert current_ids == ids_v2
        assert not current_ids.intersection(ids_v1)

    # Project citation must be updated
    updated_proj = await repo.get_project("proj-diff-content-01")
    citation = next(c for c in updated_proj.validated_citations if c.id == "doc-diff-01")
    assert citation.title == "Estudio Actualizado v2"
    assert citation.doi == "10.1234/updated.v2"


@pytest.mark.asyncio
async def test_reindex_failure_simulation_preserves_old_chunks_and_allows_recovery(
    in_memory_db: DatabaseManager,
):
    """Verify that failures during re-indexing preserve old SQLite chunks and Chroma can be rebuilt (TF-TEST-002)."""
    from unittest.mock import AsyncMock, patch

    from thesisforge.exceptions import DocumentProcessingError

    repo = ProjectRepository(in_memory_db, "local")
    rag = RAGService(
        db_manager=in_memory_db,
        project_repo=repo,
        is_memory=True,
    )

    project = ProjectStateDTO(
        id="proj-fail-recov-01",
        title="Proyecto Resiliencia RAG",
        academic_level=AcademicLevel.DOCTORADO,
    )
    await repo.create_project(project)

    pdf_v1 = _create_sample_pdf_bytes("Contenido Estable Original.")
    chunks_v1 = await rag.index_pdf_document(
        project_id="proj-fail-recov-01",
        document_id="doc-fail-01",
        pdf_bytes=pdf_v1,
        title="Estudio Original",
    )
    assert len(chunks_v1) >= 1

    # 1. Failure during PDF parsing: invalid corrupted bytes
    with pytest.raises(DocumentProcessingError):
        await rag.index_pdf_document(
            project_id="proj-fail-recov-01",
            document_id="doc-fail-01",
            pdf_bytes=b"invalid-not-a-pdf-corrupted-stream",
            title="Intento Fallido",
        )

    # Verify original chunks are still intact in SQLite
    async with in_memory_db.get_connection() as conn:
        cursor = await conn.execute(
            "SELECT count(*) as cnt FROM document_chunks WHERE project_id = ? AND document_id = ?",
            ("proj-fail-recov-01", "doc-fail-01"),
        )
        row = await cursor.fetchone()
        assert row["cnt"] == len(chunks_v1)

    # 2. Simulate Chroma failure during vector store insertion
    with (
        patch.object(
            rag.vector_store,
            "add_chunks",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Simulated ChromaDB connection drop"),
        ),
        pytest.raises(DocumentProcessingError, match="Error indexando vectores en ChromaDB"),
    ):
        await rag.index_pdf_document(
            project_id="proj-fail-recov-01",
            document_id="doc-fail-01",
            pdf_bytes=pdf_v1,
            title="Estudio Reintento Chroma",
        )

    # Recovery: rebuild Chroma from the persistent SQLite chunks
    rebuilt_count = await rag.rebuild_chroma_from_sqlite("proj-fail-recov-01")
    assert rebuilt_count == len(chunks_v1)
