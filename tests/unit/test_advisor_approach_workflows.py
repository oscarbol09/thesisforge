"""Unit tests for approach-aware advisor workflows and validation rules."""

from thesisforge.advisor.state_machine import (
    AdvisorStateMachine,
    AdvisorStep,
    get_step_sequence_for_approach,
)
from thesisforge.advisor.validators import MethodologyValidator
from thesisforge.models import (
    EpistemologicalParadigm,
    MeasurementScale,
    QualitativeCategoryDTO,
    ResearchApproach,
    VariableOperationalizationDTO,
    VariableType,
)


def test_step_sequence_quantitative() -> None:
    """Quantitative approach requires hypotheses and operationalization, skips categories."""
    seq = get_step_sequence_for_approach(ResearchApproach.CUANTITATIVO)
    assert AdvisorStep.HYPOTHESIS in seq
    assert AdvisorStep.OPERATIONALIZATION in seq
    assert AdvisorStep.CATEGORIES not in seq
    assert AdvisorStep.PARADIGM_AND_APPROACH in seq
    assert AdvisorStep.ETHICS_AND_SAMPLING in seq


def test_step_sequence_qualitative() -> None:
    """Qualitative approach requires categories, skips hypotheses and operationalization."""
    seq = get_step_sequence_for_approach(ResearchApproach.CUALITATIVO)
    assert AdvisorStep.HYPOTHESIS not in seq
    assert AdvisorStep.OPERATIONALIZATION not in seq
    assert AdvisorStep.CATEGORIES in seq
    assert AdvisorStep.PARADIGM_AND_APPROACH in seq
    assert AdvisorStep.ETHICS_AND_SAMPLING in seq


def test_step_sequence_mixed() -> None:
    """Mixed approach includes both operationalization and qualitative categories."""
    seq = get_step_sequence_for_approach(ResearchApproach.MIXTO)
    assert AdvisorStep.HYPOTHESIS in seq
    assert AdvisorStep.OPERATIONALIZATION in seq
    assert AdvisorStep.CATEGORIES in seq
    assert AdvisorStep.PARADIGM_AND_APPROACH in seq


def test_step_sequence_string_and_none() -> None:
    """Sequence resolver handles string approach names and None correctly."""
    seq_str = get_step_sequence_for_approach("cualitativo")
    assert AdvisorStep.CATEGORIES in seq_str
    assert AdvisorStep.HYPOTHESIS not in seq_str

    seq_none = get_step_sequence_for_approach(None)
    assert AdvisorStep.PARADIGM_AND_APPROACH in seq_none


def test_validate_epistemological_alignment_valid_positivism() -> None:
    """Positivism matches quantitative approach."""
    issues = MethodologyValidator.validate_epistemological_alignment(
        paradigm=EpistemologicalParadigm.POSITIVISTA.value,
        approach=ResearchApproach.CUANTITATIVO,
    )
    assert len(issues) == 0


def test_validate_epistemological_alignment_conflict_positivism_qualitative() -> None:
    """Positivism with qualitative approach generates an epistemological conflict issue."""
    issues = MethodologyValidator.validate_epistemological_alignment(
        paradigm=EpistemologicalParadigm.POSITIVISTA.value,
        approach=ResearchApproach.CUALITATIVO,
    )
    assert len(issues) == 1
    assert "Inconsistencia epistemológica" in issues[0]


def test_validate_epistemological_alignment_experimental_with_qualitative() -> None:
    """Experimental design with qualitative approach generates an issue."""
    issues = MethodologyValidator.validate_epistemological_alignment(
        paradigm=None,
        approach=ResearchApproach.CUALITATIVO,
        design="Cuasiexperimental con grupo control",
    )
    assert len(issues) == 1
    assert "El diseño experimental implica manipulación" in issues[0]


def test_validate_operationalization_valid() -> None:
    """Valid variable operationalization matrix passes checks."""
    vars_list = [
        VariableOperationalizationDTO(
            name="Clima Laboral",
            variable_type=VariableType.INDEPENDIENTE,
            conceptual_definition="Percepción global del ambiente de trabajo.",
            operational_definition="Puntuación total en escala de Likert.",
            dimensions=["Liderazgo", "Comunicación"],
            indicators=["Frecuencia de reuniones", "Claridad de directivas"],
            measurement_scale=MeasurementScale.ORDINAL,
            instrument_name="Cuestionario de Clima Organizacional",
        )
    ]
    issues = MethodologyValidator.validate_operationalization(
        variables=vars_list,
        approach=ResearchApproach.CUANTITATIVO,
    )
    assert len(issues) == 0


def test_validate_operationalization_missing_indicators() -> None:
    """Quantitative variable without indicators generates an issue."""
    vars_list = [
        VariableOperationalizationDTO(
            name="Variable Incompleta",
            variable_type=VariableType.INDEPENDIENTE,
            dimensions=["D1"],
            indicators=[],
        )
    ]
    issues = MethodologyValidator.validate_operationalization(
        variables=vars_list,
        approach=ResearchApproach.CUANTITATIVO,
    )
    assert len(issues) == 1
    assert "carece de indicadores operacionales" in issues[0]


def test_validate_qualitative_categories_valid() -> None:
    """Valid qualitative categories pass validation."""
    cats = [
        QualitativeCategoryDTO(
            name="Experiencia de Innovación",
            definition="Percepción del proceso de adopción tecnológica.",
            subcategories=["Resistencia", "Facilitadores"],
        )
    ]
    issues = MethodologyValidator.validate_qualitative_categories(
        categories=cats,
        approach=ResearchApproach.CUALITATIVO,
    )
    assert len(issues) == 0


def test_validate_qualitative_categories_missing_definition() -> None:
    """Qualitative category without definition generates an issue."""
    cats = [
        QualitativeCategoryDTO(
            name="Categoría Sin Definir",
            definition="",
        )
    ]
    issues = MethodologyValidator.validate_qualitative_categories(
        categories=cats,
        approach=ResearchApproach.CUALITATIVO,
    )
    assert len(issues) == 1
    assert "no cuenta con definición conceptual" in issues[0]


def test_state_machine_approach_routing() -> None:
    """AdvisorStateMachine transitions follow custom sequences per approach."""
    qual_order = get_step_sequence_for_approach(ResearchApproach.CUALITATIVO)
    next_step = AdvisorStateMachine.get_next_step(
        AdvisorStep.OBJECTIVES,
        step_order=qual_order,
    )
    assert next_step == AdvisorStep.CATEGORIES

    quant_order = get_step_sequence_for_approach(ResearchApproach.CUANTITATIVO)
    next_quant = AdvisorStateMachine.get_next_step(
        AdvisorStep.OBJECTIVES,
        step_order=quant_order,
    )
    assert next_quant == AdvisorStep.HYPOTHESIS
