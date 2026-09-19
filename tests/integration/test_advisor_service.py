"""Integration tests for AdvisorService and interview orchestration."""

from unittest.mock import AsyncMock, patch

import pytest

from thesisforge.advisor.service import AdvisorService
from thesisforge.advisor.state_machine import AdvisorStep
from thesisforge.llm.router import LLMRouter
from thesisforge.models import (
    AcademicLevel,
    MethodologyDTO,
    ProjectPhase,
    ProjectStateDTO,
    ResearchApproach,
)
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


@pytest.mark.asyncio
async def test_advisor_interview_progression_and_approval(in_memory_db: DatabaseManager):
    """Verify that a research project transitions through the full Socratic interview to approval."""
    repo = ProjectRepository(in_memory_db)
    router = LLMRouter()
    service = AdvisorService(project_repo=repo, llm_router=router)

    initial_project = ProjectStateDTO(
        id="proj-interview-01",
        title="Estudio de Sistemas RAG",
        academic_level=AcademicLevel.PREGRADO,
        phase=ProjectPhase.ORIENTATION,
    )
    await repo.create_project(initial_project)

    res1 = await service.process_step(
        project_id="proj-interview-01",
        step=AdvisorStep.TOPIC_AND_AREA,
        user_input="",
        form_data={
            "area_of_study": "Inteligencia Artificial",
            "topic": "Sistemas RAG para Redacción",
            "title": "Impacto de RAG en Tesis Académicas",
        },
    )
    assert res1["next_step"] == AdvisorStep.PROBLEM_STATEMENT.value

    mock_problem_json = {
        "refined_problem": "En la educación superior existe alta incidencia de alucinaciones bibliográficas en herramientas de IA sin control estricto de citas.",
        "suggested_questions": [
            "¿Cómo influye un pipeline RAG en la precisión bibliográfica de proyectos de grado?"
        ],
    }
    with patch.object(router, "complete_json", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = mock_problem_json
        res2 = await service.process_step(
            project_id="proj-interview-01",
            step=AdvisorStep.PROBLEM_STATEMENT,
            user_input="Los estudiantes sufren porque la IA inventa citas.",
        )
        assert res2["next_step"] == AdvisorStep.OBJECTIVES.value

    mock_obj_json = {
        "general_objective": "Evaluar la eficacia de un asistente RAG en la reducción de citas erróneas.",
        "specific_objectives": [
            "Diagnosticar la tasa de alucinaciones en LLMs estándar.",
            "Diseñar un indexador semántico para literatura académica.",
            "Validar la calidad de las referencias en borradores de tesis.",
        ],
        "variables_or_categories": ["Tasa de citas erróneas", "Precisión contextual"],
    }
    with patch.object(router, "complete_json", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = mock_obj_json
        res3 = await service.process_step(
            project_id="proj-interview-01",
            step=AdvisorStep.OBJECTIVES,
            user_input="Quiero diagnosticar, diseñar y validar el sistema.",
        )
        assert res3["project_state"].general_objective.startswith("Evaluar")

    await service.process_step(
        project_id="proj-interview-01",
        step=AdvisorStep.HYPOTHESIS,
        user_input="El uso de un pipeline RAG reduce significativamente la tasa de referencias alucinadas en comparación con un LLM base.",
    )

    await service.process_step(
        project_id="proj-interview-01",
        step=AdvisorStep.METHODOLOGY_DESIGN,
        user_input="",
        form_data={
            "approach": "cuantitativo",
            "design": "Cuasiexperimental con preprueba y posprueba",
            "population": "50 estudiantes de ingeniería",
            "sample": "Muestreo no probabilístico por conveniencia (n=30)",
            "instruments": ["Rúbrica de evaluación APA 7", "Cuestionario de satisfacción"],
            "analysis_technique": "Prueba t de Student para muestras emparejadas",
        },
    )

    status_info = await service.get_interview_status("proj-interview-01")
    assert status_info["can_advance"] is True
    assert status_info["audit"]["score"] == 100

    advanced_project = await service.approve_methodology("proj-interview-01")
    assert advanced_project.phase == ProjectPhase.CONTEXT


@pytest.mark.asyncio
async def test_qualitative_interview_progression_skips_hypothesis(
    in_memory_db: DatabaseManager,
):
    """Verify that qualitative research projects properly skip hypothesis step in progress calculation."""
    repo = ProjectRepository(in_memory_db)
    router = LLMRouter()
    service = AdvisorService(project_repo=repo, llm_router=router)

    project = ProjectStateDTO(
        id="proj-interview-qual-01",
        title="Experiencias de Tesistas con Asistentes IA",
        academic_level=AcademicLevel.MAESTRIA,
        phase=ProjectPhase.ORIENTATION,
        area_of_study="Ciencias de la Educación",
        topic="Adopción tecnológica en posgrados",
        research_problem="Existe desconocimiento sobre la vivencia fenomenológica de los tesistas al usar herramientas de IA.",
        research_question="¿Cómo describen los estudiantes de posgrado su proceso de escritura asistida por IA?",
        general_objective="Comprender las experiencias de estudiantes de posgrado en el uso de IA para redacción.",
        specific_objectives=[
            "Explorar las percepciones de autoeficacia en la redacción.",
            "Describir las tensiones éticas experimentadas por los tesistas.",
        ],
        methodology=MethodologyDTO(
            approach=ResearchApproach.CUALITATIVO,
            design="Fenomenológico",
            population="Estudiantes de maestría",
            sample="12 participantes seleccionados por criterio",
            instruments=["Entrevistas en profundidad semiestructuradas"],
            analysis_technique="Análisis temático de Braun y Clarke",
        ),
    )

    await repo.create_project(project)

    status_info = await service.get_interview_status("proj-interview-qual-01")
    assert AdvisorStep.HYPOTHESIS.value in status_info["skipped_steps"]
    assert status_info["can_advance"] is True
    assert status_info["progress_percentage"] == 100
