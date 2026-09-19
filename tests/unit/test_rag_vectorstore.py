"""Unit tests for ChromaVectorStore and CitationGuard."""

import pytest

from thesisforge.models import DocumentChunkDTO
from thesisforge.rag.citation_guard import CitationGuard
from thesisforge.rag.clients.crossref import CrossRefClient
from thesisforge.rag.vectorstore import ChromaVectorStore


@pytest.mark.asyncio
async def test_chroma_vectorstore_lifecycle():
    """Verify ChromaVectorStore add, query, delete, and collection lifecycle."""
    store = ChromaVectorStore(is_memory=True)

    chunks = [
        DocumentChunkDTO(
            id="chunk_1",
            document_id="doc_1",
            project_id="proj_store_01",
            title="Vector Search",
            doi="10.1000/1",
            authors=["Alice", "Bob"],
            year=2024,
            page_number=1,
            chunk_index=0,
            section_name="Methods",
            text="Vector search uses approximate nearest neighbors with HNSW indexes.",
            char_start=0,
            char_end=65,
        ),
        DocumentChunkDTO(
            id="chunk_2",
            document_id="doc_1",
            project_id="proj_store_01",
            title="Vector Search",
            doi="10.1000/1",
            authors=["Alice", "Bob"],
            year=2024,
            page_number=1,
            chunk_index=1,
            section_name="Results",
            text="Cosine similarity outperformed dot product on normalized embeddings.",
            char_start=66,
            char_end=130,
        ),
    ]

    # 1. Add chunks
    count = await store.add_chunks(project_id="proj_store_01", chunks=chunks)
    assert count == 2

    # 2. Empty query returns empty
    empty_results = await store.query_chunks(project_id="proj_store_01", query="  ")
    assert empty_results == []

    # 3. Query
    results = await store.query_chunks(
        project_id="proj_store_01",
        query="nearest neighbors HNSW",
        top_k=1,
    )
    assert len(results) == 1
    assert "HNSW" in results[0].text

    # 4. Delete document
    deleted = await store.delete_document(project_id="proj_store_01", document_id="doc_1")
    assert deleted == 1

    # 5. Delete project collection
    await store.delete_project_collection(project_id="proj_store_01")


@pytest.mark.asyncio
async def test_citation_guard_claim_evidence_evaluation():
    """Verify CitationGuard claim grounding evaluation without LLM."""
    crossref = CrossRefClient()
    guard = CitationGuard(crossref_client=crossref)

    # 1. Empty claim
    empty_verdict = await guard.verify_claim_evidence(claim="  ", retrieved_chunks=[])
    assert empty_verdict.is_supported is False

    # 2. No chunks
    no_chunks_verdict = await guard.verify_claim_evidence(
        claim="Afirmación sobre redes neuronales", retrieved_chunks=[]
    )
    assert no_chunks_verdict.is_supported is False

    # 3. Grounded chunks
    chunks = [
        DocumentChunkDTO(
            id="c1",
            document_id="d1",
            project_id="p1",
            title="Deep Learning Study",
            doi="10.1000/dl",
            authors=["Goodfellow, Ian"],
            year=2016,
            page_number=45,
            chunk_index=0,
            section_name="Methodology",
            text="Las redes neuronales profundas con regularización dropout reducen el sobreajuste significativamente.",
            char_start=0,
            char_end=100,
        )
    ]

    verdict = await guard.verify_claim_evidence(
        claim="Las redes neuronales con dropout reducen el sobreajuste.",
        retrieved_chunks=chunks,
    )
    assert verdict.is_supported is True
    assert verdict.confidence_score >= 0.40
    assert len(verdict.supporting_chunks) == 1
    assert verdict.supporting_chunks[0].supports_claim is True

    await crossref.close()
