"""Integration tests for WebSocket security, handshake authentication, and frame limits (TF-WS-001, TF-WS-002, TF-WS-003, TF-TEST-003)."""

import pytest
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketDenialResponse
from starlette.websockets import WebSocketDisconnect

from thesisforge.api.app import app
from thesisforge.api.deps import get_db_manager, get_llm_router, get_settings
from thesisforge.config import AppSettings
from thesisforge.models import (
    AcademicLevel,
    ProjectPhase,
    ProjectStateDTO,
    SectionDraftDTO,
    SectionStatus,
)
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


@pytest.fixture
def override_db(in_memory_db: DatabaseManager):
    app.dependency_overrides[get_db_manager] = lambda: in_memory_db
    app.dependency_overrides[get_llm_router] = lambda: None
    yield in_memory_db
    app.dependency_overrides.clear()


@pytest.fixture
async def seeded_project(override_db: DatabaseManager) -> ProjectStateDTO:
    repo = ProjectRepository(override_db, "local")
    project = ProjectStateDTO(
        id="proj-ws-guard-01",
        title="Proyecto con Protección WebSocket",
        academic_level=AcademicLevel.MAESTRIA,
        phase=ProjectPhase.DRAFTING,
        sections=[
            SectionDraftDTO(
                section_id="sec_valid_01",
                chapter_number=1,
                order_index=1,
                title="Marco Teórico",
                status=SectionStatus.APPROVED,
                content="Contenido seguro validado.",
            )
        ],
    )
    await repo.create_project(project)
    return project


def test_websocket_draft_rejects_missing_token_in_production(
    override_db: DatabaseManager,
    seeded_project: ProjectStateDTO,
    monkeypatch: pytest.MonkeyPatch,
):
    """In production mode, WebSocket connection without token is rejected (TF-TEST-003)."""
    monkeypatch.setenv("THESISFORGE_INSTANCE_TOKEN", "super-secret-token-12345")
    prod_settings = AppSettings(
        environment="production",
        instance_token="super-secret-token-12345",
    )
    app.dependency_overrides[get_settings] = lambda: prod_settings

    client = TestClient(app)
    # Connecting without headers/subprotocols must fail with WebSocketDenialResponse
    with (
        pytest.raises(WebSocketDenialResponse),
        client.websocket_connect("/api/drafting/ws/proj-ws-guard-01/sec_valid_01"),
    ):
        pass


def test_websocket_draft_accepts_valid_subprotocol_token_in_production(
    override_db: DatabaseManager,
    seeded_project: ProjectStateDTO,
    monkeypatch: pytest.MonkeyPatch,
):
    """In production mode, WebSocket connection with valid Sec-WebSocket-Protocol token succeeds."""
    token = "super-secret-token-12345"
    monkeypatch.setenv("THESISFORGE_INSTANCE_TOKEN", token)
    prod_settings = AppSettings(
        environment="production",
        instance_token=token,
    )
    app.dependency_overrides[get_settings] = lambda: prod_settings

    client = TestClient(app)
    with client.websocket_connect(
        "/api/drafting/ws/proj-ws-guard-01/sec_valid_01",
        subprotocols=["bearer", token],
    ) as ws:
        assert ws is not None


def test_websocket_draft_rejects_nonexistent_section(
    override_db: DatabaseManager,
    seeded_project: ProjectStateDTO,
):
    """Connecting to a section_id that does not exist in the project is rejected (TF-WS-001)."""
    client = TestClient(app)
    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        client.websocket_connect("/api/drafting/ws/proj-ws-guard-01/sec_nonexistent"),
    ):
        pass
    assert exc_info.value.code == 1008


def test_websocket_draft_rejects_oversized_instructions(
    override_db: DatabaseManager,
    seeded_project: ProjectStateDTO,
):
    """Payload with instructions exceeding maximum length returns structured error (TF-WS-002)."""
    client = TestClient(app)
    with client.websocket_connect("/api/drafting/ws/proj-ws-guard-01/sec_valid_01") as ws:
        huge_instructions = "x" * 6000
        ws.send_json({"action": "generate", "user_instructions": huge_instructions})
        resp = ws.receive_json()
        assert resp["event"] == "error"
        assert resp.get("error_code") == "PAYLOAD_TOO_LARGE"


def test_websocket_defense_rejects_nonexistent_session(
    override_db: DatabaseManager,
):
    """Connecting to a defense session that does not exist is rejected pre-accept (TF-WS-001)."""
    client = TestClient(app)
    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        client.websocket_connect("/api/defense/ws/nonexistent-session-uuid"),
    ):
        pass
    assert exc_info.value.code == 1008
