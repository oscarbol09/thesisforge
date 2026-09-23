"""REST API endpoints and WebSocket handlers for interactive oral thesis defense simulation."""

from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, ConfigDict, Field

from thesisforge.api.deps import get_jury_service
from thesisforge.core.logging import get_logger
from thesisforge.jury.service import JuryService
from thesisforge.models import DefenseSessionDTO

logger = get_logger(__name__)

router = APIRouter(prefix="/api/defense", tags=["Thesis Defense Simulation"])


class StartDefenseRequest(BaseModel):
    """Payload to initialize or resume an oral defense session."""

    model_config = ConfigDict(extra="forbid")

    force_new: bool = Field(default=False, description="Forzar creación de nueva sesión de defensa")


class SubmitReplyRequest(BaseModel):
    """Payload with student's answer to a specific defense turn."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    turn_index: int = Field(ge=0, description="Índice del turno de defensa a responder")
    student_answer: str = Field(
        min_length=1, max_length=5000, description="Respuesta y argumentación del estudiante"
    )


@router.post(
    "/projects/{project_id}/start",
    response_model=DefenseSessionDTO,
    status_code=status.HTTP_200_OK,
    summary="Iniciar o reanudar sesión de sustentación oral",
)
async def start_defense_session_endpoint(
    project_id: str,
    payload: StartDefenseRequest = StartDefenseRequest(),
    jury_service: JuryService = Depends(get_jury_service),
) -> DefenseSessionDTO:
    """Initialize a multi-turn oral thesis defense session with the 4 juror members."""
    return await jury_service.start_defense_session(
        project_id=project_id,
        force_new=payload.force_new,
    )


@router.post(
    "/sessions/{session_id}/reply",
    response_model=DefenseSessionDTO,
    status_code=status.HTTP_200_OK,
    summary="Enviar réplica del estudiante al turno actual de sustentación",
)
async def submit_defense_reply_endpoint(
    session_id: str,
    payload: SubmitReplyRequest,
    jury_service: JuryService = Depends(get_jury_service),
) -> DefenseSessionDTO:
    """Submit oral defense argument for evaluation by the corresponding juror."""
    return await jury_service.submit_defense_answer(
        session_id=session_id,
        turn_index=payload.turn_index,
        student_answer=payload.student_answer,
    )


@router.get(
    "/sessions/{session_id}",
    response_model=DefenseSessionDTO,
    status_code=status.HTTP_200_OK,
    summary="Consultar estado y transcripción de una sesión de sustentación",
)
async def get_defense_session_endpoint(
    session_id: str,
    jury_service: JuryService = Depends(get_jury_service),
) -> DefenseSessionDTO:
    """Retrieve full transcript, scores, and status of a thesis defense session."""
    return await jury_service.get_defense_session(session_id)


@router.get(
    "/projects/{project_id}/sessions",
    response_model=list[DefenseSessionDTO],
    status_code=status.HTTP_200_OK,
    summary="Listar historial de sesiones de sustentación de un proyecto",
)
async def list_project_defense_sessions_endpoint(
    project_id: str,
    jury_service: JuryService = Depends(get_jury_service),
) -> list[DefenseSessionDTO]:
    """Retrieve all defense sessions initiated for a project."""
    return await jury_service.list_defense_sessions(project_id)


@router.websocket("/ws/{session_id}")
async def defense_websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    jury_service: JuryService = Depends(get_jury_service),
) -> None:
    """Interactive bidirectional WebSocket for live oral defense simulation."""
    await websocket.accept()
    logger.info("Defense WebSocket connection established.", extra={"session_id": session_id})

    try:
        session = await jury_service.get_defense_session(session_id)
        await websocket.send_json(
            {
                "event": "session_state",
                "session": session.model_dump(mode="json"),
            }
        )

        while True:
            data: dict[str, Any] = await websocket.receive_json()
            event_type = data.get("event")

            if event_type == "reply":
                turn_index = int(data.get("turn_index", -1))
                student_answer = str(data.get("student_answer", "")).strip()

                if not student_answer:
                    await websocket.send_json(
                        {
                            "event": "error",
                            "message": "La respuesta del estudiante no puede estar vacía.",
                        }
                    )
                    continue

                updated_session = await jury_service.submit_defense_answer(
                    session_id=session_id,
                    turn_index=turn_index,
                    student_answer=student_answer,
                )

                # Send feedback on evaluated turn
                answered_turn = updated_session.turns[turn_index]
                await websocket.send_json(
                    {
                        "event": "turn_evaluated",
                        "turn": answered_turn.model_dump(mode="json"),
                        "session": updated_session.model_dump(mode="json"),
                    }
                )

                if updated_session.current_turn_index >= updated_session.total_turns:
                    await websocket.send_json(
                        {
                            "event": "defense_completed",
                            "final_verdict": updated_session.final_verdict.value
                            if updated_session.final_verdict
                            else None,
                            "final_score": updated_session.final_score,
                            "final_remarks": updated_session.final_remarks,
                            "session": updated_session.model_dump(mode="json"),
                        }
                    )

            elif event_type == "ping":
                await websocket.send_json({"event": "pong"})

            else:
                await websocket.send_json(
                    {
                        "event": "error",
                        "message": f"Evento desconocido '{event_type}'.",
                    }
                )

    except WebSocketDisconnect:
        logger.info("Defense WebSocket disconnected by client.", extra={"session_id": session_id})
    except Exception as exc:
        logger.exception(
            "Error in defense WebSocket handler.",
            extra={"session_id": session_id, "error": str(exc)},
        )
        try:
            await websocket.send_json({"event": "error", "message": str(exc)})
            await websocket.close()
        except Exception as close_exc:
            logger.debug(
                "Could not send error frame to WebSocket.", extra={"error": str(close_exc)}
            )
