"""REST API endpoints for Project CRUD."""

from fastapi import APIRouter, Depends, status

from thesisforge.api.deps import get_project_repository
from thesisforge.models import (
    ProjectCreateDTO,
    ProjectPhase,
    ProjectStateDTO,
    ProjectSummaryDTO,
)
from thesisforge.repository.project_repository import ProjectRepository

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectStateDTO, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreateDTO,
    repo: ProjectRepository = Depends(get_project_repository),
) -> ProjectStateDTO:
    """Create a new research project."""
    project = ProjectStateDTO(
        title=payload.title,
        academic_level=payload.academic_level,
        area_of_study=payload.area_of_study,
        topic=payload.topic,
        language=payload.language,
        phase=ProjectPhase.ORIENTATION,
    )
    return await repo.create_project(project)


@router.get("", response_model=list[ProjectSummaryDTO])
async def list_projects(
    repo: ProjectRepository = Depends(get_project_repository),
) -> list[ProjectSummaryDTO]:
    """List all projects summaries."""
    return await repo.list_projects()


@router.get("/{project_id}", response_model=ProjectStateDTO)
async def get_project(
    project_id: str,
    repo: ProjectRepository = Depends(get_project_repository),
) -> ProjectStateDTO:
    """Retrieve full project state by ID."""
    return await repo.get_project(project_id)


@router.put("/{project_id}", response_model=ProjectStateDTO)
async def update_project(
    project_id: str,
    project: ProjectStateDTO,
    repo: ProjectRepository = Depends(get_project_repository),
) -> ProjectStateDTO:
    """Update project state."""
    project.id = project_id
    return await repo.update_project(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    repo: ProjectRepository = Depends(get_project_repository),
) -> None:
    """Delete a project by ID."""
    await repo.delete_project(project_id)
