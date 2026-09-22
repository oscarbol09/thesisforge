"""Transactional repository for jury evaluations and thesis defense sessions."""

import json

from thesisforge.core.logging import get_logger
from thesisforge.exceptions import DefenseSessionError, JuryEvaluationError
from thesisforge.models import DefenseSessionDTO, JuryEvaluationReportDTO
from thesisforge.repository.database import DatabaseManager

logger = get_logger(__name__)


class JuryRepository:
    """Async repository for persisting jury evaluation reports and oral defense sessions."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    # --- Jury Evaluations ---

    async def save_evaluation(self, evaluation: JuryEvaluationReportDTO) -> None:
        """Persist a newly generated jury evaluation report."""
        eval_json = evaluation.model_dump_json()
        async with self.db.get_connection() as db:
            await db.execute(
                """
                INSERT INTO jury_evaluations (id, project_id, verdict, score, evaluation_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    evaluation.id,
                    evaluation.project_id,
                    evaluation.verdict.value,
                    evaluation.overall_score,
                    eval_json,
                    evaluation.created_at.isoformat(),
                ),
            )
            await db.commit()
            logger.info(
                "Saved jury evaluation report.",
                extra={
                    "evaluation_id": evaluation.id,
                    "project_id": evaluation.project_id,
                    "verdict": evaluation.verdict.value,
                    "score": evaluation.overall_score,
                },
            )

    async def get_evaluation(self, evaluation_id: str) -> JuryEvaluationReportDTO:
        """Retrieve a specific evaluation report by ID."""
        async with (
            self.db.get_connection() as db,
            db.execute(
                "SELECT evaluation_json FROM jury_evaluations WHERE id = ?;",
                (evaluation_id,),
            ) as cursor,
        ):
            row = await cursor.fetchone()
            if not row:
                raise JuryEvaluationError(
                    f"No se encontró el dictamen de jurado con ID '{evaluation_id}'.",
                    details={"evaluation_id": evaluation_id},
                )
            data = json.loads(row["evaluation_json"])
            return JuryEvaluationReportDTO.model_validate(data)

    async def get_latest_evaluation_for_project(
        self, project_id: str
    ) -> JuryEvaluationReportDTO | None:
        """Retrieve the most recent jury evaluation report for a project."""
        async with (
            self.db.get_connection() as db,
            db.execute(
                """
                SELECT evaluation_json FROM jury_evaluations
                WHERE project_id = ?
                ORDER BY created_at DESC
                LIMIT 1;
                """,
                (project_id,),
            ) as cursor,
        ):
            row = await cursor.fetchone()
            if not row:
                return None
            data = json.loads(row["evaluation_json"])
            return JuryEvaluationReportDTO.model_validate(data)

    async def list_evaluations_for_project(self, project_id: str) -> list[JuryEvaluationReportDTO]:
        """List all historical jury evaluations for a project."""
        async with (
            self.db.get_connection() as db,
            db.execute(
                """
                SELECT evaluation_json FROM jury_evaluations
                WHERE project_id = ?
                ORDER BY created_at DESC;
                """,
                (project_id,),
            ) as cursor,
        ):
            rows = await cursor.fetchall()
            results: list[JuryEvaluationReportDTO] = []
            for r in rows:
                data = json.loads(r["evaluation_json"])
                results.append(JuryEvaluationReportDTO.model_validate(data))
            return results

    # --- Defense Sessions ---

    async def save_defense_session(self, session: DefenseSessionDTO) -> None:
        """Persist a newly started thesis defense session."""
        session_json = session.model_dump_json()
        async with self.db.get_connection() as db:
            await db.execute(
                """
                INSERT INTO defense_sessions (id, project_id, status, current_turn, session_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    session.id,
                    session.project_id,
                    session.status.value,
                    session.current_turn_index,
                    session_json,
                    session.created_at.isoformat(),
                    session.updated_at.isoformat(),
                ),
            )
            await db.commit()
            logger.info(
                "Saved new defense session.",
                extra={
                    "session_id": session.id,
                    "project_id": session.project_id,
                    "status": session.status.value,
                },
            )

    async def update_defense_session(self, session: DefenseSessionDTO) -> None:
        """Update an existing defense session state."""
        session_json = session.model_dump_json()
        async with self.db.get_connection() as db:
            cursor = await db.execute(
                """
                UPDATE defense_sessions
                SET status = ?, current_turn = ?, session_json = ?, updated_at = ?
                WHERE id = ?;
                """,
                (
                    session.status.value,
                    session.current_turn_index,
                    session_json,
                    session.updated_at.isoformat(),
                    session.id,
                ),
            )
            if cursor.rowcount == 0:
                raise DefenseSessionError(
                    f"No se encontró la sesión de sustentación con ID '{session.id}' para actualizar.",
                    details={"session_id": session.id},
                )
            await db.commit()
            logger.info(
                "Updated defense session.",
                extra={
                    "session_id": session.id,
                    "current_turn": session.current_turn_index,
                    "status": session.status.value,
                },
            )

    async def get_defense_session(self, session_id: str) -> DefenseSessionDTO:
        """Retrieve a defense session by its unique ID."""
        async with (
            self.db.get_connection() as db,
            db.execute(
                "SELECT session_json FROM defense_sessions WHERE id = ?;",
                (session_id,),
            ) as cursor,
        ):
            row = await cursor.fetchone()
            if not row:
                raise DefenseSessionError(
                    f"No se encontró la sesión de sustentación con ID '{session_id}'.",
                    details={"session_id": session_id},
                )
            data = json.loads(row["session_json"])
            return DefenseSessionDTO.model_validate(data)

    async def get_active_defense_session_for_project(
        self, project_id: str
    ) -> DefenseSessionDTO | None:
        """Retrieve the currently active (in_progress) defense session for a project if any."""
        async with (
            self.db.get_connection() as db,
            db.execute(
                """
                SELECT session_json FROM defense_sessions
                WHERE project_id = ? AND status = 'in_progress'
                ORDER BY updated_at DESC
                LIMIT 1;
                """,
                (project_id,),
            ) as cursor,
        ):
            row = await cursor.fetchone()
            if not row:
                return None
            data = json.loads(row["session_json"])
            return DefenseSessionDTO.model_validate(data)

    async def list_defense_sessions_for_project(self, project_id: str) -> list[DefenseSessionDTO]:
        """List all defense sessions for a given project."""
        async with (
            self.db.get_connection() as db,
            db.execute(
                """
                SELECT session_json FROM defense_sessions
                WHERE project_id = ?
                ORDER BY created_at DESC;
                """,
                (project_id,),
            ) as cursor,
        ):
            rows = await cursor.fetchall()
            results: list[DefenseSessionDTO] = []
            for r in rows:
                data = json.loads(r["session_json"])
                results.append(DefenseSessionDTO.model_validate(data))
            return results
