"""Unit tests for ThesisDefenseSimulator, oral defense progression, and scoring."""

import pytest

from thesisforge.exceptions import DefenseSessionError, DefenseTurnNotFoundError
from thesisforge.jury.defense import ThesisDefenseSimulator
from thesisforge.models import (
    AcademicLevel,
    DefenseStatus,
    JurorRole,
    MethodologyDTO,
    ProjectPhase,
    ProjectStateDTO,
    ResearchApproach,
)


@pytest.fixture
def sample_defense_project() -> ProjectStateDTO:
    """Fixture providing a project for oral defense simulation."""
    return ProjectStateDTO(
        id="proj-def-sim-01",
        title="Validación de Modelos RAG en Diagnóstico Clínico",
        academic_level=AcademicLevel.MAESTRIA,
        phase=ProjectPhase.REVIEW,
        research_question="¿Cómo influye la arquitectura RAG en la precisión diagnóstica?",
        general_objective="Evaluar la precisión diagnóstica de un sistema RAG.",
        hypothesis="El sistema RAG reduce en un 40% los falsos positivos.",
        methodology=MethodologyDTO(
            approach=ResearchApproach.CUANTITATIVO,
            design="Estudio transversal comparativo",
            population="500 casos clínicos anonimizados",
            sample="150 casos con diagnóstico validado",
            instruments=["Matriz de confusión y métricas F1/AUC"],
            analysis_technique="Curvas ROC y prueba de McNemar",
        ),
    )


@pytest.mark.asyncio
async def test_initialize_defense_session_structure(
    sample_defense_project: ProjectStateDTO,
) -> None:
    """Verify initialization of 4-turn defense session with calibrated questions."""
    simulator = ThesisDefenseSimulator(llm_router=None)
    session = await simulator.initialize_defense_session(sample_defense_project)

    assert session.project_id == "proj-def-sim-01"
    assert session.status == DefenseStatus.IN_PROGRESS
    assert session.total_turns == 4
    assert session.current_turn_index == 0
    assert len(session.turns) == 4

    # Check roles
    assert session.turns[0].juror_role == JurorRole.METODOLOGO
    assert session.turns[1].juror_role == JurorRole.ESPECIALISTA_TEMATICO
    assert session.turns[2].juror_role == JurorRole.AUDITOR_ESTADISTICO
    assert session.turns[3].juror_role == JurorRole.ABOGADO_DEL_DIABLO


@pytest.mark.asyncio
async def test_submit_defense_turn_progression(sample_defense_project: ProjectStateDTO) -> None:
    """Verify answering turns, heuristic scoring, and status advancement."""
    simulator = ThesisDefenseSimulator(llm_router=None)
    session = await simulator.initialize_defense_session(sample_defense_project)

    # Answer Turn 0 (Metodólogo)
    ans0 = (
        "Para controlar la validez interna ante la variabilidad del modelo, fijamos la temperatura en 0.0, "
        "establecimos semillas deterministas y realizamos 5 repeticiones independientes por caso clínico, "
        "verificando la confiabilidad inter-ensayos mediante el coeficiente kappa de Cohen."
    )
    session = await simulator.submit_defense_turn(
        session=session,
        turn_index=0,
        student_answer=ans0,
        project=sample_defense_project,
    )

    assert session.current_turn_index == 1
    assert session.turns[0].is_answered is True
    assert session.turns[0].turn_score is not None
    assert session.turns[0].turn_score >= 80.0
    assert session.status == DefenseStatus.IN_PROGRESS

    # Answer Turn 1 (Especialista Temático)
    ans1 = (
        "El aporte conceptual se diferencia del estado del arte al incorporar verificación de citas con DOI "
        "y árboles de decisión clínicos en la fase de re-ranking, reduciendo las alucinaciones factuales."
    )
    session = await simulator.submit_defense_turn(
        session=session,
        turn_index=1,
        student_answer=ans1,
        project=sample_defense_project,
    )
    assert session.current_turn_index == 2

    # Answer Turn 2 (Auditor Estadístico)
    ans2 = (
        "El tamaño muestral de N=150 se calculó para una potencia del 90% y alfa de 0.05 en la prueba de McNemar. "
        "Las variables se contrastaron respetando los supuestos de independencia entre pares discordantes."
    )
    session = await simulator.submit_defense_turn(
        session=session,
        turn_index=2,
        student_answer=ans2,
        project=sample_defense_project,
    )
    assert session.current_turn_index == 3

    # Answer Turn 3 (Abogado del Diablo)
    ans3 = (
        "Reconocemos como limitación que los casos clínicos provienen de un único centro hospitalario. "
        "Si otro centro con diferente terminología intenta replicar, requerirá un ajuste en el vocabulario del tokenizer."
    )
    session = await simulator.submit_defense_turn(
        session=session,
        turn_index=3,
        student_answer=ans3,
        project=sample_defense_project,
    )

    # All 4 turns completed -> Session finalized!
    assert session.current_turn_index == 4
    assert session.final_score is not None
    assert session.final_score >= 70.0
    assert session.status in (DefenseStatus.PASSED, DefenseStatus.PASSED_WITH_HONORS)
    assert session.final_remarks is not None


@pytest.mark.asyncio
async def test_defense_validation_errors(sample_defense_project: ProjectStateDTO) -> None:
    """Verify validation guards for turn order, empty answer, and out of bounds turns."""
    simulator = ThesisDefenseSimulator(llm_router=None)
    session = await simulator.initialize_defense_session(sample_defense_project)

    # Wrong turn index
    with pytest.raises(DefenseSessionError):
        await simulator.submit_defense_turn(
            session=session,
            turn_index=2,  # Expected 0
            student_answer="Respuesta válida.",
            project=sample_defense_project,
        )

    # Empty answer
    with pytest.raises(DefenseSessionError):
        await simulator.submit_defense_turn(
            session=session,
            turn_index=0,
            student_answer="   ",
            project=sample_defense_project,
        )

    # Out of bounds turn
    with pytest.raises(DefenseTurnNotFoundError):
        await simulator.submit_defense_turn(
            session=session,
            turn_index=99,
            student_answer="Respuesta.",
            project=sample_defense_project,
        )
