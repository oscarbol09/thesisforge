"""Unit tests for JuryService facade and high-level project workflows."""

import pytest

from thesisforge.jury.service import JuryService
from thesisforge.models import (
    AcademicLevel,
    CitationDTO,
    DefenseStatus,
    MethodologyDTO,
    ProjectPhase,
    ProjectStateDTO,
    ResearchApproach,
)
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.jury_repository import JuryRepository
from thesisforge.repository.project_repository import ProjectRepository


@pytest.fixture
def sample_project() -> ProjectStateDTO:
    """Fixture providing a project ready for jury audit and defense."""
    return ProjectStateDTO(
        id="proj-service-test-01",
        title="Evaluación de Agentes Multi-Modelo en Tareas de Programación",
        academic_level=AcademicLevel.MAESTRIA,
        phase=ProjectPhase.DRAFTING,
        research_problem="Los modelos de lenguaje individuales presentan sesgos y alucinaciones en código complejo.",
        research_question="¿Cómo mejora el rendimiento de generación de código un ensamble multi-agente?",
        general_objective="Determinar la ganancia en precisión de un sistema multi-agente frente a modelos individuales.",
        specific_objectives=[
            "Medir la tasa de éxito de modelos individuales en benchmarks estándar.",
            "Diseñar un protocolo de consenso y debate entre agentes.",
            "Comparar la cobertura de pruebas generadas por ambos enfoques.",
        ],
        hypothesis="El ensamble multi-agente supera en un 25% la tasa de éxito en el benchmark HumanEval.",
        methodology=MethodologyDTO(
            approach=ResearchApproach.CUANTITATIVO,
            design="Experimental comparativo",
            population="164 problemas del benchmark HumanEval",
            sample="164 problemas evaluados en 3 repeticiones",
            instruments=["Pipeline de ejecución hermética Docker"],
            analysis_technique="Prueba de rangos con signo de Wilcoxon",
        ),
        validated_citations=[
            CitationDTO(
                title="Multi-Agent Software Engineering",
                authors=["Hong, S.", "Zheng, T."],
                year=2024,
                doi="10.1145/3611643.3616281",
            ),
            CitationDTO(
                title="Evaluating Large Language Models for Code",
                authors=["Chen, M.", "Tworek, J."],
                year=2021,
                doi="10.48550/arXiv.2107.03374",
            ),
            CitationDTO(
                title="Self-Refinement in LLM Coding",
                authors=["Madaan, A."],
                year=2023,
                doi="10.48550/arXiv.2303.17651",
            ),
        ],
    )


@pytest.mark.asyncio
async def test_jury_service_audit_and_retrieval(
    in_memory_db: DatabaseManager,
    sample_project: ProjectStateDTO,
) -> None:
    """Test full project audit workflow via JuryService."""
    proj_repo = ProjectRepository(in_memory_db)
    jury_repo = JuryRepository(in_memory_db)
    await proj_repo.create_project(sample_project)

    service = JuryService(
        db_manager=in_memory_db,
        project_repo=proj_repo,
        jury_repo=jury_repo,
        llm_router=None,
    )

    # Execute Audit
    report = await service.audit_project("proj-service-test-01")
    assert report.project_id == "proj-service-test-01"
    assert report.overall_score >= 70.0
    assert len(report.juror_evaluations) == 4

    # Verify project phase transition to REVIEW
    updated_project = await proj_repo.get_project("proj-service-test-01")
    assert updated_project.phase == ProjectPhase.REVIEW

    # Retrieve latest evaluation
    latest = await service.get_latest_evaluation("proj-service-test-01")
    assert latest is not None
    assert latest.id == report.id

    # List evaluations
    all_evals = await service.list_evaluations("proj-service-test-01")
    assert len(all_evals) == 1

    # Get by ID
    by_id = await service.get_evaluation(report.id)
    assert by_id.id == report.id


@pytest.mark.asyncio
async def test_jury_service_defense_workflow(
    in_memory_db: DatabaseManager,
    sample_project: ProjectStateDTO,
) -> None:
    """Test starting defense and completing all turns via JuryService."""
    proj_repo = ProjectRepository(in_memory_db)
    jury_repo = JuryRepository(in_memory_db)
    await proj_repo.create_project(sample_project)

    service = JuryService(
        db_manager=in_memory_db,
        project_repo=proj_repo,
        jury_repo=jury_repo,
        llm_router=None,
    )

    # Start defense session
    session = await service.start_defense_session("proj-service-test-01")
    assert session.status == DefenseStatus.IN_PROGRESS
    assert session.current_turn_index == 0

    # Answer all 4 turns
    answers = [
        "Para controlar la validez interna se utilizó un contenedor Docker aislado y determinismo con semilla fija.",
        "El marco teórico se basa en los principios de agentes cooperativos y arquitecturas de debate socrático.",
        "Se aplicó la prueba no paramétrica de Wilcoxon dado que las diferencias no cumplían el supuesto de normalidad.",
        "Como limitación, los resultados se circunscriben a problemas de complejidad algorítmica y no a proyectos de software extensos.",
    ]

    for idx, ans in enumerate(answers):
        session = await service.submit_defense_answer(
            session_id=session.id,
            turn_index=idx,
            student_answer=ans,
        )

    assert session.status in (DefenseStatus.PASSED, DefenseStatus.PASSED_WITH_HONORS)
    assert session.final_score is not None
    assert session.final_score >= 70.0

    # Check project completed phase
    proj = await proj_repo.get_project("proj-service-test-01")
    assert proj.phase == ProjectPhase.COMPLETED
