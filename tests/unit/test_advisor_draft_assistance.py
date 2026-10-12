"""Unit tests for AdvisorService assisted drafting with cumulative context."""

import pytest
from tests.fakes import FakeLLMRouter

from thesisforge.advisor.service import AdvisorService
from thesisforge.exceptions import MethodologyValidationError
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
def mock_advisor_llm_router() -> FakeLLMRouter:
    router = FakeLLMRouter()
    return router


@pytest.mark.asyncio
async def test_assist_drafting_justification_injects_prior_context_and_4_dimensions(
    in_memory_db: DatabaseManager,
    mock_advisor_llm_router: FakeLLMRouter,
) -> None:
    """Verify that drafting justification injects prior title, topic, and problem statement,

    and generates 4 dimensions plus mandatory negative formulation.
    """
    repo = ProjectRepository(in_memory_db, "local")
    project = ProjectStateDTO(
        id="proj-assist-01",
        title="Impacto del RAG en la Tesis Universitaria",
        topic="Sistemas RAG en Educación Superior",
        area_of_study="Ciencias de la Computación",
        academic_level=AcademicLevel.MAESTRIA,
        phase=ProjectPhase.ORIENTATION,
        research_problem="Los estudiantes enfrentan severas dificultades para citar literatura científica relevante...",
        research_question="¿De qué manera el uso de RAG optimiza la precisión en la citación académica?",
        sections=[
            SectionDraftDTO(
                section_id="sec_1_4",
                title="1.4 Justificación e Importancia del Estudio",
                chapter_number=1,
                order_index=4,
                status=SectionStatus.PENDING,
            )
        ],
    )
    await repo.create_project(project)

    mock_advisor_llm_router.canned_json_response = {
        "draft_text": "La presente investigación se justifica en cuatro dimensiones...",
        "dimensions": {
            "teorica": "Aporta a la comprensión de arquitecturas de recuperación de información...",
            "practica_social": "Beneficia directamente a 150 maestrandos reduciendo el tiempo de búsqueda...",
            "metodologica": "Propone un pipeline validado de segmentación semántica...",
            "educativa_institucional": "Fortalece las líneas de investigación en IA de la facultad...",
        },
        "formulacion_negativa": "De no realizarse esta investigación, persistirá una tasa del 40% de alucinación...",
        "critique": "Justificación sólida con cumplimiento de las 4 dimensiones y formulación negativa.",
    }

    advisor = AdvisorService(project_repo=repo, llm_router=mock_advisor_llm_router)
    result = await advisor.assist_drafting(
        project_id="proj-assist-01",
        component="justification",
        user_instructions="Enfocar fuertemente en el beneficio de los estudiantes de posgrado.",
        auto_apply=True,
    )

    # 1. Assert result structure
    assert "draft_text" in result
    assert "dimensions" in result
    assert result["dimensions"]["teorica"] != ""
    assert "formulacion_negativa" in result

    # 2. Assert prior context was injected into the prompt
    assert len(mock_advisor_llm_router.recorded_prompts) == 1
    _, prompt_text = mock_advisor_llm_router.recorded_prompts[0]
    assert "Impacto del RAG en la Tesis Universitaria" in prompt_text
    assert "Sistemas RAG en Educación Superior" in prompt_text
    assert "Los estudiantes enfrentan severas dificultades" in prompt_text
    assert "Enfocar fuertemente en el beneficio" in prompt_text

    # 3. Assert project state and section draft updated
    updated_project = await repo.get_project("proj-assist-01")
    assert updated_project.justification == result["draft_text"]
    sec_1_4 = next(s for s in updated_project.sections if s.section_id == "sec_1_4")
    assert sec_1_4.content == result["draft_text"]
    assert sec_1_4.status == SectionStatus.READY_FOR_REVIEW


