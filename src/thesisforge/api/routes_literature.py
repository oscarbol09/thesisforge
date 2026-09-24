"""FastAPI router for academic literature search, PDF ingestion, semantic RAG, and APA 7 citation."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field

from thesisforge.api.deps import get_rag_service
from thesisforge.core.logging import get_logger
from thesisforge.exceptions import DocumentProcessingError
from thesisforge.models import (
    AcademicSearchResultDTO,
    CitationDTO,
    DocumentChunkDTO,
    EvidenceVerdictDTO,
)
from thesisforge.rag.apa_formatter import APA7Formatter
from thesisforge.rag.service import RAGService

logger = get_logger(__name__)

router = APIRouter(prefix="/api/literature", tags=["Literature & RAG"])


class VerifyDOIRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    doi: str = Field(min_length=3, max_length=100)


class QueryContextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: str = Field(min_length=1)
    query: str = Field(min_length=3)
    top_k: int = Field(default=5, ge=1, le=20)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    section_filter: str | None = None


class VerifyClaimRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: str = Field(min_length=1)
    claim: str = Field(min_length=5)
    top_k: int = Field(default=5, ge=1, le=20)


class APAFormatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    parenthetical: str
    narrative: str
    reference_entry: str


@router.get("/search", response_model=list[AcademicSearchResultDTO])
async def search_literature(
    q: str = Query(..., min_length=2, description="Búsqueda de artículos científicos"),
    limit: int = Query(10, ge=1, le=50),
    source: list[str] | None = Query(
        None, description="Fuentes: semantic_scholar, arxiv, crossref"
    ),
    year_start: int | None = Query(None, ge=1900, le=2100),
    year_end: int | None = Query(None, ge=1900, le=2100),
    rag: RAGService = Depends(get_rag_service),
) -> list[AcademicSearchResultDTO]:
    """Search academic literature across multiple open access registries."""
    return await rag.search_literature(
        query=q,
        limit=limit,
        sources=source,
        year_start=year_start,
        year_end=year_end,
    )


@router.post("/verify-doi")
async def verify_doi(
    request: VerifyDOIRequest,
    rag: RAGService = Depends(get_rag_service),
) -> dict[str, Any]:
    """Verify official DOI existence and retrieve registered bibliographic metadata."""
    is_valid = await rag.citation_guard.verify_doi(request.doi)
    resolved = await rag.crossref.resolve_doi(request.doi) if is_valid else None
    return {
        "doi": request.doi,
        "is_valid": is_valid,
        "metadata": resolved,
    }


MAX_PDF_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB limit


@router.post(
    "/index-pdf", status_code=status.HTTP_201_CREATED, response_model=list[DocumentChunkDTO]
)
async def index_pdf_file(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    title: str | None = Form(None),
    doi: str | None = Form(None),
    rag: RAGService = Depends(get_rag_service),
) -> list[DocumentChunkDTO]:
    """Upload and index a PDF research paper into the project's vector database."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise DocumentProcessingError("El archivo debe ser un documento PDF válido (.pdf).")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise DocumentProcessingError("El archivo subido está vacío.")

    if len(pdf_bytes) > MAX_PDF_UPLOAD_BYTES:
        raise DocumentProcessingError(
            f"El archivo PDF excede el límite máximo permitido de {MAX_PDF_UPLOAD_BYTES // (1024 * 1024)} MB."
        )

    document_id = uuid.uuid4().hex[:10]
    doc_title = title or file.filename.rsplit(".", 1)[0]

    return await rag.index_pdf_document(
        project_id=project_id,
        document_id=document_id,
        pdf_bytes=pdf_bytes,
        title=doc_title,
        doi=doi,
    )


@router.post("/query-context", response_model=list[DocumentChunkDTO])
async def query_relevant_context(
    request: QueryContextRequest,
    rag: RAGService = Depends(get_rag_service),
) -> list[DocumentChunkDTO]:
    """Semantic vector search over indexed papers for drafting chapters."""
    return await rag.query_relevant_chunks(
        project_id=request.project_id,
        query=request.query,
        top_k=request.top_k,
        min_score=request.min_score,
        section_filter=request.section_filter,
    )


@router.post("/verify-claim", response_model=EvidenceVerdictDTO)
async def verify_claim_grounding(
    request: VerifyClaimRequest,
    rag: RAGService = Depends(get_rag_service),
) -> EvidenceVerdictDTO:
    """Verify that a drafted factual statement is substantiated by retrieved literature passages."""
    return await rag.verify_claim(
        project_id=request.project_id,
        claim=request.claim,
        top_k=request.top_k,
    )


@router.post("/format-apa", response_model=APAFormatResponse)
async def format_apa_citation(
    citation: CitationDTO,
) -> APAFormatResponse:
    """Convert citation metadata into APA 7 parenthetical, narrative, and bibliography formats."""
    return APAFormatResponse(
        parenthetical=APA7Formatter.format_parenthetical(citation),
        narrative=APA7Formatter.format_narrative(citation),
        reference_entry=APA7Formatter.format_reference_entry(citation),
    )


@router.post("/citations/{project_id}", response_model=CitationDTO)
async def add_citation_to_project(
    project_id: str,
    citation: CitationDTO,
    rag: RAGService = Depends(get_rag_service),
) -> CitationDTO:
    """Validate and register an academic citation into the master project state."""
    return await rag.add_citation_to_project(
        project_id=project_id,
        doi=citation.doi,
        title=citation.title,
        authors=citation.authors,
        year=citation.year,
        journal=citation.journal,
        abstract=citation.abstract,
        source=citation.source,
    )


@router.post("/prisma-flow/{project_id}")
async def build_prisma_flow(
    project_id: str,
    query: str = Query("", description="Consulta temática de búsqueda"),
    excluded_screening: int = Query(0, ge=0),
    rag: RAGService = Depends(get_rag_service),
) -> dict[str, Any]:
    """Generate or update the PRISMA 2020 Systematic Review Flow Report for the project."""
    report = await rag.build_prisma_flow(
        project_id=project_id,
        query=query,
        excluded_screening=excluded_screening,
    )
    return report.to_dict()
