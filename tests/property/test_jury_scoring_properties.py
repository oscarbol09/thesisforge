"""Property-based tests for jury scoring, verdict determination, and defense invariants using Hypothesis."""

from hypothesis import given, settings
from hypothesis import strategies as st

from thesisforge.jury.evaluator import MultiAgentJuryEngine
from thesisforge.models import (
    AuditIssueDTO,
    AuditIssueType,
    AuditSeverity,
    JuryVerdict,
)


@given(
    score=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=100)
def test_property_verdict_monotonicity_without_issues(score: float) -> None:
    """Property: In the absence of issues, verdict mapping is strictly monotonic and exhaustive."""
    engine = MultiAgentJuryEngine(llm_router=None)
    verdict = engine._determine_verdict(score, issues=[])

    if score >= 95.0:
        assert verdict == JuryVerdict.APROBADO_CON_DISTINCION
    elif score >= 80.0:
        assert verdict == JuryVerdict.APROBADO
    elif score >= 70.0:
        assert verdict == JuryVerdict.MODIFICACIONES_MENORES
    elif score >= 50.0:
        assert verdict == JuryVerdict.MODIFICACIONES_MAYORES
    else:
        assert verdict == JuryVerdict.NO_APROBADO


@given(
    score=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    issue_type=st.sampled_from(list(AuditIssueType)),
)
@settings(max_examples=50)
def test_property_critical_issue_vetoes_approval(score: float, issue_type: AuditIssueType) -> None:
    """Property: If a critical issue exists, the verdict can never be approved regardless of score."""
    engine = MultiAgentJuryEngine(llm_router=None)
    critical_issue = AuditIssueDTO(
        issue_type=issue_type,
        severity=AuditSeverity.CRITICAL,
        chapter_or_section="Capítulo 1",
        title="Defecto crítico metodológico",
        description="Inconsistencia fatal en la formulación.",
        recommendation="Reformular completamente.",
    )
    verdict = engine._determine_verdict(score, issues=[critical_issue])
    assert verdict == JuryVerdict.NO_APROBADO
    assert verdict not in (
        JuryVerdict.APROBADO,
        JuryVerdict.APROBADO_CON_DISTINCION,
        JuryVerdict.MODIFICACIONES_MENORES,
    )


@given(
    score=st.floats(min_value=80.0, max_value=100.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50)
def test_property_multiple_major_issues_forces_major_modifications(score: float) -> None:
    """Property: 3 or more major issues downgrade approval to MODIFICACIONES_MAYORES."""
    engine = MultiAgentJuryEngine(llm_router=None)
    major_issues = [
        AuditIssueDTO(
            issue_type=AuditIssueType.METHODOLOGICAL_INCONSISTENCY,
            severity=AuditSeverity.MAJOR,
            chapter_or_section=f"Sección {idx}",
            title=f"Defecto mayor {idx}",
            description="Observación de peso.",
            recommendation="Corregir.",
        )
        for idx in range(3)
    ]
    verdict = engine._determine_verdict(score, issues=major_issues)
    assert verdict == JuryVerdict.MODIFICACIONES_MAYORES
