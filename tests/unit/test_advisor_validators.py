"""Unit tests for methodological consistency validators."""

from thesisforge.advisor.validators import MethodologyValidator
from thesisforge.models import (
    ProjectStateDTO,
    ResearchApproach,
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


def test_validate_hypothesis_approaches():
    """Test hypothesis validation across quantitative, qualitative, and mixed approaches."""
    # Quantitative empty -> issue
    issues = MethodologyValidator.validate_hypothesis("", ResearchApproach.CUANTITATIVO)
    assert len(issues) == 1
    assert "altamente recomendable" in issues[0]

    # Quantitative too short -> issue
    issues = MethodologyValidator.validate_hypothesis("Corta", ResearchApproach.CUANTITATIVO)
    assert len(issues) == 1
    assert "demasiado escueta" in issues[0]

    # Quantitative valid -> no issues
    issues = MethodologyValidator.validate_hypothesis(
        "El uso de ThesisForge incrementa significativamente la precisión bibliográfica.",
        ResearchApproach.CUANTITATIVO,
    )
    assert len(issues) == 0

    # Qualitative with statistical hypothesis -> issue
    issues = MethodologyValidator.validate_hypothesis(
        "Se realizará un contraste estadístico de medias.", ResearchApproach.CUALITATIVO
    )
    assert len(issues) == 1
    assert "no deben plantear contrastes estadísticos" in issues[0]

    # Mixed without hypothesis -> recommendation issue
    issues = MethodologyValidator.validate_hypothesis("", ResearchApproach.MIXTO)
    assert len(issues) == 1
    assert "enfoque mixto" in issues[0]


def test_validate_research_question_dichotomous_detection():
    """Test dichotomous questions are flagged."""
    dichotomous_q1 = "¿Existe relación entre la motivación y el rendimiento académico?"
    issues1 = MethodologyValidator.validate_research_question(dichotomous_q1)
    assert len(issues1) == 1
    assert "dicotómica" in issues1[0]

    dichotomous_q2 = "¿Influye el uso de RAG en la precisión?"
    issues2 = MethodologyValidator.validate_research_question(dichotomous_q2)
    assert len(issues2) == 1
    assert "dicotómica" in issues2[0]


def test_validate_specific_objectives_procedural_tasks_rejected():
    """Test procedural activities in specific objectives are flagged as errors."""
    bad_objs = [
        "Revisar la literatura sobre inteligencia artificial generativa.",
        "Elaborar el marco teórico de la investigación.",
        "Aplicar encuestas a los estudiantes de posgrado.",
    ]
    issues = MethodologyValidator.validate_specific_objectives(bad_objs)
    assert len(issues) == 3
    for iss in issues:
        assert "tarea o actividad procedimental" in iss


def test_validate_justification_and_scope():
    """Test justification and scope validation."""
    short_just = "Es muy importante."
    issues_j = MethodologyValidator.validate_justification(short_just)
    assert len(issues_j) == 1
    assert "demasiado escueta" in issues_j[0]

    good_just = "La investigación posee relevancia teórica al contrastar modelos de memoria jerárquica y relevancia práctica al reducir errores en redacción académica."
    assert len(MethodologyValidator.validate_justification(good_just)) == 0

    bad_scope = "Por falta de tiempo no pudimos entrevistar a más personas."
    issues_s = MethodologyValidator.validate_scope_limitations(bad_scope)
    assert len(issues_s) == 1
    assert "excusas operativas" in issues_s[0]


def test_validate_conclusions_alignment():
    """Test isomorphism between specific objectives count and conclusions count."""
    objectives = [
        "Diagnosticar el nivel de estrés laboral en los docentes.",
        "Determinar la asociación entre estrés y autoeficacia docente.",
        "Evaluar la efectividad del programa de intervención psicoeducativo.",
    ]
    conclusions_matching = [
        "El diagnóstico evidenció niveles moderados de estrés en la muestra evaluada.",
        "Existe una correlación inversa estadísticamente significativa entre estrés y autoeficacia.",
        "El programa de intervención redujo significativamente los puntajes de estrés docente.",
    ]
    assert (
        len(MethodologyValidator.validate_conclusions_alignment(conclusions_matching, objectives))
        == 0
    )

    conclusions_mismatch = [
        "El diagnóstico evidenció niveles moderados de estrés en la muestra.",
    ]
    issues = MethodologyValidator.validate_conclusions_alignment(conclusions_mismatch, objectives)
    assert len(issues) == 1
    assert "Discordancia en la correspondencia de conclusiones" in issues[0]

    conclusions_evasion = [
        "El diagnóstico evidenció niveles moderados de estrés en la muestra evaluada.",
        "En los datos analizados, parece haber indicios de que posiblemente existe relación.",
        "El programa de intervención redujo significativamente los puntajes de estrés docente.",
    ]
    issues_ev = MethodologyValidator.validate_conclusions_alignment(conclusions_evasion, objectives)
    assert len(issues_ev) == 1
    assert "evasivas sintácticas" in issues_ev[0]


def test_validate_recommendations():
    """Test validation of recommendations with explicit actors and actionable verbs."""
    good_recs = [
        "Se recomienda a la coordinación académica diseñar un programa de acompañamiento docente semestral.",
        "Se recomienda a los investigadores replicar el diseño longitudinal en instituciones rurales.",
    ]
    assert len(MethodologyValidator.validate_recommendations(good_recs)) == 0

    vacuous_recs = [
        "Se recomienda mejorar la calidad educativa en todas las escuelas.",
    ]
    issues = MethodologyValidator.validate_recommendations(vacuous_recs)
    assert len(issues) == 1
    assert "vacua o genérica" in issues[0]
