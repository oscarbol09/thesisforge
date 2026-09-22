"""Integration tests for thesis jury REST API endpoints."""

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from thesisforge.api.app import app
from thesisforge.api.deps import get_db_manager, get_llm_router
from thesisforge.llm.router import LLMRouter
from thesisforge.models import (
    AcademicLevel,
    CitationDTO,
    MethodologyDTO,
    ProjectPhase,
    ProjectStateDTO,
    ResearchApproach,
)
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


@pytest.fixture
def mock_llm_router():
    router = AsyncMock(spec=LLMRouter)
    router.complete_json.return_value = {
        "overall_score": 88.0,
        "verdict": "aprobado",
        "summary_dictamen": "Proyecto aprobado con observaciones menores.",
        "juror_evaluations": [
            {
                "juror_role": "metodologo",
                "juror_name": "Dr. Arístides Valenzuela",
                "dimension_name": "Consistencia Metodológica",
                "score": 90.0,
                "criteria_evaluation": "Diseño cuantitativo adecuado.",
                "feedback": "Aclarar el tamaño del grupo experimental.",
                "strengths": ["Objetivos delimitados"],
                "flaws": [],
            }
        ],
        "issues": [],
        "mandatory_fixes": [],
        "recommended_improvements": ["Añadir detalles del instrumento"],
    }
    return router


@pytest.fixture
def override_deps(in_memory_db: DatabaseManager, mock_llm_router: LLMRouter):
    app.dependency_overrides[get_db_manager] = lambda: in_memory_db
    app.dependency_overrides[get_llm_router] = lambda: mock_llm_router
    yield in_memory_db
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_jury_audit_flow(override_deps: DatabaseManager) -> None:
    """Verify full jury audit execution, latest retrieval, and listing via REST API."""
    repo = ProjectRepository(override_deps)
    project = ProjectStateDTO(
        id="proj-api-jury-01",
        title="Evaluación de Algoritmos Genéticos en Optimización de Rutas",
        academic_level=AcademicLevel.PREGRADO,
        phase=ProjectPhase.DRAFTING,
        research_problem="La congestión vehicular genera pérdidas económicas y retrasos logísticos en el transporte urbano.",
        research_question="¿Cómo optimiza un algoritmo genético las rutas de transporte público?",
        general_objective="Optimizar las rutas de transporte mediante algoritmos genéticos.",
        specific_objectives=["Modelar la red vial", "Implementar operadores genéticos", "Evaluar tiempos de viaje"],
        hypothesis="El algoritmo genético reduce en un 18% los tiempos promedio de recorrido.",
        methodology=MethodologyDTO(
            approach=ResearchApproach.CUANTITATIVO,
            design="Experimental por simulación",
            population="Red de 50 rutas urbanas",
            sample="10 rutas críticas de alta densidad",
            instruments=["Simulador SUMO y métricas de retardo"],
            analysis_technique="Prueba ANOVA de una vía",
        ),
        validated_citations=[
            CitationDTO(
                title="Genetic Algorithms in Transit Network Design",
                authors=["Goldberg, D."],
                year=2023,
                doi="10.1016/j.trb.2023.102000",
            ),
            CitationDTO(
                title="Urban Route Optimization Models",
                authors=["Holland, J."],
                year=2022,
                doi="10.1109/TITS.2022.310000",
            ),
            CitationDTO(
                title="Simulation-Based Traffic Management",
                authors=["Krajzewicz, D."],
                year=2024,
                doi="10.1016/j.simpat.2024.102500",
            ),
        ],
    )
    await repo.create_project(project)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Trigger Audit
        resp_audit = await client.post("/api/jury/projects/proj-api-jury-01/audit")
        assert resp_audit.status_code == 200
        audit_data = resp_audit.json()
        assert audit_data["success"] is True
        assert audit_data["report"]["project_id"] == "proj-api-jury-01"
        assert audit_data["report"]["overall_score"] == 88.0
        evaluation_id = audit_data["report"]["id"]

        # 2. Get Latest Evaluation
        resp_latest = await client.get("/api/jury/projects/proj-api-jury-01/evaluations/latest")
        assert resp_latest.status_code == 200
        latest_data = resp_latest.json()
        assert latest_data["id"] == evaluation_id
        assert latest_data["verdict"] == "aprobado"

        # 3. List Evaluations for Project
        resp_list = await client.get("/api/jury/projects/proj-api-jury-01/evaluations")
        assert resp_list.status_code == 200
        evals_list = resp_list.json()
        assert len(evals_list) == 1

        # 4. Get Evaluation by ID
        resp_by_id = await client.get(f"/api/jury/evaluations/{evaluation_id}")
        assert resp_by_id.status_code == 200
        assert resp_by_id.json()["id"] == evaluation_id


@pytest.mark.asyncio
async def test_api_jury_not_found(override_deps: DatabaseManager) -> None:
    """Verify 404 response for non-existent project evaluations."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/jury/projects/non-existent-proj/evaluations/latest")
        assert resp.status_code == 404

        resp_id = await client.get("/api/jury/evaluations/non-existent-eval-id")
        assert resp_id.status_code == 404
