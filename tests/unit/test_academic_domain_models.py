"""Unit tests for enriched academic domain models and validation rules."""

from thesisforge.models import (
    EpistemologicalParadigm,
    MeasurementScale,
    MethodologyDTO,
    ProjectStateDTO,
    QualitativeCategoryDTO,
    ResearchApproach,
    SamplingTechnique,
    VariableOperationalizationDTO,
    VariableType,
)


def test_epistemological_paradigm_enum_values() -> None:
    """Verify EpistemologicalParadigm enum values."""
    assert EpistemologicalParadigm.POSITIVISTA.value == "positivista"
    assert EpistemologicalParadigm.POSTPOSITIVISTA.value == "postpositivista"
    assert EpistemologicalParadigm.INTERPRETATIVO.value == "interpretativo"
    assert EpistemologicalParadigm.SOCIOCRITICO.value == "sociocritico"
    assert EpistemologicalParadigm.PRAGMATICO.value == "pragmatico"


def test_sampling_technique_enum_values() -> None:
    """Verify SamplingTechnique enum values."""
    assert SamplingTechnique.PROBABILISTICO_ALEATORIO.value == "probabilistico_aleatorio"
    assert SamplingTechnique.PROBABILISTICO_ESTRATIFICADO.value == "probabilistico_estratificado"
    assert SamplingTechnique.PROBABILISTICO_CONGLOMERADOS.value == "probabilistico_conglomerados"
    assert SamplingTechnique.NO_PROBABILISTICO_INTENCIONAL.value == "no_probabilistico_intencional"
    assert SamplingTechnique.NO_PROBABILISTICO_BOLA_NIEVE.value == "no_probabilistico_bola_nieve"
    assert SamplingTechnique.NO_PROBABILISTICO_POR_CUOTAS.value == "no_probabilistico_por_cuotas"
    assert SamplingTechnique.CENSO_COMPLETO.value == "censo_completo"


def test_variable_operationalization_dto_valid() -> None:
    """Verify VariableOperationalizationDTO construction with valid data."""
    var = VariableOperationalizationDTO(
        name="Rendimiento Académico",
        variable_type=VariableType.DEPENDIENTE,
        conceptual_definition="Nivel de conocimiento y competencias alcanzadas por el estudiante.",
        operational_definition="Promedio ponderado acumulado en escala vigesimal.",
        dimensions=["Rendimiento Teórico", "Rendimiento Práctico"],
        indicators=["Calificación examen final", "Puntaje de laboratorios"],
        measurement_scale=MeasurementScale.INTERVALO,
        instrument_name="Registro de actas académicas oficiales",
    )
    assert var.name == "Rendimiento Académico"
    assert var.variable_type == VariableType.DEPENDIENTE
    assert var.measurement_scale == MeasurementScale.INTERVALO
    assert len(var.dimensions) == 2
    assert len(var.indicators) == 2
    assert var.instrument_name == "Registro de actas académicas oficiales"


def test_qualitative_category_dto_valid() -> None:
    """Verify QualitativeCategoryDTO construction."""
    cat = QualitativeCategoryDTO(
        name="Significado de la Autonomía Pedagógica",
        category_type="central",
        definition="Percepciones sobre el margen de decisión curricular de los docentes.",
        subcategories=["Libertad de cátedra", "Restricciones institucionales"],
        coding_criteria="Menciones explícitas a toma de decisiones curriculares.",
        saturation_indicator="Ausencia de nuevos códigos tras 12 entrevistas.",
    )
    assert cat.name == "Significado de la Autonomía Pedagógica"
    assert len(cat.subcategories) == 2
    assert cat.category_type == "central"
    assert "decisión curricular" in cat.definition


def test_methodology_dto_enrichment() -> None:
    """Verify enriched MethodologyDTO fields including paradigm and ethical considerations."""
    meth = MethodologyDTO(
        approach=ResearchApproach.CUALITATIVO,
        paradigm=EpistemologicalParadigm.INTERPRETATIVO,
        design="Fenomenológico hermenéutico",
        sampling_technique=SamplingTechnique.NO_PROBABILISTICO_INTENCIONAL,
        ethical_considerations=["Consentimiento informado firmado", "Anonimización de identidades"],
    )
    assert meth.paradigm == EpistemologicalParadigm.INTERPRETATIVO
    assert meth.sampling_technique == SamplingTechnique.NO_PROBABILISTICO_INTENCIONAL
    assert len(meth.ethical_considerations) == 2


def test_project_state_dto_with_methodological_fields() -> None:
    """Verify ProjectStateDTO carries all new methodology data seamlessly."""
    project = ProjectStateDTO(
        id="proj-domain-test",
        title="Estudio Hermenéutico sobre la Práctica Docente",
        methodology=MethodologyDTO(
            approach=ResearchApproach.CUALITATIVO,
            paradigm=EpistemologicalParadigm.INTERPRETATIVO,
            sampling_technique=SamplingTechnique.NO_PROBABILISTICO_INTENCIONAL,
            ethical_considerations=["Anonimización estricta bajo declaración de Helsinki."],
        ),
        qualitative_categories=[
            QualitativeCategoryDTO(
                name="Identidad Profesional",
                definition="Auto-percepción del rol docente.",
            )
        ],
        operationalized_variables=[
            VariableOperationalizationDTO(
                name="Desempeño",
                dimensions=["Eficacia"],
                indicators=["Tasa de aprobación"],
            )
        ],
    )
    assert project.methodology.approach == ResearchApproach.CUALITATIVO
    assert project.methodology.paradigm == EpistemologicalParadigm.INTERPRETATIVO
    assert len(project.qualitative_categories) == 1
    assert project.qualitative_categories[0].name == "Identidad Profesional"
    assert len(project.operationalized_variables) == 1
