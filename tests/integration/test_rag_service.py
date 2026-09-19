"""Integration tests for RAGService, PDF indexing, vector retrieval, and citation guard."""

import fitz
import pytest

from thesisforge.models import (
    AcademicLevel,
    ProjectPhase,
    ProjectStateDTO,
)
from thesisforge.rag.service import RAGService
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


@pytest.mark.asyncio
async def test_rag_pdf_indexing_and_vector_query(in_memory_db: DatabaseManager):
    """Verify PDF ingestion, SQLite chunk persistence, and ChromaDB vector retrieval."""
    repo = ProjectRepository(in_memory_db)
    rag_service = RAGService(
        db_manager=in_memory_db,
        project_repo=repo,
        is_memory=True,
    )

    project = ProjectStateDTO(
        id="proj-rag-test-01",
        title="Impacto del RAG en Tesis",
        academic_level=AcademicLevel.PREGRADO,
        phase=ProjectPhase.CONTEXT,
    )
    await repo.create_project(project)

    # Generate synthetic research paper PDF
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text(
        (50, 50),
        "Metodología Experimental\n\n"
        "El presente estudio utilizó un muestreo probabilístico con 120 participantes. "
        "Se midió el tiempo de respuesta y la precisión semántica de las respuestas generadas con RAG. "
        "Los resultados demostraron una reducción del 95% en alucinaciones bibliográficas.",
    )
    pdf_bytes = doc.write()
    doc.close()

    # Index document
    chunks = await rag_service.index_pdf_document(
        project_id="proj-rag-test-01",
        document_id="doc_eval_01",
        pdf_bytes=pdf_bytes,
        title="Evaluación Empírica de RAG",
        doi="10.1000/182",
        authors=["García, Carlos", "Rodríguez, Ana"],
        year=2023,
    )

    assert len(chunks) >= 1
    assert chunks[0].project_id == "proj-rag-test-01"
    assert chunks[0].document_id == "doc_eval_01"

    # Query context
    matched = await rag_service.query_relevant_chunks(
        project_id="proj-rag-test-01",
        query="¿Cuál fue el tamaño de la muestra de participantes y la tasa de alucinaciones?",
        top_k=3,
    )

    assert len(matched) >= 1
    assert "120 participantes" in matched[0].text or "alucinaciones" in matched[0].text


@pytest.mark.asyncio
async def test_rag_claim_evidence_verification(in_memory_db: DatabaseManager):
    """Verify claim validation against indexed literature (DOI Valid != Claim Backed)."""
    repo = ProjectRepository(in_memory_db)
    rag_service = RAGService(
        db_manager=in_memory_db,
        project_repo=repo,
        is_memory=True,
    )

    project = ProjectStateDTO(
        id="proj-rag-test-02",
        title="Prueba de Evidencia",
        academic_level=AcademicLevel.MAESTRIA,
        phase=ProjectPhase.CONTEXT,
    )
    await repo.create_project(project)

    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text(
        (50, 50),
        "Resultados\n\n"
        "La arquitectura RAG con base de conocimiento indexada redujo el error de citación al 0.05%. "
        "No se detectaron alucinaciones de autores en el corpus de evaluación.",
    )
    pdf_bytes = doc.write()
    doc.close()

    await rag_service.index_pdf_document(
        project_id="proj-rag-test-02",
        document_id="doc_claim_01",
        pdf_bytes=pdf_bytes,
        title="RAG Anti-alucinación",
        doi="10.1000/claim1",
        authors=["Pérez, Luis"],
        year=2024,
    )

    # 1. Supported Claim
    supported_verdict = await rag_service.verify_claim(
        project_id="proj-rag-test-02",
        claim="La arquitectura RAG con base de conocimiento redujo el error de citación y alucinaciones.",
    )
    assert supported_verdict.is_supported is True
    assert supported_verdict.confidence_score >= 0.40
    assert len(supported_verdict.supporting_chunks) >= 1
    assert supported_verdict.supporting_chunks[0].supports_claim is True

    # 2. Unsupported Claim
    unsupported_verdict = await rag_service.verify_claim(
        project_id="proj-rag-test-02",
        claim="Los algoritmos cuánticos de encriptación demostraron ser vulnerables a ataques de fuerza bruta espacial.",
    )
    assert unsupported_verdict.is_supported is False


@pytest.mark.asyncio
async def test_rag_add_citation_to_project(in_memory_db: DatabaseManager):
    """Verify adding validated citation appends APA 7 formatting to project state."""
    repo = ProjectRepository(in_memory_db)
    rag_service = RAGService(
        db_manager=in_memory_db,
        project_repo=repo,
        is_memory=True,
    )

    project = ProjectStateDTO(
        id="proj-rag-test-03",
        title="Gestión de Citas",
        academic_level=AcademicLevel.DOCTORADO,
        phase=ProjectPhase.CONTEXT,
    )
    await repo.create_project(project)

    cit = await rag_service.add_citation_to_project(
        project_id="proj-rag-test-03",
        doi="10.1145/3397271.3401075",
        title="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        authors=["Lewis, Patrick", "Perez, Ethan"],
        year=2020,
        journal="Advances in Neural Information Processing Systems",
    )

    assert cit.apa_formatted.startswith("Lewis, P., & Perez, E. (2020).")
    assert "https://doi.org/10.1145/3397271.3401075" in cit.apa_formatted

    updated_proj = await repo.get_project("proj-rag-test-03")
    assert len(updated_proj.validated_citations) == 1
    assert updated_proj.validated_citations[0].title == cit.title
