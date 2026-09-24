"""Methodological Consistency Matrix and Validity Threats Engine.

Constructs formal 6-pillar alignment matrices (Question -> Objective -> Hypothesis -> Variables -> Instrument -> Statistical Test)
and audits threats to internal, external, construct, and statistical conclusion validity.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from thesisforge.core.time import utc_now
from thesisforge.models import (
    MeasurementScale,
    ProjectStateDTO,
    ResearchApproach,
    VariableOperationalizationDTO,
    VariableType,
)

# Known statistical tests mapped to their compatible measurement scales
STATISTICAL_TEST_SCALE_MAP: dict[str, list[MeasurementScale]] = {
    # Non-parametric tests for Nominal
    "chi_cuadrado": [MeasurementScale.NOMINAL, MeasurementScale.ORDINAL],
    "fisher": [MeasurementScale.NOMINAL],
    "regresion_logistica": [MeasurementScale.NOMINAL, MeasurementScale.ORDINAL, MeasurementScale.INTERVALO, MeasurementScale.RAZON],
    # Non-parametric tests for Ordinal
    "spearman": [MeasurementScale.ORDINAL, MeasurementScale.INTERVALO, MeasurementScale.RAZON],
    "mann_whitney": [MeasurementScale.ORDINAL, MeasurementScale.INTERVALO, MeasurementScale.RAZON],
    "wilcoxon": [MeasurementScale.ORDINAL, MeasurementScale.INTERVALO, MeasurementScale.RAZON],
    "kruskal_wallis": [MeasurementScale.ORDINAL, MeasurementScale.INTERVALO, MeasurementScale.RAZON],
    "kendall": [MeasurementScale.ORDINAL],
    # Parametric tests requiring Interval or Ratio
    "pearson": [MeasurementScale.INTERVALO, MeasurementScale.RAZON],
    "t_student": [MeasurementScale.INTERVALO, MeasurementScale.RAZON],
    "anova": [MeasurementScale.INTERVALO, MeasurementScale.RAZON],
    "regresion_lineal": [MeasurementScale.INTERVALO, MeasurementScale.RAZON],
    "ancova": [MeasurementScale.INTERVALO, MeasurementScale.RAZON],
    "sem": [MeasurementScale.INTERVALO, MeasurementScale.RAZON],
}


class ValidityThreat(BaseModel):
    """Scientific threat to methodological validity."""

    model_config = ConfigDict(extra="ignore")

    domain: str = Field(description="internal, external, construct, or statistical_conclusion")
    name: str
    description: str
    mitigation_strategy: str


class ConsistencyMatrixRow(BaseModel):
    """An individual aligned row in the master methodological consistency matrix."""

    model_config = ConfigDict(extra="ignore")

    row_index: int = Field(ge=1)
    research_question: str
    specific_objective: str
    hypothesis: str | None = None
    independent_variables: list[str] = Field(default_factory=list)
    dependent_variables: list[str] = Field(default_factory=list)
    control_variables: list[str] = Field(default_factory=list)
    instrument: str = ""
    analysis_technique_or_test: str = ""
    is_scale_compatible: bool = True
    compatibility_note: str = ""


class ConsistencyMatrixReport(BaseModel):
    """Master Methodological Consistency Matrix and Validity Audit."""

    model_config = ConfigDict(extra="ignore")

    project_id: str
    academic_level: str
    approach: ResearchApproach
    overall_alignment_score: float = Field(ge=0.0, le=100.0)
    rows: list[ConsistencyMatrixRow] = Field(default_factory=list)
    validity_threats: list[ValidityThreat] = Field(default_factory=list)
    alignment_issues: list[str] = Field(default_factory=list)
    is_fully_consistent: bool = True
    generated_at: str = Field(default_factory=lambda: utc_now().isoformat())

    def to_markdown_table(self) -> str:
        """Render consistency matrix as an academic Markdown table."""
        header = (
            "| # | Pregunta Específica | Objetivo Específico | Hipótesis | Variables (VI / VD) | Instrumento | Análisis / Prueba |\n"
            "|---|---|---|---|---|---|---|\n"
        )
        lines = [header]
        for r in self.rows:
            vi_vd = f"VI: {', '.join(r.independent_variables) or 'N/A'}<br>VD: {', '.join(r.dependent_variables) or 'N/A'}"
            hyp = r.hypothesis or "N/A (Descriptivo/Cualitativo)"
            line = f"| {r.row_index} | {r.research_question} | {r.specific_objective} | {hyp} | {vi_vd} | {r.instrument or 'No especificado'} | {r.analysis_technique_or_test or 'No especificado'} |\n"
            lines.append(line)
        return "".join(lines)


class ConsistencyMatrixEngine:
    """Evaluates methodological alignment and checks statistical scale compatibility."""

    @classmethod
    def build_matrix(cls, project: ProjectStateDTO) -> ConsistencyMatrixReport:
        """Construct the consistency matrix and evaluate threats across the project."""
        rows: list[ConsistencyMatrixRow] = []
        alignment_issues: list[str] = []
        validity_threats: list[ValidityThreat] = []

        meth = project.methodology
        approach = meth.approach if meth and meth.approach else ResearchApproach.CUANTITATIVO

        # 1. Map Questions, Objectives, and Hypotheses
        specific_objs = project.specific_objectives or []
        questions = [project.research_question] if project.research_question else []
        hypotheses = [project.hypothesis] if project.hypothesis else []

        # Find variables
        op_vars = project.operationalized_variables or []
        vi_list = [v.name for v in op_vars if v.variable_type == VariableType.INDEPENDIENTE]
        vd_list = [v.name for v in op_vars if v.variable_type == VariableType.DEPENDIENTE]
        ctrl_list = [v.name for v in op_vars if v.variable_type == VariableType.CONTROL]

        instruments = meth.instruments if meth and meth.instruments else []
        instrument_summary = ", ".join(instruments) if instruments else "No especificado"
        analysis_tech = meth.analysis_technique if meth else "No especificado"

        # Match row count by specific objectives
        target_count = max(len(specific_objs), 1)
        for idx in range(target_count):
            obj = specific_objs[idx] if idx < len(specific_objs) else f"Objetivo específico {idx + 1} pendiente"
            q = questions[idx] if idx < len(questions) else (questions[0] if questions else "Pregunta no definida")
            h = hypotheses[idx] if idx < len(hypotheses) else (hypotheses[0] if hypotheses else None)

            # Check scale compatibility with test if quantitative
            is_compat = True
            compat_note = "Compatible"
            if approach == ResearchApproach.CUANTITATIVO and op_vars:
                is_compat, compat_note = cls.check_scale_compatibility(op_vars, analysis_tech)

            rows.append(
                ConsistencyMatrixRow(
                    row_index=idx + 1,
                    research_question=q,
                    specific_objective=obj,
                    hypothesis=h,
                    independent_variables=vi_list,
                    dependent_variables=vd_list,
                    control_variables=ctrl_list,
                    instrument=instrument_summary,
                    analysis_technique_or_test=analysis_tech,
                    is_scale_compatible=is_compat,
                    compatibility_note=compat_note,
                )
            )

        # 2. Evaluate Alignment Issues
        if not project.research_question:
            alignment_issues.append("Falta definir la pregunta de investigación principal.")
        if not specific_objs:
            alignment_issues.append("No se han formulado objetivos específicos.")
        elif len(specific_objs) < 2:
            alignment_issues.append("Se recomiendan al menos 2 objetivos específicos para dar cobertura al problema.")

        if approach == ResearchApproach.CUANTITATIVO:
            if not project.hypothesis and "correlacional" in (meth.design if meth else "").lower():
                alignment_issues.append("Un diseño correlacional o explicativo exige formular hipótesis contrastables.")
            if not op_vars:
                alignment_issues.append("Se requiere la matriz de operacionalización de variables para investigación cuantitativa.")

        # 3. Assess Validity Threats
        validity_threats = cls.audit_validity_threats(project)

        # 4. Calculate Score
        score = 100.0 - (len(alignment_issues) * 15.0) - (len(validity_threats) * 5.0)
        for r in rows:
            if not r.is_scale_compatible:
                score -= 10.0
        score = max(0.0, min(100.0, round(score, 1)))

        return ConsistencyMatrixReport(
            project_id=project.id,
            academic_level=project.academic_level.value,
            approach=approach,
            overall_alignment_score=score,
            rows=rows,
            validity_threats=validity_threats,
            alignment_issues=alignment_issues,
            is_fully_consistent=len(alignment_issues) == 0 and score >= 80.0,
        )

    @classmethod
    def check_scale_compatibility(
        cls,
        variables: list[VariableOperationalizationDTO],
        technique: str,
    ) -> tuple[bool, str]:
        """Verify if the measurement scales of the variables match the statistical test requirements."""
        if not technique or technique.strip().lower() in ("no especificado", "pendiente"):
            return True, "Técnica no declarada"

        tech_lower = technique.lower()
        for test_key, valid_scales in STATISTICAL_TEST_SCALE_MAP.items():
            if test_key in tech_lower or test_key.replace("_", " ") in tech_lower:
                for v in variables:
                    if v.measurement_scale not in valid_scales:
                        return False, (
                            f"Incompatibilidad: La prueba '{test_key}' requiere escalas {[s.value for s in valid_scales]}, "
                            f"pero la variable '{v.name}' tiene escala '{v.measurement_scale.value}'."
                        )
                return True, f"Compatible con prueba '{test_key}'."

        return True, "Técnica general compatible"

    @classmethod
    def audit_validity_threats(cls, project: ProjectStateDTO) -> list[ValidityThreat]:
        """Audit classical threats to internal, external, construct, and statistical validity."""
        threats: list[ValidityThreat] = []
        meth = project.methodology

        # Check 1: Selection bias / Non-probabilistic sampling
        if meth and meth.sampling_technique:
            st_val = meth.sampling_technique.value
            if "no_probabilistico" in st_val:
                threats.append(
                    ValidityThreat(
                        domain="external",
                        name="Sesgo de Muestreo No Probabilístico",
                        description=f"El muestreo ({st_val}) restringe la generalización poblacional de los hallazgos.",
                        mitigation_strategy="Declare explícitamente el alcance contextual y evite extrapolaciones universales.",
                    )
                )

        # Check 2: Attrition threat in longitudinal studies
        if meth and meth.temporal_scope and "longitudinal" in meth.temporal_scope.lower():
            threats.append(
                ValidityThreat(
                    domain="internal",
                    name="Mortalidad Experimental / Atrición",
                    description="Los estudios longitudinales sufren pérdida de participantes a lo largo del tiempo.",
                    mitigation_strategy="Planifique un sobremuestreo inicial del 15-20% y análisis de sesgo de abandono.",
                )
            )

        # Check 3: Construct under-representation
        if project.operationalized_variables:
            for v in project.operationalized_variables:
                if not v.indicators or len(v.indicators) < 2:
                    threats.append(
                        ValidityThreat(
                            domain="construct",
                            name=f"Sub-representación del Constructo ('{v.name}')",
                            description="La variable tiene menos de 2 indicadores, lo que arriesga medición incompleta.",
                            mitigation_strategy="Agregue al menos 2-3 indicadores empíricos por dimensión.",
                        )
                    )

        return threats
