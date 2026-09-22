"""REST API endpoints for thesis jury evaluation and automated scientific audit."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from thesisforge.api.deps import get_jury_service
from thesisforge.core.logging import get_logger
from thesisforge.jury.service import JuryService
from thesisforge.models import JuryEvaluationReportDTO

logger = get_logger(__name__)

router = APIRouter(prefix="/api/jury", tags=["Jury & Thesis Audit"])


class ProjectAuditResponse(BaseModel):
    """Response DTO for project audit execution."""

    model_config = ConfigDict(extra="forbid")

    success: bool = True
    project_id: str
    report: JuryEvaluationReportDTO


@router.post(
    "/projects/{project_id}/audit",
    response_model=ProjectAuditResponse,
    status_code=status.HTTP_200_OK,
    summary="Ejecutar auditoría de jurado evaluador multi-agente",
)
async def audit_project_endpoint(
    project_id: str,
    jury_service: JuryService = Depends(get_jury_service),
) -> ProjectAuditResponse:
    """Execute complete multi-perspective scientific jury audit on a research project."""
    report = await jury_service.audit_project(project_id)
    return ProjectAuditResponse(
        success=True,
        project_id=project_id,
        report=report,
    )


@router.get(
    "/projects/{project_id}/evaluations/latest",
    response_model=JuryEvaluationReportDTO,
    status_code=status.HTTP_200_OK,
    summary="Obtener el dictamen de jurado más reciente de un proyecto",
)
async def get_latest_project_evaluation_endpoint(
    project_id: str,
    jury_service: JuryService = Depends(get_jury_service),
) -> JuryEvaluationReportDTO:
    """Fetch the most recent jury audit report for the given project."""
    report = await jury_service.get_latest_evaluation(project_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El proyecto '{project_id}' no cuenta con dictámenes de jurado registrados.",
        )
    return report


@router.get(
    "/projects/{project_id}/evaluations",
    response_model=list[JuryEvaluationReportDTO],
    status_code=status.HTTP_200_OK,
    summary="Listar historial de dictámenes de jurado de un proyecto",
)
async def list_project_evaluations_endpoint(
    project_id: str,
    jury_service: JuryService = Depends(get_jury_service),
) -> list[JuryEvaluationReportDTO]:
    """Retrieve all historical evaluation reports generated for a project."""
    return await jury_service.list_evaluations(project_id)


@router.get(
    "/evaluations/{evaluation_id}",
    response_model=JuryEvaluationReportDTO,
    status_code=status.HTTP_200_OK,
    summary="Consultar un dictamen de jurado específico por ID",
)
async def get_evaluation_by_id_endpoint(
    evaluation_id: str,
    jury_service: JuryService = Depends(get_jury_service),
) -> JuryEvaluationReportDTO:
    """Retrieve an exact jury evaluation report by its primary ID."""
    return await jury_service.get_evaluation(evaluation_id)
