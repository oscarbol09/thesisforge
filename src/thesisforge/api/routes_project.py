"""REST API endpoints for Project CRUD."""

from fastapi import APIRouter, Depends, Header, status

from thesisforge.api.deps import get_project_repository, get_rag_service
from thesisforge.core.auth import get_current_owner
from thesisforge.models import (
    ProjectCreateDTO,
    ProjectPhase,
    ProjectStateDTO,
    ProjectSummaryDTO,
)
from thesisforge.rag.service import RAGService
from thesisforge.repository.project_repository import ProjectRepository

router = APIRouter(
    prefix="/api/projects",
    tags=["projects"],
    dependencies=[Depends(get_current_owner)],
)


@router.post("", response_model=ProjectStateDTO, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreateDTO,
    repo: ProjectRepository = Depends(get_project_repository),
    owner_id: str = Depends(get_current_owner),
) -> ProjectStateDTO:
    """Create a new research project."""
    project = ProjectStateDTO(
        title=payload.title,
        academic_level=payload.academic_level,
        area_of_study=payload.area_of_study,
        topic=payload.topic,
        language=payload.language,
        phase=ProjectPhase.ORIENTATION,
        owner_id=owner_id,
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
    x_project_version: int | None = Header(
        default=None,
        alias="X-Project-Version",
        description=(
            "Versión optimista del proyecto leída en el GET previo. "
            "Si se omite, la actualización es sin control de concurrencia (blind write). "
            "Se recomienda siempre enviarla para evitar pérdida de datos concurrente."
        ),
    ),
) -> ProjectStateDTO:
    """Update project state.

    Supports optimistic concurrency control via the X-Project-Version header.
    If provided and the stored version differs, returns HTTP 409 Conflict.
    """
    project.id = project_id
    if x_project_version is not None:
        return await repo.update_project_versioned(project, expected_version=x_project_version)
    return await repo.update_project(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    repo: ProjectRepository = Depends(get_project_repository),
    rag_service: RAGService = Depends(get_rag_service),
) -> None:
    """Delete a project by ID and clean up its SQLite records and ChromaDB vector collection."""
    await repo.delete_project(project_id)
    await rag_service.vector_store.delete_project_collection(project_id)
