"""REST API endpoints for compiling and exporting thesis documents."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, File, Response, UploadFile

from thesisforge.api.deps import get_export_service, get_project_bundle_service
from thesisforge.exceptions import ExportError
from thesisforge.models import CitationDTO, ExportOptionsDTO, ProjectStateDTO

if TYPE_CHECKING:
    from thesisforge.export.bundle import ProjectBundleService
    from thesisforge.export.service import ExportService

MAX_BUNDLE_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB

router = APIRouter(prefix="/api/export", tags=["export"])


@router.post("/projects/{project_id}/docx")
async def export_project_docx(
    project_id: str,
    options: ExportOptionsDTO = ExportOptionsDTO(),
    export_service: ExportService = Depends(get_export_service),
) -> Response:
    """Compile thesis project into APA 7th Edition Word document (.docx) attachment."""
    docx_bytes = await export_service.compile_project_docx(project_id, options)
    filename = f"tesis_{project_id}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/projects/{project_id}/bibtex")
async def export_project_bibtex(
    project_id: str,
    export_service: ExportService = Depends(get_export_service),
) -> Response:
    """Compile validated project citations into BibTeX (.bib) file attachment for Zotero and Overleaf."""
    bib_text = await export_service.compile_project_bibtex(project_id)
    filename = f"bibliografia_{project_id}.bib"
    return Response(
        content=bib_text,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/citations/bibtex")
async def export_citations_bibtex(
    citations: list[CitationDTO],
    export_service: ExportService = Depends(get_export_service),
) -> Response:
    """Export an arbitrary list of citations as a BibTeX (.bib) text stream."""
    bib_text = export_service.bibtex_exporter.export_citations(citations)
    filename = "referencias.bib"
    return Response(
        content=bib_text,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/projects/{project_id}/bundle")
async def export_project_bundle(
    project_id: str,
    bundle_service: ProjectBundleService = Depends(get_project_bundle_service),
) -> Response:
    """Export full project state, manifest, citations and drafts as a portable .thesisforge package."""
    bundle_bytes = await bundle_service.export_bundle_bytes(project_id)
    filename = f"proyecto_{project_id}.thesisforge"
    return Response(
        content=bundle_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/bundle/import", response_model=ProjectStateDTO)
async def import_project_bundle(
    file: UploadFile = File(...),
    bundle_service: ProjectBundleService = Depends(get_project_bundle_service),
) -> ProjectStateDTO:
    """Validate and restore a project from an uploaded .thesisforge archive."""
    chunk_size = 1024 * 1024  # 1 MB chunk
    buffer = bytearray()
    while chunk := await file.read(chunk_size):
        buffer.extend(chunk)
        if len(buffer) > MAX_BUNDLE_UPLOAD_BYTES:
            raise ExportError(
                f"El archivo del paquete excede el límite máximo permitido de {MAX_BUNDLE_UPLOAD_BYTES // (1024 * 1024)} MB."
            )
    if not buffer:
        raise ExportError("El archivo del paquete .thesisforge subido está vacío.")
    return await bundle_service.import_bundle_bytes(bytes(buffer))
