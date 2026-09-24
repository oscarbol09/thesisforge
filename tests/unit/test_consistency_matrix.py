"""Unit tests for the Methodological Consistency Matrix and Validity Threats Engine."""


from thesisforge.advisor.consistency_matrix import (
    ConsistencyMatrixEngine,
)
from thesisforge.models import (
    AcademicLevel,
    MeasurementScale,
    MethodologyDTO,
    ProjectStateDTO,
    ResearchApproach,
    SamplingTechnique,
    VariableOperationalizationDTO,
    VariableType,
)


def test_consistency_matrix_builds_aligned_rows_and_markdown() -> None:
    project = ProjectStateDTO(
        id="matrix_proj",
        title="Impacto de la Inteligencia Artificial en la Educación",
        academic_level=AcademicLevel.MAESTRIA,
        research_question="¿Cómo impacta la IA generativa en la retención académica?",
        general_objective="Determinar el impacto de la IA generativa en la retención académica.",
        specific_objectives=[
            "Diagnosticar el nivel actual de uso de herramientas de IA.",
            "Evaluar el índice de retención de los estudiantes usuarios.",
        ],
        hypothesis="El uso pedagógico de la IA incrementa significativamente la retención.",
        operationalized_variables=[
            VariableOperationalizationDTO(
                name="Uso de IA",
                variable_type=VariableType.INDEPENDIENTE,
                measurement_scale=MeasurementScale.INTERVALO,
                indicators=["Frecuencia", "Horas semanales"],
            ),
            VariableOperationalizationDTO(
                name="Retención Académica",
                variable_type=VariableType.DEPENDIENTE,
                measurement_scale=MeasurementScale.INTERVALO,
                indicators=["Tasa de permanencia", "Créditos aprobados"],
            ),
        ],
        methodology=MethodologyDTO(
            approach=ResearchApproach.CUANTITATIVO,
            design="Cuasiexperimental longitudinal",
            instruments=["Cuestionario de Adopción Tecnológica", "Registro Académico"],
            analysis_technique="Regresión lineal y Pearson",
            temporal_scope="longitudinal",
            sampling_technique=SamplingTechnique.NO_PROBABILISTICO_INTENCIONAL,
        ),
    )

    report = ConsistencyMatrixEngine.build_matrix(project)
    assert report.is_fully_consistent is True
    assert report.overall_alignment_score >= 80.0
    assert len(report.rows) == 2
    assert report.rows[0].is_scale_compatible is True

    # Check validity threats
    threat_names = {t.name for t in report.validity_threats}
    assert "Mortalidad Experimental / Atrición" in threat_names
    assert "Sesgo de Muestreo No Probabilístico" in threat_names

    md_table = report.to_markdown_table()
    assert "| # | Pregunta Específica |" in md_table
    assert "VI: Uso de IA" in md_table
    assert "VD: Retención Académica" in md_table


def test_scale_compatibility_flags_incompatible_tests() -> None:
    variables = [
        VariableOperationalizationDTO(
            name="Nivel Socioeconómico",
            variable_type=VariableType.INDEPENDIENTE,
            measurement_scale=MeasurementScale.NOMINAL,
        )
    ]
    # Pearson requires Interval/Ratio, so Nominal should be flagged
    is_compat, note = ConsistencyMatrixEngine.check_scale_compatibility(variables, "Correlación de Pearson")
    assert is_compat is False
    assert "Incompatibilidad" in note


def test_scale_compatibility_accepts_compatible_tests() -> None:
    variables = [
        VariableOperationalizationDTO(
            name="Satisfacción Laboral",
            variable_type=VariableType.DEPENDIENTE,
            measurement_scale=MeasurementScale.ORDINAL,
        )
    ]
    is_compat, note = ConsistencyMatrixEngine.check_scale_compatibility(variables, "Prueba de Mann Whitney")
    assert is_compat is True
    assert "Compatible" in note
