"""Integration tests for thesis drafting REST and WebSocket API endpoints."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from thesisforge.api.app import app
from thesisforge.api.deps import get_db_manager, get_llm_router
from thesisforge.llm.router import LLMRouter
from thesisforge.models import (
    AcademicLevel,
    MethodologyDTO,
    ProjectPhase,
    ProjectStateDTO,
    ResearchApproach,
    SectionStatus,
)
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


@pytest.fixture
def mock_llm_router():
    router = AsyncMock(spec=LLMRouter)
    router.complete.return_value = "Contenido de redacción académica rigurosa."

    async def mock_stream(*args, **kwargs):
        for token in ["El ", "presente ", "estudio ", "analiza..."]:
            yield token

    router.stream_completion.side_effect = mock_stream
    return router


@pytest.fixture
def override_deps(in_memory_db: DatabaseManager, mock_llm_router: LLMRouter):
    app.dependency_overrides[get_db_manager] = lambda: in_memory_db
    app.dependency_overrides[get_llm_router] = lambda: mock_llm_router
    yield in_memory_db
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_initialize_and_list_sections(override_deps: DatabaseManager):
    """Verify section initialization and listing via REST API."""
    repo = ProjectRepository(override_deps)
    project = ProjectStateDTO(
        id="proj-api-draft-01",
        title="Tesis de Redacción Modular",
        academic_level=AcademicLevel.PREGRADO,
        phase=ProjectPhase.ORIENTATION,
        methodology=MethodologyDTO(approach=ResearchApproach.CUANTITATIVO),
    )
    await repo.create_project(project)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Initialize sections
        init_resp = await client.post("/api/drafting/projects/proj-api-draft-01/initialize")
        assert init_resp.status_code == 200
        sections = init_resp.json()
        assert len(sections) >= 15
        assert sections[0]["section_id"] == "sec_1_1"

        # List sections
        list_resp = await client.get("/api/drafting/projects/proj-api-draft-01/sections")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == len(sections)

        # Get single section
        sec_resp = await client.get("/api/drafting/projects/proj-api-draft-01/sections/sec_1_1")
        assert sec_resp.status_code == 200
        assert sec_resp.json()["section_id"] == "sec_1_1"


@pytest.mark.asyncio
async def test_api_generate_and_refine_and_approve_section(override_deps: DatabaseManager):
    """Verify generating, manual editing, refining, and approving sections via REST API."""
    repo = ProjectRepository(override_deps)
    project = ProjectStateDTO(
        id="proj-api-draft-02",
        title="Tesis de Validación",
        academic_level=AcademicLevel.PREGRADO,
        phase=ProjectPhase.ORIENTATION,
        methodology=MethodologyDTO(approach=ResearchApproach.CUANTITATIVO),
    )
    await repo.create_project(project)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/drafting/projects/proj-api-draft-02/initialize")

        # Generate draft
        gen_resp = await client.post(
            "/api/drafting/projects/proj-api-draft-02/sections/sec_1_1/generate",
            json={"user_instructions": "Enfoque en variables operacionales."},
        )
        assert gen_resp.status_code == 200
        assert gen_resp.json()["content"] != ""
        assert gen_resp.json()["status"] == SectionStatus.READY_FOR_REVIEW.value

        # Update manually
        put_resp = await client.put(
            "/api/drafting/projects/proj-api-draft-02/sections/sec_1_1",
            json={"content": "Texto editado manualmente por el tesista."},
        )
        assert put_resp.status_code == 200
        assert put_resp.json()["content"] == "Texto editado manualmente por el tesista."

        # Refine draft
        ref_resp = await client.post(
            "/api/drafting/projects/proj-api-draft-02/sections/sec_1_1/refine",
            json={"user_instructions": "Mejorar la sintaxis y profundidad."},
        )
        assert ref_resp.status_code == 200
        assert ref_resp.json()["version"] >= 2

        # Approve section
        appr_resp = await client.post(
            "/api/drafting/projects/proj-api-draft-02/sections/sec_1_1/approve"
        )
        assert appr_resp.status_code == 200
        assert appr_resp.json()["status"] == SectionStatus.APPROVED.value
        assert appr_resp.json()["summary"] != ""


def test_api_websocket_draft_stream(override_deps: DatabaseManager, mock_llm_router: LLMRouter):
    """Verify real-time WebSocket token streaming for draft generation."""
    client = TestClient(app)

    repo = ProjectRepository(override_deps)
    import asyncio

    project = ProjectStateDTO(
        id="proj-api-ws-01",
        title="Tesis Streaming",
        academic_level=AcademicLevel.PREGRADO,
        phase=ProjectPhase.ORIENTATION,
        methodology=MethodologyDTO(approach=ResearchApproach.CUANTITATIVO),
    )
    asyncio.run(repo.create_project(project))

    init_resp = client.post("/api/drafting/projects/proj-api-ws-01/initialize")
    assert init_resp.status_code == 200

    with client.websocket_connect("/api/drafting/ws/proj-api-ws-01/sec_1_1") as websocket:
        websocket.send_json({"action": "generate", "user_instructions": "Generar borrador"})

        tokens = []
        completed = False
        while not completed:
            msg = websocket.receive_json()
            if msg.get("event") == "token":
                tokens.append(msg["data"])
            elif msg.get("event") == "complete":
                completed = True
                assert msg["section"]["section_id"] == "sec_1_1"

        assert len(tokens) > 0
