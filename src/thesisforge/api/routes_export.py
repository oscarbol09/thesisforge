"""REST API endpoints for compiling and exporting thesis documents."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, File, Response, UploadFile

from thesisforge.api.deps import get_export_service, get_project_bundle_service
from thesisforge.models import ExportOptionsDTO, ProjectStateDTO

if TYPE_CHECKING:
    from thesisforge.export.bundle import ProjectBundleService
    from thesisforge.export.service import ExportService

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
    content = await file.read()
    return await bundle_service.import_bundle_bytes(content)
