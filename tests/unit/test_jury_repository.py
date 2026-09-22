"""Unit tests for JuryRepository and transactional persistence of evaluations and defense sessions."""

import pytest

from thesisforge.exceptions import DefenseSessionError, JuryEvaluationError
from thesisforge.models import (
    AcademicLevel,
    AuditIssueDTO,
    AuditIssueType,
    AuditSeverity,
    DefenseSessionDTO,
    DefenseStatus,
    DefenseTurnDTO,
    JurorDimensionScoreDTO,
    JurorRole,
    JuryEvaluationReportDTO,
    JuryVerdict,
    ProjectPhase,
    ProjectStateDTO,
)
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.jury_repository import JuryRepository
from thesisforge.repository.project_repository import ProjectRepository


@pytest.mark.asyncio
async def test_jury_evaluation_crud(in_memory_db: DatabaseManager) -> None:
    """Test saving, retrieving, and listing jury evaluation reports."""
    proj_repo = ProjectRepository(in_memory_db)
    jury_repo = JuryRepository(in_memory_db)

    project = ProjectStateDTO(
        id="proj-eval-001",
        title="Estudio de Métodos Formales",
        academic_level=AcademicLevel.MAESTRIA,
        phase=ProjectPhase.REVIEW,
    )
    await proj_repo.create_project(project)

    eval_report = JuryEvaluationReportDTO(
        id="eval-001",
        project_id="proj-eval-001",
        overall_score=88.5,
        verdict=JuryVerdict.APROBADO,
        summary_dictamen="El proyecto presenta rigor metodológico adecuado con observaciones menores.",
        juror_evaluations=[
            JurorDimensionScoreDTO(
                juror_role=JurorRole.METODOLOGO,
                juror_name="Dr. Arístides Valenzuela",
                dimension_name="Consistencia Metodológica",
                score=90.0,
                criteria_evaluation="Coherencia estricta entre problema y objetivos.",
                feedback="Aclarar el criterio de exclusión muestral.",
                strengths=["Diseño experimental sólido"],
                flaws=["Falta justificar el tamaño del grupo de control"],
            )
        ],
        issues=[
            AuditIssueDTO(
                issue_type=AuditIssueType.METHODOLOGICAL_INCONSISTENCY,
                severity=AuditSeverity.MINOR,
                chapter_or_section="Capítulo 3",
                title="Criterio de exclusión ambiguo",
                description="No se especifica si los participantes con datos incompletos fueron imputados.",
                recommendation="Detallar el protocolo de tratamiento de valores perdidos.",
            )
        ],
        mandatory_fixes=["Añadir protocolo de valores perdidos"],
        recommended_improvements=["Expandir discusión de amenazas a la validez externa"],
    )

    await jury_repo.save_evaluation(eval_report)

    # Fetch by ID
    retrieved = await jury_repo.get_evaluation("eval-001")
    assert retrieved.id == "eval-001"
    assert retrieved.project_id == "proj-eval-001"
    assert retrieved.overall_score == 88.5
    assert retrieved.verdict == JuryVerdict.APROBADO
    assert len(retrieved.juror_evaluations) == 1
    assert retrieved.juror_evaluations[0].juror_role == JurorRole.METODOLOGO
    assert len(retrieved.issues) == 1

    # Latest evaluation
    latest = await jury_repo.get_latest_evaluation_for_project("proj-eval-001")
    assert latest is not None
    assert latest.id == "eval-001"

    # Listing
    all_evals = await jury_repo.list_evaluations_for_project("proj-eval-001")
    assert len(all_evals) == 1


@pytest.mark.asyncio
async def test_jury_evaluation_not_found(in_memory_db: DatabaseManager) -> None:
    """Verify JuryEvaluationError is raised when fetching a non-existent report."""
    jury_repo = JuryRepository(in_memory_db)
    with pytest.raises(JuryEvaluationError):
        await jury_repo.get_evaluation("non-existent-eval")


@pytest.mark.asyncio
async def test_defense_session_crud_and_turn_progression(in_memory_db: DatabaseManager) -> None:
    """Test saving, updating, and querying interactive defense sessions."""
    proj_repo = ProjectRepository(in_memory_db)
    jury_repo = JuryRepository(in_memory_db)

    project = ProjectStateDTO(
        id="proj-def-001",
        title="Evaluación de Algoritmos RAG",
        academic_level=AcademicLevel.DOCTORADO,
        phase=ProjectPhase.REVIEW,
    )
    await proj_repo.create_project(project)

    turns = [
        DefenseTurnDTO(
            turn_index=0,
            juror_role=JurorRole.METODOLOGO,
            juror_name="Dr. Arístides Valenzuela",
            question="¿Cómo garantiza la validez interna ante la variabilidad del LLM?",
            focus_area="Validez Interna",
        ),
        DefenseTurnDTO(
            turn_index=1,
            juror_role=JurorRole.AUDITOR_ESTADISTICO,
            juror_name="Dr. Camilo Restrepo",
            question="¿Qué prueba estadística utilizó para contrastar las tasas de alucinación?",
            focus_area="Análisis Estadístico",
        ),
    ]

    session = DefenseSessionDTO(
        id="def-session-001",
        project_id="proj-def-001",
        academic_level=AcademicLevel.DOCTORADO,
        status=DefenseStatus.IN_PROGRESS,
        current_turn_index=0,
        total_turns=2,
        turns=turns,
    )

    await jury_repo.save_defense_session(session)

    # Retrieve session
    retrieved = await jury_repo.get_defense_session("def-session-001")
    assert retrieved.id == "def-session-001"
    assert retrieved.status == DefenseStatus.IN_PROGRESS
    assert retrieved.current_turn_index == 0
    assert len(retrieved.turns) == 2

    # Active session check
    active = await jury_repo.get_active_defense_session_for_project("proj-def-001")
    assert active is not None
    assert active.id == "def-session-001"

    # Simulate answering turn 0 and updating session
    session.turns[0].student_answer = "Fijamos la temperatura en 0.0 y ejecutamos 5 repeticiones por consulta."
    session.turns[0].juror_feedback = "Respuesta fundamentada y metodológicamente acertada."
    session.turns[0].turn_score = 95.0
    session.turns[0].is_answered = True
    session.current_turn_index = 1

    await jury_repo.update_defense_session(session)

    updated = await jury_repo.get_defense_session("def-session-001")
    assert updated.current_turn_index == 1
    assert updated.turns[0].is_answered is True
    assert updated.turns[0].turn_score == 95.0


@pytest.mark.asyncio
async def test_defense_session_not_found(in_memory_db: DatabaseManager) -> None:
    """Verify DefenseSessionError is raised for non-existent session."""
    jury_repo = JuryRepository(in_memory_db)
    with pytest.raises(DefenseSessionError):
        await jury_repo.get_defense_session("non-existent-session")
