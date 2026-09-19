"""Scientific and methodological consistency validators."""

import re
from typing import Any

from thesisforge.models import ProjectStateDTO, ResearchApproach

# Standard academic taxonomy infinitive verbs (Bloom & Scientific Research Taxonomy)
VALID_ACADEMIC_VERBS = {
    # Exploratory / Descriptive
    "analizar",
    "caracterizar",
    "clasificar",
    "comparar",
    "describir",
    "diagnosticar",
    "examinar",
    "explorar",
    "identificar",
    "interpretar",
    # Correlational / Explanatory
    "determinar",
    "establecer",
    "evaluar",
    "explicar",
    "demostrar",
    "correlacionar",
    "comprobar",
    "contrastar",
    # Applied / Constructive
    "diseñar",
    "desarrollar",
    "implementar",
    "construir",
    "formular",
    "proponer",
    "optimizar",
    "modelar",
    "validar",
}

INTERROGATIVE_STARTERS = [
    "cómo",
    "en qué medida",
    "de qué manera",
    "cuál",
    "cuáles",
    "qué",
    "por qué",
    "cuánto",
    "cuánta",
    "hasta qué punto",
]


class MethodologyValidator:
    """Scientific validator ensuring alignment between problem, questions, objectives, and methods."""

    @staticmethod
    def extract_first_word(text: str) -> str:
        """Extract the first cleaned word from a sentence."""
        words = re.findall(r"\b\w+\b", text.strip().lower())
        return words[0] if words else ""

    @classmethod
    def validate_problem_statement(cls, problem: str) -> list[str]:
        """Validate research problem description."""
        issues: list[str] = []
        cleaned = problem.strip()
        if len(cleaned) < 50:
            issues.append(
                "El planteamiento del problema es demasiado breve (mínimo 50 caracteres para describir contexto, síntomas y causas)."
            )
        return issues

    @classmethod
    def validate_research_question(cls, question: str) -> list[str]:
        """Validate formal research question structure."""
        issues: list[str] = []
        cleaned = question.strip()

        if not cleaned:
            issues.append("La pregunta de investigación no puede estar vacía.")
            return issues

        if not (cleaned.startswith("¿") or cleaned.endswith("?")):
            issues.append(
                "La pregunta de investigación debe estar formulada con signos de interrogación formales (¿...?)."
            )

        lower_q = cleaned.lower()
        has_starter = any(starter in lower_q for starter in INTERROGATIVE_STARTERS)
        if not has_starter:
            issues.append(
                "La pregunta debe iniciar con una partícula interrogativa formal (ej. '¿Cómo...', '¿En qué medida...', '¿Cuál...')."
            )

        return issues

    @classmethod
    def validate_general_objective(cls, objective: str, question: str = "") -> list[str]:
        """Validate that general objective starts with an academic infinitive verb."""
        issues: list[str] = []
        cleaned = objective.strip()

        if not cleaned:
            issues.append("El objetivo general no puede estar vacío.")
            return issues

        first_verb = cls.extract_first_word(cleaned)
        if first_verb not in VALID_ACADEMIC_VERBS:
            issues.append(
                f"El objetivo general debe iniciar con un verbo formal en infinitivo (ej. Determinar, Analizar, Evaluar, Diseñar). Verbo detectado: '{first_verb}'."
            )

        return issues

    @classmethod
    def validate_specific_objectives(cls, objectives: list[str]) -> list[str]:
        """Validate specific objectives count and infinitive verb starters."""
        issues: list[str] = []
        if len(objectives) < 2:
            issues.append(
                "Se requieren al menos 2 objetivos específicos (idealmente 3: diagnóstico, desarrollo/diseño y evaluación/impacto)."
            )

        for idx, obj in enumerate(objectives, start=1):
            cleaned = obj.strip()
            if not cleaned:
                issues.append(f"El objetivo específico #{idx} está vacío.")
                continue
            verb = cls.extract_first_word(cleaned)
            if verb not in VALID_ACADEMIC_VERBS:
                issues.append(
                    f"El objetivo específico #{idx} debe iniciar con un verbo en infinitivo. Verbo detectado: '{verb}'."
                )

        return issues

    @classmethod
    def validate_hypothesis(
        cls, hypothesis: str | None, approach: ResearchApproach | None
    ) -> list[str]:
        """Validate hypothesis consistency based on research approach."""
        issues: list[str] = []
        cleaned = (hypothesis or "").strip()

        if approach == ResearchApproach.CUANTITATIVO:
            if not cleaned:
                issues.append(
                    "Para investigaciones con enfoque cuantitativo, es altamente recomendable o requerida una hipótesis explícita y contrastable."
                )
        elif (
            approach == ResearchApproach.CUALITATIVO and cleaned and "estadístic" in cleaned.lower()
        ):
            issues.append(
                "En investigaciones cualitativas puras, las hipótesis no deben plantear contrastes estadísticos formales (usar supuestos o preguntas directrices)."
            )

        return issues

    @classmethod
    def audit_project(cls, project: ProjectStateDTO) -> dict[str, Any]:
        """Run a full consistency matrix audit across the project's methodological fields."""
        all_issues: list[str] = []
        all_issues.extend(cls.validate_problem_statement(project.research_problem))
        all_issues.extend(cls.validate_research_question(project.research_question))
        all_issues.extend(
            cls.validate_general_objective(project.general_objective, project.research_question)
        )
        all_issues.extend(cls.validate_specific_objectives(project.specific_objectives))
        all_issues.extend(cls.validate_hypothesis(project.hypothesis, project.methodology.approach))

        score = max(0, 100 - (len(all_issues) * 15))
        is_consistent = len(all_issues) == 0

        return {
            "score": score,
            "is_consistent": is_consistent,
            "issues": all_issues,
            "status": "APPROVED" if is_consistent else "REVISION_REQUIRED",
        }
