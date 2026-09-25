"""High-level RAG orchestrator integrating literature search, parsing, vector index, and citation validation."""

import asyncio
import json

from thesisforge.core.logging import get_logger
from thesisforge.core.time import format_iso_utc, utc_now
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
from thesisforge.rag.prisma import PRISMAFlowReport
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

    # ------------------------------------------------------------------
    # Internal helpers: document_index_status lifecycle
    # ------------------------------------------------------------------

    async def _upsert_index_status(
        self,
        project_id: str,
        document_id: str,
        status: str,
        chunk_count: int = 0,
        title: str = "",
        doi: str | None = None,
        error_msg: str | None = None,
    ) -> None:
        """Write or update a row in document_index_status.

        Allowed status values: 'pending' | 'indexed' | 'failed'.
        Keeps ChromaDB state auditable and reconstructible from SQLite.
        """
        now_str = format_iso_utc(utc_now())
        async with self.db.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO document_index_status
                    (document_id, project_id, status, chunk_count, title, doi, error_msg,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id, project_id) DO UPDATE SET
                    status      = excluded.status,
                    chunk_count = excluded.chunk_count,
                    title       = excluded.title,
                    doi         = excluded.doi,
                    error_msg   = excluded.error_msg,
                    updated_at  = excluded.updated_at
                """,
                (
                    document_id,
                    project_id,
                    status,
                    chunk_count,
                    title,
                    doi,
                    error_msg,
                    now_str,
                    now_str,
                ),
            )
            await conn.commit()

    async def get_document_index_statuses(self, project_id: str) -> list[dict[str, object]]:
        """Return indexing status for every document in a project.

        Useful for the UI to show PENDING / INDEXED / FAILED badges per document.
        """
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                """
                SELECT document_id, status, chunk_count, title, doi, error_msg,
                       created_at, updated_at
                FROM document_index_status
                WHERE project_id = ?
                ORDER BY created_at DESC
                """,
                (project_id,),
            )
            rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def rebuild_chroma_from_sqlite(self, project_id: str) -> int:
        """Re-index all INDEXED documents for a project from SQLite into ChromaDB.

        Use after a Chroma data-loss event.  Returns the total number of chunks
        re-indexed.  Documents whose status is PENDING or FAILED are skipped.
        """
        # Fetch all chunk rows for this project from SQLite
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                """
                SELECT dc.id, dc.project_id, dc.document_id, dc.chunk_index,
                       dc.page_number, dc.section_name, dc.text, dc.metadata_json,
                       dc.created_at
                FROM document_chunks dc
                INNER JOIN document_index_status dis
                    ON dc.document_id = dis.document_id
                    AND dc.project_id = dis.project_id
                WHERE dc.project_id = ? AND dis.status = 'indexed'
                ORDER BY dc.document_id, dc.chunk_index
                """,
                (project_id,),
            )
            rows = await cursor.fetchall()

        if not rows:
            logger.info(
                "No indexed documents found in SQLite for Chroma rebuild.",
                extra={"project_id": project_id},
            )
            return 0

        chunks: list[DocumentChunkDTO] = []
        for row in rows:
            meta = json.loads(str(row["metadata_json"]))
            chunks.append(
                DocumentChunkDTO(
                    id=str(row["id"]),
                    project_id=str(row["project_id"]),
                    document_id=str(row["document_id"]),
                    chunk_index=int(row["chunk_index"]),
                    page_number=int(row["page_number"]),
                    section_name=str(row["section_name"]),
                    text=str(row["text"]),
                    title=meta.get("title", ""),
                    doi=meta.get("doi"),
                    authors=meta.get("authors", []),
                    year=meta.get("year"),
                    char_start=meta.get("char_start", 0),
                    char_end=meta.get("char_end", 0),
                )
            )

        indexed_count = await self.vector_store.add_chunks(project_id=project_id, chunks=chunks)
        logger.info(
            "ChromaDB rebuilt from SQLite.",
            extra={"project_id": project_id, "chunk_count": indexed_count},
        )
        return indexed_count

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

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
        """Extract text from PDF, chunk into sentence-aware units, and index into SQLite and ChromaDB.

        Lifecycle written to document_index_status:
            PENDING  → set before any I/O (survives crashes)
            INDEXED  → set after both SQLite and Chroma succeed
            FAILED   → set on any error, with error_msg populated
        """
        # Ensure project exists
        await self.repo.get_project(project_id)

        # Mark as PENDING so the UI knows indexing is in progress
        await self._upsert_index_status(
            project_id=project_id,
            document_id=document_id,
            status="pending",
            title=title,
            doi=doi,
        )

        try:
            chunks = await asyncio.to_thread(
                self.parser.parse_pdf_bytes,
                pdf_bytes=pdf_bytes,
                project_id=project_id,
                document_id=document_id,
                title=title,
                doi=doi,
                authors=authors,
                year=year,
            )
        except Exception as err:
            await self._upsert_index_status(
                project_id=project_id,
                document_id=document_id,
                status="failed",
                title=title,
                doi=doi,
                error_msg=f"PDF parsing failed: {err}",
            )
            raise DocumentProcessingError(
                f"No se pudo procesar el documento PDF '{document_id}': {err}"
            ) from err

        if not chunks:
            await self._upsert_index_status(
                project_id=project_id,
                document_id=document_id,
                status="failed",
                title=title,
                doi=doi,
                error_msg="PDF yielded zero extractable text chunks.",
            )
            raise DocumentProcessingError(
                "No se pudieron extraer fragmentos de texto válidos del documento PDF."
            )

        # 1. Persist chunks in SQLite
        sql_insert = """
            INSERT OR REPLACE INTO document_chunks (
                id, project_id, document_id, chunk_index, page_number,
                section_name, text, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
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
                        sql_insert,
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
        except Exception as err:
            await self._upsert_index_status(
                project_id=project_id,
                document_id=document_id,
                status="failed",
                chunk_count=len(chunks),
                title=title,
                doi=doi,
                error_msg=f"SQLite persist failed: {err}",
            )
            raise DocumentProcessingError(
                f"Error almacenando fragmentos en SQLite para '{document_id}': {err}"
            ) from err

        # 2. Add to ChromaDB vector store
        try:
            await self.vector_store.add_chunks(project_id=project_id, chunks=chunks)
        except Exception as err:
            # SQLite chunks are persisted; mark FAILED so rebuild_chroma_from_sqlite
            # can recover by re-indexing the already-stored chunks.
            await self._upsert_index_status(
                project_id=project_id,
                document_id=document_id,
                status="failed",
                chunk_count=len(chunks),
                title=title,
                doi=doi,
                error_msg=f"ChromaDB indexing failed (SQLite chunks intact): {err}",
            )
            raise DocumentProcessingError(
                f"Error indexando fragmentos en ChromaDB para '{document_id}': {err}"
            ) from err

        # Both SQLite and ChromaDB succeeded → mark INDEXED
        await self._upsert_index_status(
            project_id=project_id,
            document_id=document_id,
            status="indexed",
            chunk_count=len(chunks),
            title=title,
            doi=doi,
        )

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
        title: str | None = None,
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
            title=title or None,
            authors=authors or [],
            year=year or None,
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

    async def build_prisma_flow(
        self,
        project_id: str,
        query: str = "",
        search_results: list[AcademicSearchResultDTO] | None = None,
        excluded_screening: int = 0,
        screening_reasons: dict[str, int] | None = None,
    ) -> PRISMAFlowReport:
        """Construct a formal PRISMA 2020 Flow Report from academic searches and indexed documents."""
        project = await self.repo.get_project(project_id)
        report = PRISMAFlowReport(
            project_id=project_id,
            query_string=query or project.topic or "Revisión Sistemática",
        )

        # Count by source
        if search_results:
            source_breakdown: dict[str, int] = {}
            for res in search_results:
                src = res.source or "semantic_scholar"
                source_breakdown[src] = source_breakdown.get(src, 0) + 1
            for src_name, count in source_breakdown.items():
                report.record_database_search(src_name, count)

            total_found = len(search_results)
            # Deduplicate by title/DOI
            seen = set()
            duplicates = 0
            for r in search_results:
                key = (r.doi or r.title).lower()
                if key in seen:
                    duplicates += 1
                else:
                    seen.add(key)
            report.record_deduplication(duplicates)

            screened = max(0, total_found - duplicates)
            report.record_screening(
                screened=screened,
                excluded=excluded_screening,
                reasons=screening_reasons or {"fuera_de_alcance": excluded_screening},
            )
        else:
            # Derive from project's validated citations
            val_cits = project.validated_citations
            report.record_database_search("manual_o_rag", len(val_cits))
            report.record_deduplication(0)
            report.record_screening(len(val_cits), 0)

        # Eligibility & Included from indexed literature
        included_ids = [
            id_val for c in project.validated_citations if (id_val := c.doi or c.title or c.id)
        ]
        report.record_eligibility(
            sought=len(project.validated_citations),
            not_retrieved=0,
            assessed=len(project.validated_citations),
            excluded=0,
            included_ids=included_ids,
        )

        # Persist in project state
        project.prisma_flow = report.to_dict()
        await self.repo.update_project(project)

        logger.info(
            "Built PRISMA 2020 flow report.",
            extra={
                "project_id": project_id,
                "included_count": report.included.new_studies_included,
            },
        )
        return report
