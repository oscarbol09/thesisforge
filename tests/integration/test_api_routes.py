"""Integration tests for FastAPI REST routes."""

import pytest
from httpx import ASGITransport, AsyncClient

from thesisforge.api.app import app
from thesisforge.api.deps import get_db_manager
from thesisforge.repository.database import DatabaseManager


@pytest.fixture
def override_db(in_memory_db: DatabaseManager):
    """Override database dependency to use in-memory test database."""
    app.dependency_overrides[get_db_manager] = lambda: in_memory_db
    yield in_memory_db
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_and_version(override_db: DatabaseManager):
    """Test health check and version metadata endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp_health = await client.get("/health")
        assert resp_health.status_code == 200
        assert resp_health.json()["status"] == "ok"

        resp_ver = await client.get("/api/version")
        assert resp_ver.status_code == 200
        assert "version" in resp_ver.json()

        # Check security headers
        assert resp_health.headers["X-Content-Type-Options"] == "nosniff"
        assert resp_health.headers["X-Frame-Options"] == "DENY"


@pytest.mark.asyncio
async def test_project_crud_and_advisor_endpoints(override_db: DatabaseManager):
    """Verify full HTTP lifecycle for project creation, advisor step submission, and deletion."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/projects",
            json={
                "title": "Tesis sobre Algoritmos Genéticos",
                "academic_level": "pregrado",
                "area_of_study": "Ciencias de la Computación",
                "topic": "Optimización de Rutas",
            },
        )
        assert create_resp.status_code == 201
        created_data = create_resp.json()
        project_id = created_data["id"]
        assert project_id is not None

        get_resp = await client.get(f"/api/projects/{project_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["title"] == "Tesis sobre Algoritmos Genéticos"

        status_resp = await client.get(f"/api/advisor/{project_id}/status")
        assert status_resp.status_code == 200
        status_json = status_resp.json()
        assert status_json["current_step"] == "problem_statement"

        step_resp = await client.post(
            f"/api/advisor/{project_id}/step",
            json={
                "step": "research_question",
                "user_input": "¿Cómo optimizar la planificación de rutas mediante algoritmos genéticos híbridos?",
            },
        )
        assert step_resp.status_code == 200
        assert step_resp.json()["ai_analysis"]["is_valid"] is True

        list_resp = await client.get("/api/projects")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 1

        del_resp = await client.delete(f"/api/projects/{project_id}")
        assert del_resp.status_code == 204
