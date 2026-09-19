"""Integration tests for AdvisorService and interview orchestration."""

from unittest.mock import AsyncMock, patch

import pytest

from thesisforge.advisor.service import AdvisorService
from thesisforge.advisor.state_machine import AdvisorStep
from thesisforge.llm.router import LLMRouter
from thesisforge.models import (
    AcademicLevel,
    ProjectPhase,
    ProjectStateDTO,
)
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


@pytest.mark.asyncio
async def test_advisor_interview_progression_and_approval(in_memory_db: DatabaseManager):
    """Test executing interview steps, consistency audit, and final phase approval."""
    repo = ProjectRepository(in_memory_db)
    router = LLMRouter()
    service = AdvisorService(project_repo=repo, llm_router=router)

    # 1. Initialize project
    initial_project = ProjectStateDTO(
        id="proj-interview-01",
        title="Estudio de Sistemas RAG",
        academic_level=AcademicLevel.PREGRADO,
        phase=ProjectPhase.ORIENTATION,
    )
    await repo.create_project(initial_project)

    # 2. Step: TOPIC_AND_AREA
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

    # 3. Step: PROBLEM_STATEMENT with mocked LLM refinement
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

    # 4. Step: OBJECTIVES
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

    # 5. Step: HYPOTHESIS
    await service.process_step(
        project_id="proj-interview-01",
        step=AdvisorStep.HYPOTHESIS,
        user_input="El uso de un pipeline RAG reduce significativamente la tasa de referencias alucinadas en comparación con un LLM base.",
    )

    # 6. Step: METHODOLOGY_DESIGN
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

    # 7. Check interview status
    status_info = await service.get_interview_status("proj-interview-01")
    assert status_info["can_advance"] is True
    assert status_info["audit"]["score"] == 100

    # 8. Approve and advance to CONTEXT phase
    advanced_project = await service.approve_methodology("proj-interview-01")
    assert advanced_project.phase == ProjectPhase.CONTEXT
