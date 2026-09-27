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


def test_methodology_dto_long_descriptions() -> None:
    """MethodologyDTO accommodates comprehensive academic descriptions up to 3000 characters."""
    from thesisforge.models import MethodologyDTO

    long_analysis = (
        "Análisis de contenido temático asistido por codificación axial. " * 30
    ).strip()
    assert len(long_analysis) > 600
    dto = MethodologyDTO(
        approach=ResearchApproach.CUALITATIVO,
        analysis_technique=long_analysis,
        design="Diseño fenomenológico hermenéutico con saturación teórica...",
    )
    assert dto.analysis_technique == long_analysis


async def test_advisor_service_approve_methodology_idempotent() -> None:
    """Approve methodology transitions from ORIENTATION to CONTEXT, and is idempotent if called again."""
    from thesisforge.advisor.service import AdvisorService
    from thesisforge.config import AppSettings
    from thesisforge.llm.router import LLMRouter
    from thesisforge.models import ProjectPhase, ProjectStateDTO
    from thesisforge.repository.database import DatabaseManager
    from thesisforge.repository.project_repository import ProjectRepository

    db = DatabaseManager("sqlite+aiosqlite:///:memory:")
    await db.initialize()
    repo = ProjectRepository(db)
    llm = LLMRouter(AppSettings())
    service = AdvisorService(repo, llm)

    # Create fully consistent project
    project = ProjectStateDTO(
        id="test-proj-01",
        title="Estudio sobre IA Generativa y Educación",
        area_of_study="Ciencias de la Educación",
        topic="IA Generativa",
        research_problem="La irrupción de las IA generativas en la educación superior genera desafíos pedagógicos sustanciales...",
        research_question="¿En qué medida la IA generativa impacta en el rendimiento académico de los estudiantes?",
        general_objective="Determinar el impacto de la IA generativa en el rendimiento académico.",
        specific_objectives=[
            "Diagnosticar el nivel actual de adopción de herramientas de IA.",
            "Evaluar la correlación entre uso de IA y calificaciones promedio.",
        ],
        hypothesis="El uso guiado de IA generativa se asocia con un mayor rendimiento académico.",
    )
    project.phase = ProjectPhase.ORIENTATION
    await repo.create_project(project)

    # First approval -> transitions to CONTEXT
    approved = await service.approve_methodology(project.id)
    assert approved.phase == ProjectPhase.CONTEXT

    # Second approval -> idempotent, remains CONTEXT without error
    reapproved = await service.approve_methodology(project.id)
    assert reapproved.phase == ProjectPhase.CONTEXT
