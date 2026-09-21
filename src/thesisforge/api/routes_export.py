"""REST API endpoints for compiling and exporting thesis documents."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Response

from thesisforge.api.deps import get_export_service
from thesisforge.models import ExportOptionsDTO

if TYPE_CHECKING:
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
