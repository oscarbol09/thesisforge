"""REST API endpoints for the Methodological Advisor."""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from thesisforge.advisor.service import AdvisorService
from thesisforge.advisor.state_machine import AdvisorStep
from thesisforge.api.deps import get_advisor_service
from thesisforge.models import ProjectStateDTO

router = APIRouter(prefix="/api/advisor", tags=["advisor"])


class AdvisorStepRequest(BaseModel):
    """Request payload for processing an interview step."""

    model_config = ConfigDict(extra="ignore")

    step: AdvisorStep
    user_input: str = Field(default="", max_length=10000)
    form_data: dict[str, Any] = Field(default_factory=dict)


@router.get("/{project_id}/status")
async def get_advisor_status(
    project_id: str,
    service: AdvisorService = Depends(get_advisor_service),
) -> dict[str, Any]:
    """Retrieve current interview state, progress, and consistency audit."""
    return await service.get_interview_status(project_id)


@router.post("/{project_id}/step")
async def process_advisor_step(
    project_id: str,
    payload: AdvisorStepRequest,
    service: AdvisorService = Depends(get_advisor_service),
) -> dict[str, Any]:
    """Process a single step in the methodological interview."""
    return await service.process_step(
        project_id=project_id,
        step=payload.step,
        user_input=payload.user_input,
        form_data=payload.form_data,
    )


@router.post("/{project_id}/approve", response_model=ProjectStateDTO)
async def approve_project_methodology(
    project_id: str,
    service: AdvisorService = Depends(get_advisor_service),
) -> ProjectStateDTO:
    """Approve methodology and transition project to Phase 2 (Context)."""
    return await service.approve_methodology(project_id)


@router.get("/{project_id}/consistency-matrix")
async def get_consistency_matrix(
    project_id: str,
    service: AdvisorService = Depends(get_advisor_service),
) -> dict[str, Any]:
    """Retrieve or construct the 6-pillar methodological consistency matrix and validity audit."""
    matrix = await service.get_consistency_matrix(project_id)
    return matrix.model_dump()

