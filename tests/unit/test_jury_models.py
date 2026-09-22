"""Unit tests for jury evaluation and oral defense domain models."""

import pytest
from pydantic import ValidationError

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
)


def test_audit_issue_dto_validation() -> None:
    """Test creation and serialization of AuditIssueDTO."""
    issue = AuditIssueDTO(
        issue_type=AuditIssueType.METHODOLOGICAL_INCONSISTENCY,
        severity=AuditSeverity.CRITICAL,
        chapter_or_section="Capítulo 3",
        title="Falta de contrastación de hipótesis",
        description="Se declaró un estudio experimental pero no se especificó la prueba de hipótesis.",
        quote_or_passage="El estudio analizará los datos de forma cualitativa.",
        recommendation="Incorporar prueba t de Student o ANOVA según normalidad.",
    )
    assert issue.severity == AuditSeverity.CRITICAL
    assert issue.issue_type == AuditIssueType.METHODOLOGICAL_INCONSISTENCY
    assert "ANOVA" in issue.recommendation

    data = issue.model_dump()
    assert data["severity"] == "critical"
    restored = AuditIssueDTO.model_validate(data)
    assert restored.id == issue.id


def test_juror_dimension_score_dto_bounds() -> None:
    """Test JurorDimensionScoreDTO score boundaries (0-100)."""
    valid = JurorDimensionScoreDTO(
        juror_role=JurorRole.METODOLOGO,
        juror_name="Dr. Arístides Valenzuela",
        dimension_name="Consistencia Metodológica",
        score=92.5,
        criteria_evaluation="Excelente delimitación de variables.",
        feedback="Diseño apropiado.",
        strengths=["Variables operacionales claras"],
        flaws=[],
    )
    assert valid.score == 92.5

    with pytest.raises(ValidationError):
        JurorDimensionScoreDTO(
            juror_role=JurorRole.METODOLOGO,
            juror_name="Dr. Valenzuela",
            dimension_name="Consistencia",
            score=105.0,  # Out of bounds (>100)
        )

    with pytest.raises(ValidationError):
        JurorDimensionScoreDTO(
            juror_role=JurorRole.METODOLOGO,
            juror_name="Dr. Valenzuela",
            dimension_name="Consistencia",
            score=-5.0,  # Out of bounds (<0)
        )


def test_jury_evaluation_report_dto() -> None:
    """Test JuryEvaluationReportDTO integrity and serialization."""
    report = JuryEvaluationReportDTO(
        project_id="proj-123",
        overall_score=96.0,
        verdict=JuryVerdict.APROBADO_CON_DISTINCION,
        summary_dictamen="Trabajo de investigación de calidad sobresaliente.",
        juror_evaluations=[
            JurorDimensionScoreDTO(
                juror_role=JurorRole.METODOLOGO,
                juror_name="Dr. Arístides Valenzuela",
                dimension_name="Metodología",
                score=96.0,
            )
        ],
        issues=[],
        mandatory_fixes=[],
        recommended_improvements=["Publicar en revista indexada Q1"],
    )
    assert report.verdict == JuryVerdict.APROBADO_CON_DISTINCION
    assert report.overall_score == 96.0

    json_str = report.model_dump_json()
    assert "aprobado_con_distincion" in json_str


def test_defense_session_dto_lifecycle() -> None:
    """Test DefenseSessionDTO turn structure and state changes."""
    turns = [
        DefenseTurnDTO(
            turn_index=0,
            juror_role=JurorRole.METODOLOGO,
            juror_name="Dr. Arístides Valenzuela",
            question="¿Cuál es la amenaza a la validez interna más crítica en su diseño?",
            focus_area="Validez",
        ),
        DefenseTurnDTO(
            turn_index=1,
            juror_role=JurorRole.ESPECIALISTA_TEMATICO,
            juror_name="Dra. Beatriz Salamanca",
            question="¿Cómo fundamenta la elección del marco conceptual?",
            focus_area="Teoría",
        ),
    ]

    session = DefenseSessionDTO(
        project_id="proj-def-01",
        academic_level=AcademicLevel.DOCTORADO,
        status=DefenseStatus.IN_PROGRESS,
        current_turn_index=0,
        total_turns=2,
        turns=turns,
    )
    assert session.status == DefenseStatus.IN_PROGRESS
    assert session.current_turn_index == 0
    assert len(session.turns) == 2
    assert session.turns[0].is_answered is False

    # Simulate answering turn
    session.turns[0].student_answer = "La historia y la maduración de los sujetos fueron controladas mediante grupo de control."
    session.turns[0].juror_feedback = "Respuesta rigurosa."
    session.turns[0].turn_score = 90.0
    session.turns[0].is_answered = True
    session.current_turn_index = 1

    assert session.turns[0].is_answered is True
    assert session.current_turn_index == 1
