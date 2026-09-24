"""Integration tests for the newly integrated academic skills and endpoints.

Tests:
1. Consistency matrix API route (GET /api/advisor/{project_id}/consistency-matrix)
2. PRISMA 2020 flow generator route (POST /api/literature/prisma-flow/{project_id})
3. Draft quality audit route (GET /api/drafting/projects/{project_id}/sections/{section_id}/quality-audit)
4. AI failure modes gate route (POST /api/jury/projects/{project_id}/ai-failure-gate)
"""

import pytest
from httpx import ASGITransport, AsyncClient

from thesisforge.api.app import app
from thesisforge.api.deps import get_db_manager
from thesisforge.models import (
    MethodologyDTO,
    ResearchApproach,
    SectionDraftDTO,
    VariableOperationalizationDTO,
    VariableType,
)
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


@pytest.fixture
def override_db(in_memory_db: DatabaseManager):
    """Override database dependency to use in-memory test database."""
    app.dependency_overrides[get_db_manager] = lambda: in_memory_db
    yield in_memory_db
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_academic_capabilities_end_to_end(override_db: DatabaseManager) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create a Project
        create_res = await client.post(
            "/api/projects",
            json={
                "title": "Evaluación del Desempeño Docente y Satisfacción Estudiantil",
                "academic_level": "maestria",
                "area_of_study": "Educación Superior",
                "topic": "Desempeño Docente",
            },
        )
        assert create_res.status_code == 201
        project_data = create_res.json()
        project_id = project_data["id"]

        # 2. Setup project with detailed methodology and variables
        repo = ProjectRepository(override_db)
        proj = await repo.get_project(project_id)
        proj.research_problem = (
            "La evaluación del desempeño docente requiere métricas rigurosas y validez empírica."
        )
        proj.research_question = (
            "¿Cómo se relaciona el desempeño docente con la satisfacción estudiantil?"
        )
        proj.general_objective = (
            "Determinar la relación entre desempeño docente y satisfacción estudiantil."
        )
        proj.specific_objectives = [
            "Medir el desempeño docente según la rúbrica institucional.",
            "Evaluar el nivel de satisfacción de los estudiantes.",
        ]
        proj.hypothesis = (
            "Existe una correlación positiva y significativa entre desempeño y satisfacción."
        )
        proj.operationalized_variables = [
            VariableOperationalizationDTO(
                name="Desempeño Docente",
                variable_type=VariableType.INDEPENDIENTE,
                indicators=["Didáctica", "Puntualidad"],
            ),
            VariableOperationalizationDTO(
                name="Satisfacción Estudiantil",
                variable_type=VariableType.DEPENDIENTE,
                indicators=["Atención", "Claridad"],
            ),
        ]
        proj.methodology = MethodologyDTO(
            approach=ResearchApproach.CUANTITATIVO,
            design="No experimental transversal correlacional",
            analysis_technique="Coeficiente de Spearman",
        )
        proj.sections = [
            SectionDraftDTO(
                section_id="intro",
                title="Introducción",
                content=(
                    "El presente estudio examina la relación pedagógica. "
                    "Diversos autores han señalado este efecto (Hernández et al., 2023, p. 12). "
                    "Los datos respaldan la pertinencia de la evaluación continua."
                ),
            )
        ]
        await repo.update_project(proj)

        # 3. Test Consistency Matrix API
        matrix_res = await client.get(f"/api/advisor/{project_id}/consistency-matrix")
        assert matrix_res.status_code == 200
        matrix_data = matrix_res.json()
        assert "rows" in matrix_data
        assert len(matrix_data["rows"]) == 2
        assert matrix_data["overall_alignment_score"] >= 80.0

        # 4. Test PRISMA 2020 Flow Generator API
        prisma_res = await client.post(
            f"/api/literature/prisma-flow/{project_id}",
            params={"query": "Desempeño docente universitario", "excluded_screening": 2},
        )
        assert prisma_res.status_code == 200
        prisma_data = prisma_res.json()
        assert "identification" in prisma_data
        assert "screening" in prisma_data
        assert "eligibility" in prisma_data
        assert "included" in prisma_data

        # 5. Test Draft Quality Audit API
        quality_res = await client.get(
            f"/api/drafting/projects/{project_id}/sections/intro/quality-audit"
        )
        assert quality_res.status_code == 200
        quality_data = quality_res.json()
        assert "score" in quality_data
        assert "slop_count" in quality_data
        assert "l3_locator_citations_count" in quality_data
        assert quality_data["l3_locator_citations_count"] >= 1

        # 6. Test AI Failure Gate API
        gate_res = await client.post(f"/api/jury/projects/{project_id}/ai-failure-gate")
        assert gate_res.status_code == 200
        gate_data = gate_res.json()
        assert "passed" in gate_data
        assert "risk_score" in gate_data
        assert "evaluated_modes_count" in gate_data
        assert gate_data["evaluated_modes_count"] == 7
