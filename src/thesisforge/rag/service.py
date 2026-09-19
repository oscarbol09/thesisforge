"""High-level RAG orchestrator integrating literature search, parsing, vector index, and citation validation."""

import json

from thesisforge.core.logging import get_logger
from thesisforge.core.time import format_iso_utc
from thesisforge.exceptions import DocumentProcessingError
from thesisforge.llm.router import LLMRouter
from thesisforge.models import (
    AcademicSearchResultDTO,
    CitationDTO,
    DocumentChunkDTO,
    EvidenceVerdictDTO,
)
from thesisforge.rag.apa_formatter import APA7Formatter
from thesisforge.rag.cache import LiteratureCache
from thesisforge.rag.citation_guard import CitationGuard
from thesisforge.rag.clients.aggregator import AcademicSearchAggregator
from thesisforge.rag.clients.arxiv import ArxivClient
from thesisforge.rag.clients.crossref import CrossRefClient
from thesisforge.rag.clients.semantic_scholar import SemanticScholarClient
from thesisforge.rag.parser import PDFDocumentParser
from thesisforge.rag.vectorstore import ChromaVectorStore
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository

logger = get_logger(__name__)


class RAGService:
    """Unified service for academic search, PDF parsing, semantic vector indexing, and evidence verification."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        project_repo: ProjectRepository,
        llm_router: LLMRouter | None = None,
        persist_dir: str = "data/chroma",
        is_memory: bool = False,
        candidate_threshold: float = 0.25,
        support_threshold: float = 0.40,
    ) -> None:
        self.db = db_manager
        self.repo = project_repo
        self.llm = llm_router
        self.cache = LiteratureCache(db_manager)

        # Clients
        self.semantic_scholar = SemanticScholarClient(cache=self.cache)
        self.arxiv = ArxivClient(cache=self.cache)
        self.crossref = CrossRefClient(cache=self.cache)
        self.aggregator = AcademicSearchAggregator(
            semantic_scholar=self.semantic_scholar,
            arxiv=self.arxiv,
            crossref=self.crossref,
        )

        # Vector Store & Parser
        self.vector_store = ChromaVectorStore(
            persist_directory=persist_dir,
            llm_router=self.llm,
            is_memory=is_memory,
        )
        self.parser = PDFDocumentParser()
        self.citation_guard = CitationGuard(
            crossref_client=self.crossref,
            llm_router=self.llm,
            candidate_threshold=candidate_threshold,
            support_threshold=support_threshold,
        )

    async def search_literature(
        self,
        query: str,
        limit: int = 10,
        sources: list[str] | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
    ) -> list[AcademicSearchResultDTO]:
        """Search academic sources with automatic caching and deduplication."""
        return await self.aggregator.search(
            query=query,
            limit_per_source=limit,
            sources=sources,
            year_start=year_start,
            year_end=year_end,
        )

    async def index_pdf_document(
        self,
        project_id: str,
        document_id: str,
        pdf_bytes: bytes,
        title: str = "",
        doi: str | None = None,
        authors: list[str] | None = None,
        year: int | None = None,
    ) -> list[DocumentChunkDTO]:
        """Extract text from PDF, chunk into sentence-aware units, and index into SQLite and ChromaDB."""
        # Ensure project exists
        await self.repo.get_project(project_id)

        chunks = self.parser.parse_pdf_bytes(
            pdf_bytes=pdf_bytes,
            project_id=project_id,
            document_id=document_id,
            title=title,
            doi=doi,
            authors=authors,
            year=year,
        )

        if not chunks:
            raise DocumentProcessingError(
                "No se pudieron extraer fragmentos de texto válidos del documento PDF."
            )

        # 1. Persist chunks in SQLite
        query = """
            INSERT OR REPLACE INTO document_chunks (
                id, project_id, document_id, chunk_index, page_number,
                section_name, text, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        async with self.db.get_connection() as conn:
            for chunk in chunks:
                meta = {
                    "title": chunk.title,
                    "doi": chunk.doi,
                    "authors": chunk.authors,
                    "year": chunk.year,
                    "char_start": chunk.char_start,
                    "char_end": chunk.char_end,
                }
                await conn.execute(
                    query,
                    (
                        chunk.id,
                        chunk.project_id,
                        chunk.document_id,
                        chunk.chunk_index,
                        chunk.page_number,
                        chunk.section_name,
                        chunk.text,
                        json.dumps(meta, ensure_ascii=False),
                        format_iso_utc(chunk.created_at),
                    ),
                )
            await conn.commit()

        # 2. Add to ChromaDB vector store
        await self.vector_store.add_chunks(project_id=project_id, chunks=chunks)
        return chunks

    async def query_relevant_chunks(
        self,
        project_id: str,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        section_filter: str | None = None,
    ) -> list[DocumentChunkDTO]:
        """Retrieve top semantic chunks matching a research question or topic."""
        return await self.vector_store.query_chunks(
            project_id=project_id,
            query=query,
            top_k=top_k,
            min_score=min_score,
            section_filter=section_filter,
        )

    async def add_citation_to_project(
        self,
        project_id: str,
        doi: str | None = None,
        title: str = "",
        authors: list[str] | None = None,
        year: int | None = None,
        journal: str | None = None,
        abstract: str | None = None,
        source: str = "manual",
    ) -> CitationDTO:
        """Validate and append an academic citation to the project state."""
        project = await self.repo.get_project(project_id)

        # Check DOI if provided
        if doi:
            is_valid_doi = await self.citation_guard.verify_doi(doi)
            if is_valid_doi:
                resolved = await self.crossref.resolve_doi(doi)
                if resolved:
                    title = resolved.title or title
                    authors = resolved.authors or (authors or [])
                    year = resolved.year or year
                    journal = resolved.venue or journal

        cit = CitationDTO(
            doi=doi,
            title=title or "Sin título",
            authors=authors or ["Anónimo"],
            year=year or 2024,
            journal=journal,
            abstract=abstract,
            source=source,
        )
        cit.apa_formatted = APA7Formatter.format_reference_entry(cit)

        # Avoid duplicates in project validated citations
        existing_dois = {c.doi.lower() for c in project.validated_citations if c.doi}
        if not (doi and doi.lower() in existing_dois):
            project.validated_citations.append(cit)
            await self.repo.update_project(project)

        return cit

    async def verify_claim(
        self,
        project_id: str,
        claim: str,
        top_k: int = 5,
    ) -> EvidenceVerdictDTO:
        """Verify if a generated claim has grounding in the indexed project literature."""
        chunks = await self.query_relevant_chunks(
            project_id=project_id,
            query=claim,
            top_k=top_k,
        )
        return await self.citation_guard.verify_claim_evidence(
            claim=claim,
            retrieved_chunks=chunks,
        )
