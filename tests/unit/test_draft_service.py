"""Unit tests for DraftService including generation, streaming, revision, and approvals."""

from unittest.mock import AsyncMock

import pytest

from thesisforge.drafting.service import DraftService
from thesisforge.exceptions import SectionNotFoundError
from thesisforge.llm.router import LLMRouter
from thesisforge.models import (
    AcademicLevel,
    MethodologyDTO,
    ProjectPhase,
    ProjectStateDTO,
    ResearchApproach,
    SectionDraftDTO,
    SectionStatus,
)
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


@pytest.fixture
def mock_llm_router():
    router = AsyncMock(spec=LLMRouter)
    router.complete.return_value = "Este es un borrador académico riguroso sobre el problema de investigación."

    async def mock_stream(*args, **kwargs):
        tokens = ["Este ", "es ", "un ", "borrador ", "en ", "streaming."]
        for t in tokens:
            yield t

    router.stream_completion.side_effect = mock_stream
    return router


@pytest.mark.asyncio
async def test_draft_service_initialize_sections(
    in_memory_db: DatabaseManager,
    mock_llm_router: LLMRouter,
):
    """Verify initialize_thesis_sections populates outline and advances phase to DRAFTING."""
    repo = ProjectRepository(in_memory_db)
    project = ProjectStateDTO(
        id="proj-draft-01",
        title="Estudio de RAG en Tesis",
        academic_level=AcademicLevel.PREGRADO,
        phase=ProjectPhase.ORIENTATION,
        methodology=MethodologyDTO(approach=ResearchApproach.CUANTITATIVO),
    )
    await repo.create_project(project)

    service = DraftService(db_manager=in_memory_db, project_repo=repo, llm_router=mock_llm_router)
    sections = await service.initialize_thesis_sections("proj-draft-01")

    assert len(sections) >= 15
    assert sections[0].section_id == "sec_1_1"
    assert sections[0].status == SectionStatus.PENDING

    updated = await repo.get_project("proj-draft-01")
    assert updated.phase == ProjectPhase.DRAFTING
    assert len(updated.sections) == len(sections)


@pytest.mark.asyncio
async def test_draft_service_get_section_and_not_found(
    in_memory_db: DatabaseManager,
    mock_llm_router: LLMRouter,
):
    """Verify get_section returns target section and raises SectionNotFoundError on invalid ID."""
    repo = ProjectRepository(in_memory_db)
    project = ProjectStateDTO(
        id="proj-draft-02",
        title="Estudio de RAG",
        academic_level=AcademicLevel.MAESTRIA,
        phase=ProjectPhase.DRAFTING,
        sections=[
            SectionDraftDTO(section_id="sec_1_1", title="1.1 Planteamiento", chapter_number=1, order_index=1),
        ],
    )
    await repo.create_project(project)

    service = DraftService(db_manager=in_memory_db, project_repo=repo, llm_router=mock_llm_router)
    sec = await service.get_section("proj-draft-02", "sec_1_1")
    assert sec.title == "1.1 Planteamiento"

    with pytest.raises(SectionNotFoundError):
        await service.get_section("proj-draft-02", "non_existent_section")


@pytest.mark.asyncio
async def test_draft_service_generate_section_draft(
    in_memory_db: DatabaseManager,
    mock_llm_router: LLMRouter,
):
    """Verify generate_section_draft calls LLM, updates word count, status, and version."""
    repo = ProjectRepository(in_memory_db)
    project = ProjectStateDTO(
        id="proj-draft-03",
        title="Estudio de IA",
        academic_level=AcademicLevel.PREGRADO,
        phase=ProjectPhase.DRAFTING,
        research_problem="Falta de rigor en citaciones.",
        sections=[
            SectionDraftDTO(section_id="sec_1_1", title="1.1 Planteamiento", chapter_number=1, order_index=1),
        ],
    )
    await repo.create_project(project)

    service = DraftService(db_manager=in_memory_db, project_repo=repo, llm_router=mock_llm_router)
    draft = await service.generate_section_draft(
        project_id="proj-draft-03",
        section_id="sec_1_1",
        user_guidance="Enfocarse en el contexto de universidades públicas.",
    )

    assert draft.content == "Este es un borrador académico riguroso sobre el problema de investigación."
    assert draft.status == SectionStatus.READY_FOR_REVIEW
    assert draft.word_count == 11
    assert draft.version == 2
    assert mock_llm_router.complete.called


@pytest.mark.asyncio
async def test_draft_service_stream_section_draft(
    in_memory_db: DatabaseManager,
    mock_llm_router: LLMRouter,
):
    """Verify stream_section_draft yields start, token, and complete events."""
    repo = ProjectRepository(in_memory_db)
    project = ProjectStateDTO(
        id="proj-draft-04",
        title="Streaming Test",
        academic_level=AcademicLevel.DOCTORADO,
        phase=ProjectPhase.DRAFTING,
        sections=[
            SectionDraftDTO(section_id="sec_1_2", title="1.2 Preguntas", chapter_number=1, order_index=2),
        ],
    )
    await repo.create_project(project)

    service = DraftService(db_manager=in_memory_db, project_repo=repo, llm_router=mock_llm_router)
    events = []
    async for event in service.stream_section_draft("proj-draft-04", "sec_1_2"):
        events.append(event)

    event_types = [e["event"] for e in events]
    assert event_types[0] == "start"
    assert "token" in event_types
    assert event_types[-1] == "complete"
    assert events[-1]["section"]["content"] == "Este es un borrador en streaming."


@pytest.mark.asyncio
async def test_draft_service_revise_and_approve_section(
    in_memory_db: DatabaseManager,
    mock_llm_router: LLMRouter,
):
    """Verify revise_section_draft and approve_section lifecycle."""
    repo = ProjectRepository(in_memory_db)
    project = ProjectStateDTO(
        id="proj-draft-05",
        title="Approval Test",
        academic_level=AcademicLevel.MAESTRIA,
        phase=ProjectPhase.DRAFTING,
        sections=[
            SectionDraftDTO(
                section_id="sec_5_1",
                title="5.1 Conclusiones",
                chapter_number=5,
                order_index=18,
                content="Borrador previo de conclusiones.",
                status=SectionStatus.READY_FOR_REVIEW,
            ),
        ],
    )
    await repo.create_project(project)

    service = DraftService(db_manager=in_memory_db, project_repo=repo, llm_router=mock_llm_router)

    # 1. Revise
    revised = await service.revise_section_draft(
        project_id="proj-draft-05",
        section_id="sec_5_1",
        user_feedback="Hacer mayor énfasis en el objetivo 3.",
    )
    assert revised.user_feedback == "Hacer mayor énfasis en el objetivo 3."
    assert revised.version == 2

    # 2. Approve (single section project advances to REVIEW)
    mock_llm_router.complete.return_value = "Resumen sintético de conclusiones del proyecto."
    approved = await service.approve_section("proj-draft-05", "sec_5_1")
    assert approved.status == SectionStatus.APPROVED
    assert approved.summary == "Resumen sintético de conclusiones del proyecto."

    updated_proj = await repo.get_project("proj-draft-05")
    assert updated_proj.phase == ProjectPhase.REVIEW
