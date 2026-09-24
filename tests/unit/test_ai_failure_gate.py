"""Unit tests for the 7 AI Failure Modes Academic Audit Gate."""


from thesisforge.jury.ai_failure_gate import AIFailureGateAuditor, AIFailureMode
from thesisforge.models import (
    AcademicLevel,
    CitationDTO,
    MethodologyDTO,
    ProjectStateDTO,
    ResearchApproach,
    SamplingTechnique,
    SectionDraftDTO,
    VariableOperationalizationDTO,
    VariableType,
)


def test_ai_failure_gate_passes_on_sound_thesis() -> None:
    project = ProjectStateDTO(
        id="sound_proj",
        title="Impacto del Clima Organizacional en el Desempeño Laboral",
        academic_level=AcademicLevel.MAESTRIA,
        research_problem="El clima organizacional deficiente genera alta rotación en el sector salud público.",
        research_question="¿Cómo influye el clima organizacional en el desempeño de los médicos?",
        general_objective="Determinar la influencia del clima organizacional en el desempeño laboral.",
        hypothesis="Existe una correlación directa entre clima organizacional y desempeño laboral.",
        justification="Relevancia social y teórica para la optimización de recursos humanos.",
        scope_limitations="El estudio se limita a hospitales públicos de tercer nivel durante el periodo 2024.",
        variables=["Clima Organizacional", "Desempeño Laboral"],
        operationalized_variables=[
            VariableOperationalizationDTO(
                name="Clima Organizacional",
                variable_type=VariableType.INDEPENDIENTE,
                indicators=["Liderazgo", "Comunicación"],
            ),
            VariableOperationalizationDTO(
                name="Desempeño Laboral",
                variable_type=VariableType.DEPENDIENTE,
                indicators=["Eficacia", "Puntualidad"],
            ),
        ],
        methodology=MethodologyDTO(
            approach=ResearchApproach.CUANTITATIVO,
            design="No experimental transversal correlacional",
            population="200 médicos especialistas",
            sample="120 médicos seleccionados aleatoriamente",
            sampling_technique=SamplingTechnique.PROBABILISTICO_ALEATORIO,
            inclusion_criteria=["Médicos con más de 1 año de antigüedad"],
            exclusion_criteria=["Personal en periodo de prueba"],
            instruments=["Escala de Clima Laboral de Likert"],
            analysis_technique="Coeficiente de correlación de Pearson",
        ),
        validated_citations=[
            CitationDTO(title="Clima y Rendimiento", authors=["Gómez", "Pérez"], year=2022)
        ],
        sections=[
            SectionDraftDTO(
                section_id="intro",
                title="Introducción",
                content="Según Gómez y Pérez (2022), el ambiente incide en la productividad.",
            )
        ],
    )

    report = AIFailureGateAuditor.audit_project(project)
    assert report.passed is True
    assert report.risk_score < 40.0
    assert len(report.passed_modes) >= 5


def test_ai_failure_gate_detects_bug_as_insight_and_hedging() -> None:
    project = ProjectStateDTO(
        id="risky_proj",
        title="Investigación con fallos",
        research_problem="Quizás el fenómeno tal vez ocurra, posiblemente influenciado por factores que se podría suponer relevantes.",
        justification="Detectamos una anomalía reveladora en el pipeline que demuestra una nueva ley universal.",
        scope_limitations="",  # Missing limitations -> Epistemic Frame Lock
        methodology=MethodologyDTO(
            approach=ResearchApproach.CUANTITATIVO,
            design="Explicativo causal",
            sample="12 participantes",  # Small sample -> Overgeneralization
            sampling_technique=SamplingTechnique.NO_PROBABILISTICO_INTENCIONAL,
        ),
        sections=[
            SectionDraftDTO(
                section_id="sec1",
                title="Resultados",
                content="Como demostró (Mendoza, 2021), el efecto es absoluto.",  # In-text citation without validated citations
            )
        ],
        validated_citations=[],  # Empty -> Literature Fabrication risk
    )

    report = AIFailureGateAuditor.audit_project(project)
    assert report.passed is False
    assert report.risk_score > 40.0
    detected_modes = {f.mode for f in report.findings}
    assert AIFailureMode.BUG_AS_INSIGHT in detected_modes
    assert AIFailureMode.EPISTEMIC_FRAME_LOCK in detected_modes
    assert AIFailureMode.SAMPLE_OVERGENERALIZATION in detected_modes
    assert AIFailureMode.LITERATURE_FABRICATION in detected_modes