@pytest.mark.asyncio
async def test_assist_drafting_objectives_injects_isomorphism_and_bloom(
    in_memory_db: DatabaseManager,
    mock_advisor_llm_router: FakeLLMRouter,
) -> None:
    """Verify that drafting objectives enforces isomorphic OG=PG and Bloom sequence (3 phases)."""
    repo = ProjectRepository(in_memory_db, "local")
    project = ProjectStateDTO(
        id="proj-assist-02",
        title="Evaluación de Algoritmos de Búsqueda Semántica",
        topic="Búsqueda Semántica",
        area_of_study="Ingeniería de Sistemas",
        academic_level=AcademicLevel.PREGRADO,
        research_problem="Inconsistencia en la recuperación de literatura empírica...",
        research_question="¿Cómo influye la búsqueda híbrida en la exhaustividad de la revisión?",
        methodology=MethodologyDTO(approach=ResearchApproach.CUANTITATIVO),
        sections=[
            SectionDraftDTO(
                section_id="sec_1_3",
                title="1.3 Objetivos de la Investigación",
                chapter_number=1,
                order_index=3,
                status=SectionStatus.PENDING,
            )
        ],
    )
    await repo.create_project(project)

    mock_advisor_llm_router.canned_json_response = {
        "general_objective": "Evaluar la influencia de la búsqueda híbrida en la exhaustividad de la revisión académica.",
        "specific_objectives": [
            "Diagnosticar la precisión y exhaustividad actual en la recuperación de literatura.",
            "Implementar un pipeline de búsqueda híbrida combinando BM25 y embeddings densos.",
            "Comparar la exhaustividad de la búsqueda híbrida frente a la búsqueda léxica tradicional.",
        ],
        "draft_text": "Objetivo General: Evaluar la influencia...\nObjetivos Específicos:\n1. Diagnosticar...",
        "variables_or_categories": ["búsqueda híbrida", "exhaustividad de la revisión"],
        "alignment_critique": "Objetivo general isomorfo con verbo de nivel evaluativo acorde al alcance cuantitativo.",
    }

    advisor = AdvisorService(project_repo=repo, llm_router=mock_advisor_llm_router)
    result = await advisor.assist_drafting(
        project_id="proj-assist-02",
        component="objectives",
        user_instructions="Garantizar que los específicos sigan las tres fases (diagnóstico, diseño, comparación).",
        auto_apply=True,
    )

    assert result["general_objective"].startswith("Evaluar")
    assert len(result["specific_objectives"]) == 3
    assert len(mock_advisor_llm_router.recorded_prompts) == 1
    _, prompt_text = mock_advisor_llm_router.recorded_prompts[0]
    assert "¿Cómo influye la búsqueda híbrida" in prompt_text
    assert "Inconsistencia en la recuperación" in prompt_text

    updated_project = await repo.get_project("proj-assist-02")
    assert updated_project.general_objective == result["general_objective"]
    assert len(updated_project.specific_objectives) == 3
    sec_1_3 = next(s for s in updated_project.sections if s.section_id == "sec_1_3")
    assert sec_1_3.content == result["draft_text"]


@pytest.mark.asyncio
async def test_assist_drafting_fails_when_prerequisites_missing(
    in_memory_db: DatabaseManager,
    mock_advisor_llm_router: FakeLLMRouter,
) -> None:
    """Verify that attempting to draft justification or objectives without prerequisite context raises error."""
    repo = ProjectRepository(in_memory_db, "local")
    project = ProjectStateDTO(
        id="proj-assist-03",
        title="",  # Missing title and problem
        academic_level=AcademicLevel.PREGRADO,
    )
    await repo.create_project(project)

    advisor = AdvisorService(project_repo=repo, llm_router=mock_advisor_llm_router)
    with pytest.raises(MethodologyValidationError, match="Faltan datos previos"):
        await advisor.assist_drafting(
            project_id="proj-assist-03",
            component="justification",
        )


@pytest.mark.asyncio
async def test_api_assist_drafting_endpoint(
    in_memory_db: DatabaseManager,
    mock_advisor_llm_router: FakeLLMRouter,
) -> None:
    """Verify POST /api/advisor/{project_id}/assist-draft returns valid response and updates project."""
    import httpx

    from thesisforge.api.app import create_app
    from thesisforge.api.deps import get_advisor_service, get_project_repository
    from thesisforge.core.auth import LOCAL_OWNER_ID, get_current_owner

    repo = ProjectRepository(in_memory_db, "local")
    project = ProjectStateDTO(
        id="proj-assist-api-01",
        title="Estudio de RAG",
        topic="Sistemas RAG",
        academic_level=AcademicLevel.PREGRADO,
        research_problem="Existe dispersión documental...",
        research_question="¿Cómo influye el RAG?",
    )
    await repo.create_project(project)

    mock_advisor_llm_router.canned_json_response = {
        "draft_text": "Texto redactado para la justificación...",
        "dimensions": {
            "teorica": "Aporte conceptual...",
            "practica_social": "Beneficio directo...",
            "metodologica": "Protocolo...",
            "educativa_institucional": "Impacto institucional...",
        },
        "formulacion_negativa": "De no realizarse...",
        "critique": "Aprobado",
    }
    advisor = AdvisorService(project_repo=repo, llm_router=mock_advisor_llm_router)

    app = create_app()
    app.dependency_overrides[get_advisor_service] = lambda: advisor
    app.dependency_overrides[get_project_repository] = lambda: repo
    app.dependency_overrides[get_current_owner] = lambda: LOCAL_OWNER_ID

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/advisor/proj-assist-api-01/assist-draft",
            json={
                "component": "justification",
                "user_instructions": "Hacer énfasis en los estudiantes.",
                "auto_apply": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["draft_text"] == "Texto redactado para la justificación..."
        assert "dimensions" in data
