"""Scientific and methodological consistency validators."""

import re
from typing import Any

from thesisforge.models import ProjectStateDTO, ResearchApproach

# Standard academic taxonomy infinitive verbs (Bloom & Scientific Research Taxonomy)
VALID_ACADEMIC_VERBS = {
    # Exploratory / Descriptive / Qualitative
    "analizar",
    "caracterizar",
    "clasificar",
    "comparar",
    "comprender",
    "describir",
    "diagnosticar",
    "examinar",
    "explorar",
    "identificar",
    "indagar",
    "interpretar",
    "reconocer",
    "sistematizar",
    # Correlational / Explanatory
    "comprobar",
    "contrastar",
    "correlacionar",
    "demostrar",
    "determinar",
    "establecer",
    "evaluar",
    "explicar",
    "verificar",
    # Applied / Constructive
    "construir",
    "desarrollar",
    "diseñar",
    "elaborar",
    "estructurar",
    "formular",
    "implementar",
    "modelar",
    "optimizar",
    "proponer",
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

DICHOTOMOUS_STARTER_PATTERN = re.compile(
    r"^¿\s*(es|existe|existen|influye|influyen|afecta|afectan|tiene|tienen|hay|son|ser[aá])\b",
    re.IGNORECASE,
)

PROCEDURAL_TASK_PATTERNS = [
    re.compile(r"\b(revisar|consultar)\s+(la\s+)?(literatura|bibliograf[ií]a|fuentes|estado\s+del\s+arte)\b", re.IGNORECASE),
    re.compile(r"\b(elaborar|construir|redactar)\s+(el\s+)?marco\s+te[oó]rico\b", re.IGNORECASE),
    re.compile(r"\b(aplicar|administrar|pasar)\s+(las?\s+)?(encuestas?|cuestionarios?|entrevistas?|test)\b", re.IGNORECASE),
    re.compile(r"\b(recolectar|recopilar|levantar)\s+(los\s+)?(datos|informaci[oó]n|muestras)\b", re.IGNORECASE),
    re.compile(r"\b(diseñar|elaborar)\s+(los?\s+)?instrumentos?\s+de\s+recolecci[oó]n\b", re.IGNORECASE),
]

CAUSAL_VERB_PATTERNS = [
    "demostrar",
    "determinar el efecto",
    "determinar la incidencia",
    "comprobar el efecto",
    "probar la causalidad",
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
        """Validate formal research question structure and check for dichotomous formulation."""
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
            if DICHOTOMOUS_STARTER_PATTERN.search(cleaned):
                issues.append(
                    "La pregunta de investigación es dicotómica (admite respuesta cerrada de Sí/No). Transfórmala usando partículas de alta resolución (ej. '¿En qué medida...', '¿De qué manera...', '¿Cómo...')."
                )
            else:
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
        """Validate specific objectives count, infinitive verb starters, and prohibit procedural task-objectives."""
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

            # Check for procedural tasks masquerading as research objectives
            is_procedural = False
            for pattern in PROCEDURAL_TASK_PATTERNS:
                match = pattern.search(cleaned)
                if match:
                    issues.append(
                        f"El objetivo específico #{idx} describe una tarea o actividad procedimental ('{match.group(0)}'). Los objetivos deben expresar metas cognitivas de conocimiento (ej. diagnosticar, caracterizar, correlacionar, validar), no actividades del cronograma."
                    )
                    is_procedural = True
                    break

            if is_procedural:
                continue

            verb = cls.extract_first_word(cleaned)
            if verb not in VALID_ACADEMIC_VERBS:
                issues.append(
                    f"El objetivo específico #{idx} debe iniciar con un verbo en infinitivo. Verbo detectado: '{verb}'."
                )

        return issues

    @classmethod
    def validate_justification(cls, justification: str) -> list[str]:
        """Validate research justification substance and completeness."""
        issues: list[str] = []
        cleaned = justification.strip()
        if cleaned and len(cleaned) < 40:
            issues.append(
                "La justificación es demasiado escueta (debe fundamentar al menos relevancia teórica, práctica o metodológica)."
            )
        return issues

    @classmethod
    def validate_scope_limitations(cls, scope_limitations: str) -> list[str]:
        """Validate delimitations and limitations preventing rhetorical excuses."""
        issues: list[str] = []
        cleaned = scope_limitations.strip().lower()
        if cleaned:
            if re.search(r"\b(falta\s+de\s+tiempo|poco\s+tiempo|recursos\s+econ[oó]micos|falta\s+de\s+dinero)\b", cleaned) and len(cleaned) < 80:
                issues.append(
                    "Las limitaciones no deben ser excusas operativas personales (ej. falta de tiempo o dinero). Deben formularse como restricciones metodológicas reales con su efecto y estrategia de mitigación."
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
            elif len(cleaned) < 15:
                issues.append(
                    "La hipótesis cuantitativa es demasiado escueta para establecer una relación verificable entre variables."
                )
        elif (
            approach == ResearchApproach.CUALITATIVO and cleaned and "estadístic" in cleaned.lower()
        ):
            issues.append(
                "En investigaciones cualitativas puras, las hipótesis no deben plantear contrastes estadísticos formales (usar supuestos o preguntas directrices)."
            )
        elif approach == ResearchApproach.MIXTO and not cleaned:
            issues.append(
                "En investigaciones de enfoque mixto, se recomienda formular hipótesis de trabajo o supuestos directrices para integrar ambas fases metodológicas."
            )

        return issues

    @classmethod
    def validate_epistemological_alignment(
        cls,
        paradigm: str | None,
        approach: ResearchApproach | None,
        design: str = "",
    ) -> list[str]:
        """Validate philosophical and methodological alignment between paradigm, approach and design."""
        issues: list[str] = []
        if not paradigm and not design:
            return issues

        if paradigm:
            para_lower = str(paradigm).lower()
            if "positivista" in para_lower and approach == ResearchApproach.CUALITATIVO:
                issues.append(
                    "Inconsistencia epistemológica: El paradigma positivista es eminentemente cuantitativo y contradice un enfoque cualitativo puro."
                )
            elif "interpretativ" in para_lower and approach == ResearchApproach.CUANTITATIVO:
                issues.append(
                    "Inconsistencia epistemológica: El paradigma interpretativo/hermenéutico se fundamenta en la comprensión cualitativa y contradice un enfoque cuantitativo puro."
                )

        if design:
            design_lower = design.lower()
            if "experimental" in design_lower and approach == ResearchApproach.CUALITATIVO:
                issues.append(
                    "El diseño experimental implica manipulación de variables y medición cuantitativa, incompatible con un enfoque cualitativo puro."
                )

        return issues

    @classmethod
    def validate_operationalization(
        cls,
        variables: list[Any],
        approach: ResearchApproach | None,
    ) -> list[str]:
        """Validate variable operationalization matrix completeness."""
        issues: list[str] = []
        if approach == ResearchApproach.CUANTITATIVO and variables:
            for v in variables:
                v_name = getattr(v, "name", str(v))
                indicators = getattr(v, "indicators", [])
                if hasattr(v, "indicators") and not indicators:
                    issues.append(
                        f"La variable '{v_name}' carece de indicadores operacionales medibles."
                    )
        return issues

    @classmethod
    def validate_qualitative_categories(
        cls,
        categories: list[Any],
        approach: ResearchApproach | None,
    ) -> list[str]:
        """Validate qualitative categorical matrix and coding definitions."""
        issues: list[str] = []
        if approach == ResearchApproach.CUALITATIVO and categories:
            for cat in categories:
                cat_name = getattr(cat, "name", str(cat))
                cat_def = getattr(cat, "definition", "")
                if hasattr(cat, "definition") and not cat_def:
                    issues.append(
                        f"La categoría cualitativa '{cat_name}' no cuenta con definición conceptual o criterios de codificación."
                    )
        return issues

    @classmethod
    def validate_conclusions_alignment(
        cls,
        conclusions: list[str],
        specific_objectives: list[str],
    ) -> list[str]:
        """Validate isomorphism between specific objectives and specific conclusions."""
        issues: list[str] = []
        if not conclusions:
            return issues

        if specific_objectives and len(conclusions) != len(specific_objectives):
            issues.append(
                f"Discordancia en la correspondencia de conclusiones: Se declararon {len(specific_objectives)} objetivos específicos pero se formularon {len(conclusions)} conclusiones. Debe existir exactamente una conclusión por cada objetivo específico."
            )

        for idx, concl in enumerate(conclusions, start=1):
            cleaned = concl.strip()
            if len(cleaned) < 25:
                issues.append(
                    f"La conclusión #{idx} es demasiado escueta para sintetizar el significado de un objetivo específico."
                )
            if re.search(
                r"\b(?:podr[ií]a sugerir una posible mejora|parece haber indicios de que posiblemente)\b",
                cleaned,
                re.IGNORECASE,
            ):
                issues.append(
                    f"La conclusión #{idx} contiene evasivas sintácticas. Debe formularse de manera afirmativa y directa, modulando la certeza mediante el estatus epistémico."
                )

        return issues

    @classmethod
    def validate_recommendations(
        cls,
        recommendations: list[str],
    ) -> list[str]:
        """Validate that recommendations have explicit actors/recipients and actionable verbs."""
        issues: list[str] = []
        if not recommendations:
            return issues

        for idx, rec in enumerate(recommendations, start=1):
            cleaned = rec.strip()
            if len(cleaned) < 30:
                issues.append(
                    f"La recomendación #{idx} es demasiado breve. Debe incluir destinatario, acción en infinitivo, hallazgo de origen e indicador de seguimiento."
                )
            if re.search(
                r"\b(?:se recomienda mejorar la calidad(?: educativa)?|es necesario concientizar a la (?:comunidad|población|sociedad)|sería interesante (?:seguir|continuar) investigando este tema)\b",
                cleaned,
                re.IGNORECASE,
            ):
                issues.append(
                    f"La recomendación #{idx} es vacua o genérica. Debe dirigirse a un actor explícito con una acción concreta, viable y medible."
                )

        return issues

    @classmethod
    def audit_project(cls, project: ProjectStateDTO) -> dict[str, Any]:
        """Run a full consistency matrix audit across the project's methodological fields."""
        problem_issues = cls.validate_problem_statement(project.research_problem)
        question_issues = cls.validate_research_question(project.research_question)
        general_obj_issues = cls.validate_general_objective(
            project.general_objective, project.research_question
        )
        spec_obj_issues = cls.validate_specific_objectives(project.specific_objectives)
        hypo_issues = cls.validate_hypothesis(project.hypothesis, project.methodology.approach)
        epistem_issues = cls.validate_epistemological_alignment(
            project.methodology.paradigm.value if project.methodology.paradigm else None,
            project.methodology.approach,
            project.methodology.design,
        )
        op_issues = cls.validate_operationalization(
            project.operationalized_variables, project.methodology.approach
        )
        cat_issues = cls.validate_qualitative_categories(
            project.qualitative_categories, project.methodology.approach
        )

        justification_issues = cls.validate_justification(project.justification)
        scope_issues = cls.validate_scope_limitations(project.scope_limitations)

        all_issues: list[str] = (
            problem_issues
            + question_issues
            + general_obj_issues
            + spec_obj_issues
            + justification_issues
            + scope_issues
            + hypo_issues
            + epistem_issues
            + op_issues
            + cat_issues
        )

        # Severity-weighted penalty calculation
        penalty = 0
        if problem_issues:
            penalty += 15 * len(problem_issues)
        if question_issues:
            penalty += 25 * len(question_issues)
        if general_obj_issues:
            penalty += 25 * len(general_obj_issues)
        if spec_obj_issues:
            for iss in spec_obj_issues:
                penalty += 15 if "al menos 2" in iss else 5
        if justification_issues:
            penalty += 5 * len(justification_issues)
        if scope_issues:
            penalty += 5 * len(scope_issues)
        if hypo_issues:
            penalty += 15 * len(hypo_issues)
        if epistem_issues:
            penalty += 20 * len(epistem_issues)
        if op_issues:
            penalty += 10 * len(op_issues)
        if cat_issues:
            penalty += 10 * len(cat_issues)

        score = max(0, 100 - penalty)
        is_consistent = len(all_issues) == 0

        return {
            "score": score,
            "is_consistent": is_consistent,
            "issues": all_issues,
            "status": "APPROVED" if is_consistent else "REVISION_REQUIRED",
        }
