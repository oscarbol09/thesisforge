"""Unit tests for MultiAgentJuryEngine, bias detection, and score weighting."""

from unittest.mock import AsyncMock

import pytest

from thesisforge.jury.evaluator import MultiAgentJuryEngine
from thesisforge.llm.router import LLMRouter
from thesisforge.models import (
    AcademicLevel,
    CitationDTO,
    JurorRole,
    JuryVerdict,
    MethodologyDTO,
    ProjectPhase,
    ProjectStateDTO,
    ResearchApproach,
    SectionDraftDTO,
    SectionStatus,
)


@pytest.fixture
def sample_complete_project() -> ProjectStateDTO:
    """Fixture providing a complete, well-formed thesis project."""
    return ProjectStateDTO(
        id="proj-comp-01",
        title="Impacto de la Realidad Aumentada en el Aprendizaje de Geometría",
        academic_level=AcademicLevel.PREGRADO,
        phase=ProjectPhase.DRAFTING,
        area_of_study="Ciencias de la Educación",
        topic="Tecnología Educativa",
        research_problem=(
            "Los estudiantes de educación secundaria presentan dificultades en la visualización espacial de figuras 3D, "
            "lo que incide negativamente en el rendimiento académico en matemáticas según pruebas estandarizadas 2024."
        ),
        research_question="¿Cómo incide el uso de una herramienta de Realidad Aumentada en el rendimiento académico de geometría?",
        hypothesis="El uso de la herramienta de Realidad Aumentada incrementa significativamente el rendimiento en geometría.",
        general_objective="Determinar la incidencia del uso de Realidad Aumentada en el rendimiento de geometría.",
        specific_objectives=[
            "Diagnosticar el nivel inicial de competencia espacial de los estudiantes.",
            "Diseñar una secuencia didáctica mediada por Realidad Aumentada.",
            "Evaluar la ganancia de aprendizaje tras la intervención experimental.",
        ],
        methodology=MethodologyDTO(
            approach=ResearchApproach.CUANTITATIVO,
            design="Cuasiexperimental con grupo control y experimental",
            population="240 estudiantes de grado noveno",
            sample="60 estudiantes divididos en 2 grupos de 30",
            instruments=["Prueba estandarizada de geometría", "Cuestionario de usabilidad"],
            analysis_technique="Prueba t de Student para muestras independientes",
        ),
        validated_citations=[
            CitationDTO(
                title="Augmented Reality in Education",
                authors=["Johnson, M.", "Smith, P."],
                year=2023,
                doi="10.1016/j.compedu.2023.104000",
            ),
            CitationDTO(
                title="Spatial Ability and Geometry Performance",
                authors=["García, L."],
                year=2022,
                doi="10.1080/0020739X.2022.204000",
            ),
            CitationDTO(
                title="Interactive 3D Environments for STEM",
                authors=["Chen, H."],
                year=2024,
                doi="10.1109/TLT.2024.330000",
            ),
        ],
        sections=[
            SectionDraftDTO(
                section_id="intro",
                title="Introducción",
                content="Texto redactado con rigor sobre realidad aumentada...",
                status=SectionStatus.APPROVED,
                word_count=500,
            ),
            SectionDraftDTO(
                section_id="method",
                title="Metodología",
                content="Diseño cuasiexperimental con dos grupos de 30 estudiantes...",
                status=SectionStatus.APPROVED,
                word_count=600,
            ),
        ],
    )


@pytest.mark.asyncio
async def test_rule_based_audit_complete_project(sample_complete_project: ProjectStateDTO) -> None:
    """Verify evaluation of a complete project using the deterministic rule engine."""
    engine = MultiAgentJuryEngine(llm_router=None)
    report = await engine.evaluate_project(sample_complete_project)

    assert report.project_id == "proj-comp-01"
    assert report.overall_score >= 80.0
    assert report.verdict in (JuryVerdict.APROBADO, JuryVerdict.APROBADO_CON_DISTINCION)
    assert len(report.juror_evaluations) == 4
    # All 4 roles present
    roles = {je.juror_role for je in report.juror_evaluations}
    assert roles == {
        JurorRole.METODOLOGO,
        JurorRole.ESPECIALISTA_TEMATICO,
        JurorRole.AUDITOR_ESTADISTICO,
        JurorRole.ABOGADO_DEL_DIABLO,
    }


