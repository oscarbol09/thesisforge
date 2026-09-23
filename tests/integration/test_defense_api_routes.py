"""Integration tests for thesis oral defense REST and WebSocket API endpoints."""

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from thesisforge.api.app import app
from thesisforge.api.deps import get_db_manager, get_llm_router
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
def override_deps(in_memory_db: DatabaseManager):
    app.dependency_overrides[get_db_manager] = lambda: in_memory_db
    app.dependency_overrides[get_llm_router] = lambda: None
    yield in_memory_db
    app.dependency_overrides.clear()


@pytest.fixture
async def seeded_defense_project(override_deps: DatabaseManager) -> ProjectStateDTO:
    repo = ProjectRepository(override_deps)
    project = ProjectStateDTO(
        id="proj-api-def-01",
        title="Validación de Redes Neuronales Convolucionales en Detección de Plagas",
        academic_level=AcademicLevel.MAESTRIA,
        phase=ProjectPhase.REVIEW,
        research_problem="Las plagas agrícolas generan pérdidas del 30% en cultivos de café sin detección temprana.",
        research_question="¿Qué arquitectura CNN maximiza la sensibilidad en detección de plagas?",
        general_objective="Desarrollar y evaluar un modelo CNN para detección temprana de plagas.",
        specific_objectives=[
            "Recopilar dataset de imágenes",
            "Entrenar ResNet50 y EfficientNet",
            "Comparar métricas F1",
        ],
        hypothesis="EfficientNetB0 supera en 5 puntos de F1-score a ResNet50.",
        methodology=MethodologyDTO(
            approach=ResearchApproach.CUANTITATIVO,
            design="Experimental comparativo",
            population="5000 imágenes de hojas de café",
            sample="1000 imágenes etiquetadas por fitopatólogos",
            instruments=["Matriz de confusión y curvas Precision-Recall"],
            analysis_technique="Prueba de McNemar y bootstrap para intervalos de confianza",
        ),
        validated_citations=[
            CitationDTO(
                title="Deep Learning for Plant Disease Detection",
                authors=["Mohanty, S."],
                year=2023,
                doi="10.3389/fpls.2023.102000",
            ),
            CitationDTO(
                title="EfficientNet: Rethinking Model Scaling",
                authors=["Tan, M."],
                year=2021,
                doi="10.48550/arXiv.1905.11946",
            ),
        ],
    )
    await repo.create_project(project)
    return project


@pytest.mark.asyncio
async def test_api_defense_rest_flow(
    override_deps: DatabaseManager,
    seeded_defense_project: ProjectStateDTO,
) -> None:
    """Verify start defense, submit answers, and query sessions via REST."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Start defense
        resp_start = await client.post(
            "/api/defense/projects/proj-api-def-01/start",
            json={"force_new": True},
        )
        assert resp_start.status_code == 200
        session_data = resp_start.json()
        session_id = session_data["id"]
        assert session_data["status"] == "in_progress"
        assert session_data["current_turn_index"] == 0
        assert session_data["total_turns"] == 4

        # 2. Submit Turn 0 reply
        resp_reply_0 = await client.post(
            f"/api/defense/sessions/{session_id}/reply",
            json={
                "turn_index": 0,
                "student_answer": (
                    "Para garantizar la validez interna y evitar el sobreajuste, "
                    "utilizamos validación cruzada estratificada de 5 pliegues y data augmentation balanceado."
                ),
            },
        )
        assert resp_reply_0.status_code == 200
        reply_0_data = resp_reply_0.json()
        assert reply_0_data["current_turn_index"] == 1
        assert reply_0_data["turns"][0]["is_answered"] is True
        assert reply_0_data["turns"][0]["turn_score"] is not None

        # 3. Get session by ID
        resp_get = await client.get(f"/api/defense/sessions/{session_id}")
        assert resp_get.status_code == 200
        assert resp_get.json()["id"] == session_id

        # 4. List sessions for project
        resp_list = await client.get("/api/defense/projects/proj-api-def-01/sessions")
        assert resp_list.status_code == 200
        assert len(resp_list.json()) >= 1


def test_api_defense_websocket_flow(
    override_deps: DatabaseManager,
    seeded_defense_project: ProjectStateDTO,
) -> None:
    """Verify interactive thesis defense simulation over WebSocket."""
    with TestClient(app) as test_client:
        # First start a session via REST
        resp_start = test_client.post(
            "/api/defense/projects/proj-api-def-01/start",
            json={"force_new": True},
        )
        session_id = resp_start.json()["id"]

        # Connect WebSocket
        with test_client.websocket_connect(f"/api/defense/ws/{session_id}") as ws:
            # 1. Receive initial session state
            init_msg = ws.receive_json()
            assert init_msg["event"] == "session_state"
            assert init_msg["session"]["id"] == session_id

            # 2. Send reply to turn 0
            ws.send_json(
                {
                    "event": "reply",
                    "turn_index": 0,
                    "student_answer": (
                        "El diseño experimental incluyó partición estratificada por finca y condiciones de iluminación "
                        "para asegurar la representatividad de la muestra y mitigar sesgos de captura."
                    ),
                }
            )

            turn_msg = ws.receive_json()
            assert turn_msg["event"] == "turn_evaluated"
            assert turn_msg["turn"]["is_answered"] is True
            assert turn_msg["turn"]["turn_score"] >= 70.0

            # 3. Send ping
            ws.send_json({"event": "ping"})
            pong_msg = ws.receive_json()
            assert pong_msg["event"] == "pong"


def test_api_defense_websocket_malformed_payload_handling(
    override_deps: DatabaseManager,
    seeded_defense_project: ProjectStateDTO,
) -> None:
    """Verify WebSocket resilience against non-integer turn_index and empty answers without crashing."""
    with TestClient(app) as test_client:
        resp_start = test_client.post(
            "/api/defense/projects/proj-api-def-01/start",
            json={"force_new": True},
        )
        session_id = resp_start.json()["id"]

        with test_client.websocket_connect(f"/api/defense/ws/{session_id}") as ws:
            init_msg = ws.receive_json()
            assert init_msg["event"] == "session_state"

            # 1. Send invalid string turn_index
            ws.send_json(
                {
                    "event": "reply",
                    "turn_index": "not-an-integer",
                    "student_answer": "Respuesta de prueba.",
                }
            )
            err_msg1 = ws.receive_json()
            assert err_msg1["event"] == "error"
            assert "no es un número entero válido" in err_msg1["message"]

            # 2. Send empty student answer
            ws.send_json(
                {
                    "event": "reply",
                    "turn_index": 0,
                    "student_answer": "   ",
                }
            )
            err_msg2 = ws.receive_json()
            assert err_msg2["event"] == "error"
            assert "no puede estar vacía" in err_msg2["message"]

            # 3. Verify connection is still alive with ping
            ws.send_json({"event": "ping"})
            pong = ws.receive_json()
            assert pong["event"] == "pong"
