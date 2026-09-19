"""Unit tests for methodological consistency validators."""

from thesisforge.advisor.validators import MethodologyValidator
from thesisforge.models import (
    ProjectStateDTO,
)


def test_validate_problem_statement_valid():
    """Test valid research problem passes."""
    problem = "En las instituciones de educación superior se evidencia una brecha crítica en la adopción de herramientas de inteligencia artificial para la redacción científica."
    issues = MethodologyValidator.validate_problem_statement(problem)
    assert len(issues) == 0


def test_validate_problem_statement_too_short():
    """Test short problem statement produces issue."""
    short_problem = "Faltan herramientas de IA."
    issues = MethodologyValidator.validate_problem_statement(short_problem)
    assert len(issues) == 1
    assert "demasiado breve" in issues[0]


def test_validate_research_question_valid():
    """Test formal research question."""
    question = "¿En qué medida el uso de RAG mejora la exactitud de las citas bibliográficas en tesis de pregrado?"
    issues = MethodologyValidator.validate_research_question(question)
    assert len(issues) == 0


def test_validate_research_question_missing_marks_or_starter():
    """Test research question missing question marks or interrogative pronoun."""
    bad_q = "El impacto del RAG en las citas"
    issues = MethodologyValidator.validate_research_question(bad_q)
    assert len(issues) >= 1


def test_validate_general_objective_valid():
    """Test general objective starting with valid Bloom taxonomy verb."""
    obj = "Determinar el impacto del sistema ThesisForge en la coherencia metodológica de los proyectos de grado."
    issues = MethodologyValidator.validate_general_objective(obj)
    assert len(issues) == 0


def test_validate_general_objective_invalid_verb():
    """Test general objective starting with an unscientific verb."""
    bad_obj = "Hacer un software para ayudar a los estudiantes con sus tesis."
    issues = MethodologyValidator.validate_general_objective(bad_obj)
    assert len(issues) == 1
    assert "debe iniciar con un verbo formal en infinitivo" in issues[0]


def test_validate_specific_objectives():
    """Test specific objectives count and verbs."""
    good_objs = [
        "Diagnosticar los errores metodológicos más frecuentes en proyectos de grado.",
        "Diseñar la arquitectura de software basada en RAG para asistencia científica.",
        "Evaluar la efectividad del sistema mediante un estudio cuasiexperimental.",
    ]
    assert len(MethodologyValidator.validate_specific_objectives(good_objs)) == 0

    insufficient_objs = ["Diagnosticar los errores."]
    issues = MethodologyValidator.validate_specific_objectives(insufficient_objs)
    assert len(issues) == 1


def test_audit_project_full_consistency(sample_project: ProjectStateDTO):
    """Test full consistency matrix audit on sample project."""
    audit = MethodologyValidator.audit_project(sample_project)
    assert audit["is_consistent"] is True
    assert audit["score"] == 100
    assert audit["status"] == "APPROVED"