@pytest.mark.asyncio
async def test_rule_based_audit_incomplete_project() -> None:
    """Verify that an incomplete project generates critical issues and is not approved."""
    incomplete = ProjectStateDTO(
        id="proj-inc-01",
        title="",
        research_problem="",
        research_question="",
        general_objective="",
        validated_citations=[],
        sections=[],
    )
    engine = MultiAgentJuryEngine(llm_router=None)
    report = await engine.evaluate_project(incomplete)

    assert report.verdict == JuryVerdict.NO_APROBADO
    assert len(report.issues) >= 3
    # Check that critical issues are captured
    severities = [i.severity.value for i in report.issues]
    assert "critical" in severities


@pytest.mark.asyncio
async def test_quantitative_without_hypothesis_generates_issue(
    sample_complete_project: ProjectStateDTO,
) -> None:
    """Verify that a correlational/experimental quantitative project without hypothesis is flagged."""
    sample_complete_project.hypothesis = None
    engine = MultiAgentJuryEngine(llm_router=None)
    report = await engine.evaluate_project(sample_complete_project)

    hyp_issues = [
        i
        for i in report.issues
        if "hipótesis" in i.title.lower() or "hipótesis" in i.description.lower()
    ]
    assert len(hyp_issues) >= 1
    assert hyp_issues[0].severity.value in ("major", "critical")


@pytest.mark.asyncio
async def test_llm_panel_audit_with_mock(sample_complete_project: ProjectStateDTO) -> None:
    """Verify parsing and report generation when LLM returns structured JSON."""
    mock_router = AsyncMock(spec=LLMRouter)
    mock_router.complete_json.return_value = {
        "overall_score": 92.0,
        "verdict": "aprobado",
        "summary_dictamen": "El tribunal aprueba la propuesta destacando su diseño experimental.",
        "juror_evaluations": [
            {
                "juror_role": "metodologo",
                "juror_name": "Dr. Arístides Valenzuela",
                "dimension_name": "Consistencia Metodológica",
                "score": 95.0,
                "criteria_evaluation": "Diseño cuasiexperimental coherente.",
                "feedback": "Excelente alineación de objetivos.",
                "strengths": ["Grupos de control balanceados"],
                "flaws": [],
            },
            {
                "juror_role": "especialista_tematico",
                "juror_name": "Dra. Beatriz Salamanca",
                "dimension_name": "Marco Teórico",
                "score": 90.0,
                "criteria_evaluation": "Literatura relevante y actualizada.",
                "feedback": "Citas indexadas pertinentes.",
                "strengths": ["Artículos IEEE y Elsevier"],
                "flaws": [],
            },
            {
                "juror_role": "auditor_estadistico",
                "juror_name": "Dr. Camilo Restrepo",
                "dimension_name": "Rigor Empírico",
                "score": 91.0,
                "criteria_evaluation": "Pruebas paramétricas adecuadas.",
                "feedback": "Verificar supuesto de normalidad con Shapiro-Wilk.",
                "strengths": ["Tamaño muestral N=60 justificado"],
                "flaws": [],
            },
            {
                "juror_role": "abogado_del_diablo",
                "juror_name": "Dr. Demetrio Sotomayor",
                "dimension_name": "Límites Epistemológicos",
                "score": 92.0,
                "criteria_evaluation": "Amenazas a la validez externa identificadas.",
                "feedback": "Buen reconocimiento de limitaciones.",
                "strengths": ["Efecto novedad controlado"],
                "flaws": [],
            },
        ],
        "issues": [],
        "mandatory_fixes": [],
        "recommended_improvements": ["Añadir prueba de Shapiro-Wilk previa a t de Student"],
    }

    engine = MultiAgentJuryEngine(llm_router=mock_router)
    report = await engine.evaluate_project(sample_complete_project)

    assert report.overall_score == 92.0
    assert report.verdict == JuryVerdict.APROBADO
    assert len(report.juror_evaluations) == 4
    assert mock_router.complete_json.await_count == 1
