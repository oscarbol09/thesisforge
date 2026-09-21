"""REST and WebSocket API endpoints for thesis chapter drafting and streaming."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict, Field

from thesisforge.api.deps import (
    get_draft_service,
    get_project_repository,
)
from thesisforge.core.logging import get_logger
from thesisforge.exceptions import ProjectNotFoundError
from thesisforge.models import SectionDraftDTO

if TYPE_CHECKING:
    from thesisforge.drafting.service import DraftService
    from thesisforge.repository.project_repository import ProjectRepository

logger = get_logger(__name__)

router = APIRouter(prefix="/api/drafting", tags=["drafting"])


class GenerateDraftRequest(BaseModel):
    """Payload for triggering LLM draft generation on a section."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    user_instructions: str = Field(default="", max_length=2000)
    custom_prompt: str | None = Field(default=None, max_length=5000)


class UpdateSectionContentRequest(BaseModel):
    """Payload for manually updating section content and user feedback."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    content: str = Field(min_length=0)
    user_feedback: str | None = Field(default=None, max_length=2000)


class RefineDraftRequest(BaseModel):
    """Payload for iteratively refining a section draft."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    user_instructions: str = Field(min_length=1, max_length=3000)


@router.post("/projects/{project_id}/initialize", response_model=list[SectionDraftDTO])
async def initialize_sections(
    project_id: str,
    draft_service: DraftService = Depends(get_draft_service),
) -> list[SectionDraftDTO]:
    """Initialize canonical 5-chapter thesis sections for the project."""
    return await draft_service.initialize_thesis_sections(project_id)


@router.get("/projects/{project_id}/sections", response_model=list[SectionDraftDTO])
async def list_sections(
    project_id: str,
    project_repo: ProjectRepository = Depends(get_project_repository),
) -> list[SectionDraftDTO]:
    """Retrieve all structured section drafts belonging to a project."""
    project = await project_repo.get_project(project_id)
    if not project:
        raise ProjectNotFoundError(f"Proyecto con ID '{project_id}' no encontrado.")
    return sorted(project.sections, key=lambda s: (s.chapter_number, s.order_index))


@router.get("/projects/{project_id}/sections/{section_id}", response_model=SectionDraftDTO)
async def get_section(
    project_id: str,
    section_id: str,
    draft_service: DraftService = Depends(get_draft_service),
) -> SectionDraftDTO:
    """Retrieve a single section draft by ID."""
    return await draft_service.get_section(project_id, section_id)


@router.post("/projects/{project_id}/sections/{section_id}/generate", response_model=SectionDraftDTO)
async def generate_section(
    project_id: str,
    section_id: str,
    req: GenerateDraftRequest = GenerateDraftRequest(),
    draft_service: DraftService = Depends(get_draft_service),
) -> SectionDraftDTO:
    """Generate a chapter section draft using LLM with hierarchical memory."""
    return await draft_service.generate_section_draft(
        project_id=project_id,
        section_id=section_id,
        user_guidance=req.user_instructions,
    )


@router.put("/projects/{project_id}/sections/{section_id}", response_model=SectionDraftDTO)
async def update_section(
    project_id: str,
    section_id: str,
    req: UpdateSectionContentRequest,
    draft_service: DraftService = Depends(get_draft_service),
) -> SectionDraftDTO:
    """Update section content directly or save draft feedback."""
    return await draft_service.update_section_content(
        project_id=project_id,
        section_id=section_id,
        content=req.content,
        user_feedback=req.user_feedback,
    )


@router.post("/projects/{project_id}/sections/{section_id}/refine", response_model=SectionDraftDTO)
async def refine_section(
    project_id: str,
    section_id: str,
    req: RefineDraftRequest,
    draft_service: DraftService = Depends(get_draft_service),
) -> SectionDraftDTO:
    """Iteratively refine an existing draft according to specific user instructions."""
    return await draft_service.revise_section_draft(
        project_id=project_id,
        section_id=section_id,
        user_feedback=req.user_instructions,
    )


@router.post("/projects/{project_id}/sections/{section_id}/approve", response_model=SectionDraftDTO)
async def approve_section(
    project_id: str,
    section_id: str,
    draft_service: DraftService = Depends(get_draft_service),
) -> SectionDraftDTO:
    """Approve a section draft, advance status to APPROVED, and synthesize memory summary."""
    return await draft_service.approve_section(
        project_id=project_id,
        section_id=section_id,
    )


@router.websocket("/ws/{project_id}/{section_id}")
async def websocket_draft_stream(
    websocket: WebSocket,
    project_id: str,
    section_id: str,
    draft_service: DraftService = Depends(get_draft_service),
) -> None:
    """Real-time bidirectional WebSocket connection for live token streaming during generation."""
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        action = data.get("action", "generate")
        instructions = data.get("user_instructions", "")

        if action == "generate":
            async for event in draft_service.stream_section_draft(
                project_id=project_id,
                section_id=section_id,
                user_guidance=instructions,
            ):
                await websocket.send_json(event)

        elif action == "refine":
            async for event in draft_service.stream_revise_section_draft(
                project_id=project_id,
                section_id=section_id,
                user_feedback=instructions,
            ):
                await websocket.send_json(event)

        else:
            await websocket.send_json({
                "event": "error",
                "message": f"Acción desconocida: {action}",
            })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected for section: %s", section_id)
    except Exception as exc:
        logger.error("Error in draft websocket stream: %s", exc)
        with contextlib.suppress(Exception):
            await websocket.send_json({"event": "error", "message": str(exc)})
    finally:
        with contextlib.suppress(Exception):
            await websocket.close()
