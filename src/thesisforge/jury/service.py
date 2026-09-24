"""High-level service facade for jury audit, evaluations, and interactive thesis defense."""

from thesisforge.core.logging import get_logger
from thesisforge.jury.ai_failure_gate import AIFailureGateAuditor, AIFailureGateReport
from thesisforge.jury.defense import ThesisDefenseSimulator
from thesisforge.jury.evaluator import MultiAgentJuryEngine
from thesisforge.llm.router import LLMRouter
from thesisforge.models import (
    DefenseSessionDTO,
    DefenseStatus,
    JuryEvaluationReportDTO,
    ProjectPhase,
)
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.jury_repository import JuryRepository
from thesisforge.repository.project_repository import ProjectRepository

logger = get_logger(__name__)


class JuryService:
    """Domain service orchestrating multi-agent jury evaluations and interactive oral defense simulations."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        project_repo: ProjectRepository,
        jury_repo: JuryRepository | None = None,
        llm_router: LLMRouter | None = None,
    ) -> None:
        self.db = db_manager
        self.project_repo = project_repo
        self.jury_repo = jury_repo or JuryRepository(db_manager)
        self.llm = llm_router
        self.evaluator = MultiAgentJuryEngine(llm_router=llm_router)
        self.defense_simulator = ThesisDefenseSimulator(llm_router=llm_router)

    async def audit_project(self, project_id: str) -> JuryEvaluationReportDTO:
        """Run a full multi-perspective jury evaluation and persist the resulting audit report."""
        project = await self.project_repo.get_project(project_id)

        # Run multi-agent jury evaluation
        report = await self.evaluator.evaluate_project(project)

        # Persist report
        await self.jury_repo.save_evaluation(report)

        # Update project phase if appropriate
        if project.phase in (
            ProjectPhase.SETUP,
            ProjectPhase.ORIENTATION,
            ProjectPhase.CONTEXT,
            ProjectPhase.DRAFTING,
        ):
            project.phase = ProjectPhase.REVIEW
            await self.project_repo.update_project(project)

        logger.info(
            "Completed multi-agent jury audit for project.",
            extra={
                "project_id": project_id,
                "score": report.overall_score,
                "verdict": report.verdict.value,
                "issues_count": len(report.issues),
            },
        )
        return report

    async def get_latest_evaluation(self, project_id: str) -> JuryEvaluationReportDTO | None:
        """Fetch the most recent jury audit report for a project."""
        return await self.jury_repo.get_latest_evaluation_for_project(project_id)

    async def get_evaluation(self, evaluation_id: str) -> JuryEvaluationReportDTO:
        """Fetch a specific evaluation report by its ID."""
        return await self.jury_repo.get_evaluation(evaluation_id)

    async def list_evaluations(self, project_id: str) -> list[JuryEvaluationReportDTO]:
        """List all historical evaluation reports for a project."""
        return await self.jury_repo.list_evaluations_for_project(project_id)

    async def start_defense_session(
        self,
        project_id: str,
        force_new: bool = False,
    ) -> DefenseSessionDTO:
        """Start or resume an interactive oral defense session."""
        if not force_new:
            active_session = await self.jury_repo.get_active_defense_session_for_project(project_id)
            if active_session:
                return active_session

        project = await self.project_repo.get_project(project_id)
        latest_eval = await self.jury_repo.get_latest_evaluation_for_project(project_id)

        session = await self.defense_simulator.initialize_defense_session(
            project=project,
            evaluation=latest_eval,
        )

        await self.jury_repo.save_defense_session(session)
        logger.info(
            "Initialized new oral defense session.",
            extra={
                "session_id": session.id,
                "project_id": project_id,
                "turns": session.total_turns,
            },
        )
        return session

    async def submit_defense_answer(
        self,
        session_id: str,
        turn_index: int,
        student_answer: str,
    ) -> DefenseSessionDTO:
        """Submit student answer to the current defense turn, evaluate it, and update session."""
        session = await self.jury_repo.get_defense_session(session_id)
        project = await self.project_repo.get_project(session.project_id)

        updated_session = await self.defense_simulator.submit_defense_turn(
            session=session,
            turn_index=turn_index,
            student_answer=student_answer,
            project=project,
        )

        await self.jury_repo.update_defense_session(updated_session)

        # If defense is completed with success, mark project as completed
        if (
            updated_session.status in (DefenseStatus.PASSED, DefenseStatus.PASSED_WITH_HONORS)
            and project.phase != ProjectPhase.COMPLETED
        ):
            project.phase = ProjectPhase.COMPLETED
            await self.project_repo.update_project(project)

        return updated_session

    async def get_defense_session(self, session_id: str) -> DefenseSessionDTO:
        """Retrieve defense session state and transcription."""
        return await self.jury_repo.get_defense_session(session_id)

    async def list_defense_sessions(self, project_id: str) -> list[DefenseSessionDTO]:
        """List all defense sessions for a project."""
        return await self.jury_repo.list_defense_sessions_for_project(project_id)

    async def audit_ai_failure_modes(self, project_id: str) -> AIFailureGateReport:
        """Run dedicated audit of the 7 AI Failure Modes on a project and persist findings."""
        project = await self.project_repo.get_project(project_id)
        report = AIFailureGateAuditor.audit_project(project)

        project.ai_failure_audit = report.model_dump()
        await self.project_repo.update_project(project)

        logger.info(
            "Executed 7 AI Failure Modes audit on project.",
            extra={
                "project_id": project_id,
                "passed": report.passed,
                "risk_score": report.risk_score,
                "findings_count": len(report.findings),
            },
        )
        return report

