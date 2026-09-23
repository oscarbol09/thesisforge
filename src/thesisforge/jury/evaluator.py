import unicodedata
import uuid
from typing import Any

from thesisforge.core.logging import get_logger
from thesisforge.core.time import utc_now
from thesisforge.llm.prompts import JURY_PANEL_AUDIT_PROMPT
from thesisforge.llm.router import LLMRouter
from thesisforge.models import (
    AuditIssueDTO,
    AuditIssueType,
    AuditSeverity,
    JurorDimensionScoreDTO,
    JurorRole,
    JuryEvaluationReportDTO,
    JuryVerdict,
    ProjectStateDTO,
    ResearchApproach,
    SectionStatus,
)

logger = get_logger(__name__)

JUROR_DEFAULTS: dict[JurorRole, tuple[str, str]] = {
    JurorRole.METODOLOGO: (
        "Dr. Arístides Valenzuela",
        "Consistencia Metodológica y Epistemológica",
    ),
    JurorRole.ESPECIALISTA_TEMATICO: (
        "Dra. Beatriz Salamanca",
        "Estado del Arte y Sustento Teórico",
    ),
    JurorRole.AUDITOR_ESTADISTICO: (
        "Dr. Camilo Restrepo",
        "Rigor Empírico, Muestreo e Instrumentos",
    ),
    JurorRole.ABOGADO_DEL_DIABLO: (
        "Dr. Demetrio Sotomayor",
        "Resiliencia Crítica y Amenazas a la Validez",
    ),
}


def normalize_juror_role(raw_role: str | JurorRole) -> JurorRole:
    """Normalize raw juror role strings (with or without accents/variations) into canonical JurorRole."""
    if isinstance(raw_role, JurorRole):
        return raw_role

    text = (
        unicodedata.normalize("NFKD", str(raw_role))
        .encode("ASCII", "ignore")
        .decode("utf-8")
        .lower()
        .strip()
    )
    if any(k in text for k in ["metodolog", "methodolog"]):
        return JurorRole.METODOLOGO
    if any(k in text for k in ["tematic", "thematic", "especialista", "expert"]):
        return JurorRole.ESPECIALISTA_TEMATICO
    if any(k in text for k in ["estadist", "statistic", "auditor", "cuantitativ"]):
        return JurorRole.AUDITOR_ESTADISTICO
    if any(k in text for k in ["diablo", "devil", "critico", "adversar", "advocate"]):
        return JurorRole.ABOGADO_DEL_DIABLO

    for role in JurorRole:
        if role.value in text:
            return role
    return JurorRole.METODOLOGO


class MultiAgentJuryEngine:
    """Orchestrator for the 4-juror scientific evaluation panel and automated thesis audit."""

    def __init__(self, llm_router: LLMRouter | None = None) -> None:
        self.llm = llm_router

    def _determine_verdict(self, overall_score: float, issues: list[AuditIssueDTO]) -> JuryVerdict:
        """Calculate formal verdict based on numerical score and critical defect constraints."""
        has_critical = any(issue.severity == AuditSeverity.CRITICAL for issue in issues)
        has_multiple_major = (
            sum(1 for issue in issues if issue.severity == AuditSeverity.MAJOR) >= 3
        )

        if has_critical or overall_score < 50.0:
            return JuryVerdict.NO_APROBADO
        if has_multiple_major or overall_score < 70.0:
            return JuryVerdict.MODIFICACIONES_MAYORES
        if overall_score < 80.0:
            return JuryVerdict.MODIFICACIONES_MENORES
        if overall_score >= 95.0:
            return JuryVerdict.APROBADO_CON_DISTINCION
        return JuryVerdict.APROBADO

    def _run_rule_based_audit(self, project: ProjectStateDTO) -> list[AuditIssueDTO]:
        """Execute deterministic rule checks against the project state."""
        issues: list[AuditIssueDTO] = []

        # 1. Verification of problem formulation completeness
        if not project.research_problem or len(project.research_problem.strip()) < 50:
            issues.append(
                AuditIssueDTO(
                    id=uuid.uuid4().hex[:10],
                    issue_type=AuditIssueType.METHODOLOGICAL_INCONSISTENCY,
                    severity=AuditSeverity.CRITICAL,
                    chapter_or_section="Capítulo 1: Planteamiento del Problema",
                    title="Planteamiento del problema ausente o insuficiente",
                    description="El proyecto no cuenta con un planteamiento del problema delimitado y formalizado.",
                    recommendation="Completar la fase de asesoría metodológica formalizando el problema con datos empíricos.",
                )
            )

        if not project.research_question:
            issues.append(
                AuditIssueDTO(
                    id=uuid.uuid4().hex[:10],
                    issue_type=AuditIssueType.METHODOLOGICAL_INCONSISTENCY,
                    severity=AuditSeverity.CRITICAL,
                    chapter_or_section="Capítulo 1: Pregunta de Investigación",
                    title="Pregunta de investigación principal no definida",
                    description="No se ha formulado una pregunta rectora para guiar la investigación.",
                    recommendation="Redactar la pregunta general en términos precisos de variables y contexto.",
                )
            )

        if not project.general_objective:
            issues.append(
                AuditIssueDTO(
                    id=uuid.uuid4().hex[:10],
                    issue_type=AuditIssueType.METHODOLOGICAL_INCONSISTENCY,
                    severity=AuditSeverity.CRITICAL,
                    chapter_or_section="Capítulo 1: Objetivos",
                    title="Objetivo general ausente",
                    description="El proyecto carece de un objetivo general que determine el alcance del estudio.",
                    recommendation="Definir el objetivo general iniciando con un verbo en infinitivo adecuado.",
                )
            )

        # 2. Hypothesis consistency in quantitative research
        approach = project.methodology.approach if project.methodology else None
        design_str = (project.methodology.design if project.methodology else "").lower()
        if approach == ResearchApproach.CUANTITATIVO:
            is_correlational_or_causal = any(
                term in design_str
                for term in ["correlacional", "causal", "experimental", "explicativo"]
            )
            if is_correlational_or_causal and not project.hypothesis:
                issues.append(
                    AuditIssueDTO(
                        id=uuid.uuid4().hex[:10],
                        issue_type=AuditIssueType.METHODOLOGICAL_INCONSISTENCY,
                        severity=AuditSeverity.MAJOR,
                        chapter_or_section="Capítulo 1: Hipótesis",
                        title="Ausencia de hipótesis en diseño cuantitativo explicativo/correlacional",
                        description=(
                            "El diseño declarado requiere contrastación estadística formal, pero no se ha formulado hipótesis."
                        ),
                        recommendation="Formular una hipótesis nula y alternativa claramente contrastables.",
                    )
                )

        # 3. Literature citation volume & grounding
        citation_count = len(project.validated_citations)
        if citation_count == 0:
            issues.append(
                AuditIssueDTO(
                    id=uuid.uuid4().hex[:10],
                    issue_type=AuditIssueType.UNSUPPORTED_CLAIM,
                    severity=AuditSeverity.CRITICAL,
                    chapter_or_section="Capítulo 2: Marco Teórico",
                    title="Cero literatura científica indexada en RAG",
                    description="El proyecto no tiene fuentes académicas validadas ni artículos indexados para sustentar el estado del arte.",
                    recommendation="Realizar búsquedas bibliográficas en Semantic Scholar/CrossRef e indexar al menos 5 artículos relevantes.",
                )
            )
        elif citation_count < 3:
            issues.append(
                AuditIssueDTO(
                    id=uuid.uuid4().hex[:10],
                    issue_type=AuditIssueType.UNSUPPORTED_CLAIM,
                    severity=AuditSeverity.MAJOR,
                    chapter_or_section="Capítulo 2: Marco Teórico",
                    title="Cuerpo bibliográfico insuficiente",
                    description=f"Se han validado únicamente {citation_count} fuentes, lo cual es escaso para una tesis de nivel {project.academic_level.value}.",
                    recommendation="Ampliar la base bibliográfica indexando al menos 5 artículos arbitrados adicionales.",
                )
            )

        # 4. Drafted sections progress & substance
        approved_sections = [s for s in project.sections if s.status == SectionStatus.APPROVED]
        total_sections = len(project.sections)

        if total_sections > 0 and len(approved_sections) == 0:
            issues.append(
                AuditIssueDTO(
                    id=uuid.uuid4().hex[:10],
                    issue_type=AuditIssueType.MISSING_LIMITATIONS,
                    severity=AuditSeverity.MAJOR,
                    chapter_or_section="Redacción General",
                    title="Capítulos sin aprobar en borrador",
                    description="Se han inicializado las secciones pero ninguna ha sido aprobada formalmente.",
                    recommendation="Completar la redacción y revisión de los capítulos antes del dictamen final.",
                )
            )

        return issues

    def _build_rule_based_scores(
        self, project: ProjectStateDTO, issues: list[AuditIssueDTO]
    ) -> tuple[float, list[JurorDimensionScoreDTO], list[str], list[str]]:
        """Calculate fallback scores and structured feedback using deterministic rules."""
        # Calculate base scores
        methodology_score = 100.0
        literature_score = 100.0
        empirical_score = 100.0
        critical_score = 100.0

        for issue in issues:
            penalty = (
                25.0
                if issue.severity == AuditSeverity.CRITICAL
                else (15.0 if issue.severity == AuditSeverity.MAJOR else 5.0)
            )
            if issue.issue_type == AuditIssueType.METHODOLOGICAL_INCONSISTENCY:
                methodology_score = max(20.0, methodology_score - penalty)
                critical_score = max(30.0, critical_score - (penalty * 0.5))
            elif issue.issue_type == AuditIssueType.UNSUPPORTED_CLAIM:
                literature_score = max(20.0, literature_score - penalty)
            elif issue.issue_type in (
                AuditIssueType.SAMPLING_BIAS,
                AuditIssueType.INVALID_INSTRUMENT,
            ):
                empirical_score = max(20.0, empirical_score - penalty)
            else:
                critical_score = max(20.0, critical_score - penalty)

        # Check sections volume bonus/penalty
        approved_count = sum(1 for s in project.sections if s.status == SectionStatus.APPROVED)
        if len(project.sections) > 0:
            ratio = approved_count / len(project.sections)
            if ratio < 0.5:
                methodology_score = max(20.0, methodology_score - 15.0)
                literature_score = max(20.0, literature_score - 15.0)

        # Build juror scores
        juror_evaluations: list[JurorDimensionScoreDTO] = [
            JurorDimensionScoreDTO(
                juror_role=JurorRole.METODOLOGO,
                juror_name="Dr. Arístides Valenzuela",
                dimension_name="Consistencia Metodológica y Epistemológica",
                score=round(methodology_score, 1),
                criteria_evaluation="Auditoría de correspondencia entre el problema, objetivos específicos y diseño seleccionado.",
                feedback=(
                    "El proyecto presenta congruencia en su diseño general."
                    if methodology_score >= 80.0
                    else "Se detectaron incongruencias entre la pregunta rectora y la operacionalización metodológica."
                ),
                strengths=["Objetivo general adecuadamente delimitado"]
                if project.general_objective
                else [],
                flaws=[
                    i.description
                    for i in issues
                    if i.issue_type == AuditIssueType.METHODOLOGICAL_INCONSISTENCY
                ],
            ),
            JurorDimensionScoreDTO(
                juror_role=JurorRole.ESPECIALISTA_TEMATICO,
                juror_name="Dra. Beatriz Salamanca",
                dimension_name="Estado del Arte y Sustento Teórico",
                score=round(literature_score, 1),
                criteria_evaluation="Suficiencia y rigor de la literatura académica verificada para fundamentar el marco conceptual.",
                feedback=(
                    f"Se dispone de un cuerpo bibliográfico indexado con {len(project.validated_citations)} fuentes verificadas."
                    if literature_score >= 80.0
                    else "La cobertura bibliográfica es insuficiente para sustentar la discusión teórica del problema."
                ),
                strengths=[f"{len(project.validated_citations)} fuentes verificadas"]
                if len(project.validated_citations) >= 3
                else [],
                flaws=[
                    i.description
                    for i in issues
                    if i.issue_type == AuditIssueType.UNSUPPORTED_CLAIM
                ],
            ),
            JurorDimensionScoreDTO(
                juror_role=JurorRole.AUDITOR_ESTADISTICO,
                juror_name="Dr. Camilo Restrepo",
                dimension_name="Rigor Empírico, Muestreo e Instrumentos",
                score=round(empirical_score, 1),
                criteria_evaluation="Evaluación de la representatividad muestral, técnicas de recolección y validez de instrumentos.",
                feedback=(
                    "La delimitación poblacional e instrumental se encuentra descrita adecuadamente."
                    if empirical_score >= 80.0
                    else "Falta precisión en el tamaño muestral o justificación de las técnicas de análisis."
                ),
                strengths=["Población delimitada"]
                if project.methodology and project.methodology.population
                else [],
                flaws=[
                    i.description
                    for i in issues
                    if i.issue_type
                    in (AuditIssueType.SAMPLING_BIAS, AuditIssueType.INVALID_INSTRUMENT)
                ],
            ),
            JurorDimensionScoreDTO(
                juror_role=JurorRole.ABOGADO_DEL_DIABLO,
                juror_name="Dr. Demetrio Sotomayor",
                dimension_name="Resiliencia Crítica y Amenazas a la Validez",
                score=round(critical_score, 1),
                criteria_evaluation="Análisis de supuestos no declarados, sesgos de confirmación y limitaciones epistemológicas.",
                feedback=(
                    "El trabajo delimita sus alcances con honestidad científica."
                    if critical_score >= 80.0
                    else "Existen supuestos no justificados que comprometen la solidez de las conclusiones."
                ),
                strengths=["Alcance especificado"] if project.scope_limitations else [],
                flaws=[
                    i.description
                    for i in issues
                    if i.issue_type == AuditIssueType.MISSING_LIMITATIONS
                ],
            ),
        ]

        overall_score = round(
            (methodology_score * 0.35)
            + (literature_score * 0.25)
            + (empirical_score * 0.25)
            + (critical_score * 0.15),
            1,
        )

        mandatory_fixes = [
            issue.recommendation
            for issue in issues
            if issue.severity in (AuditSeverity.CRITICAL, AuditSeverity.MAJOR)
        ]
        recommended_improvements = [
            issue.recommendation
            for issue in issues
            if issue.severity in (AuditSeverity.MINOR, AuditSeverity.NOTE)
        ]

        return overall_score, juror_evaluations, mandatory_fixes, recommended_improvements

    async def evaluate_project(self, project: ProjectStateDTO) -> JuryEvaluationReportDTO:
        """Perform full multi-agent jury evaluation combining deterministic checks with LLM inference."""
        rule_issues = self._run_rule_based_audit(project)

        if not self.llm:
            # Fallback to deterministic rule engine
            overall_score, juror_evals, mandatory, recommended = self._build_rule_based_scores(
                project, rule_issues
            )
            verdict = self._determine_verdict(overall_score, rule_issues)
            summary_dictamen = (
                f"El Tribunal Académico ha emitido un dictamen de '{verdict.value.upper()}' con una calificación global de {overall_score}/100. "
                f"Se identificaron {len(rule_issues)} observaciones metodológicas y estructurales."
            )
            return JuryEvaluationReportDTO(
                id=uuid.uuid4().hex[:12],
                project_id=project.id,
                overall_score=overall_score,
                verdict=verdict,
                summary_dictamen=summary_dictamen,
                juror_evaluations=juror_evals,
                issues=rule_issues,
                mandatory_fixes=mandatory,
                recommended_improvements=recommended,
                created_at=utc_now(),
            )

        # Build prompt variables for LLM Multi-Agent Tribunal
        drafted_sections_summary = (
            "\n".join(
                f"- [{s.section_id}] {s.title} (Estado: {s.status.value}, Palabras: {s.word_count}): {s.summary or s.content[:200] + '...'}"
                for s in project.sections
            )
            or "No se han redactado secciones aún."
        )

        citations_summary = (
            "\n".join(
                f"- {c.apa_formatted or c.title} ({c.year})"
                for c in project.validated_citations[:10]
            )
            or "Sin literatura validada."
        )

        prompt = JURY_PANEL_AUDIT_PROMPT.format(
            title=project.title or "Sin título",
            academic_level=project.academic_level.value,
            area_of_study=project.area_of_study or "No especificada",
            research_problem=project.research_problem or "No especificado",
            research_question=project.research_question or "No especificada",
            general_objective=project.general_objective or "No especificado",
            specific_objectives="; ".join(project.specific_objectives) or "Ninguno",
            hypothesis=project.hypothesis or "No formulada",
            approach=project.methodology.approach.value
            if project.methodology and project.methodology.approach
            else "No definido",
            design=project.methodology.design if project.methodology else "No definido",
            population=project.methodology.population if project.methodology else "No definida",
            sample=project.methodology.sample if project.methodology else "No definida",
            instruments=", ".join(project.methodology.instruments)
            if project.methodology
            else "Ninguno",
            analysis_technique=project.methodology.analysis_technique
            if project.methodology
            else "No especificada",
            drafted_sections_summary=drafted_sections_summary,
            citation_count=len(project.validated_citations),
            citations_summary=citations_summary,
        )

        try:
            parsed_json = await self.llm.complete_json(prompt=prompt, system_prompt="")
            return self._build_report_from_llm_response(project.id, parsed_json, rule_issues)
        except Exception as exc:
            logger.warning(
                "LLM jury panel audit encountered an issue; falling back to rule-based evaluation.",
                extra={"error": str(exc), "project_id": project.id},
            )
            overall_score, juror_evals, mandatory, recommended = self._build_rule_based_scores(
                project, rule_issues
            )
            verdict = self._determine_verdict(overall_score, rule_issues)
            summary_dictamen = (
                f"El Tribunal Académico ha emitido un dictamen de '{verdict.value.upper()}' con una calificación global de {overall_score}/100. "
                f"Se detectaron {len(rule_issues)} observaciones prioritarias."
            )
            return JuryEvaluationReportDTO(
                id=uuid.uuid4().hex[:12],
                project_id=project.id,
                overall_score=overall_score,
                verdict=verdict,
                summary_dictamen=summary_dictamen,
                juror_evaluations=juror_evals,
                issues=rule_issues,
                mandatory_fixes=mandatory,
                recommended_improvements=recommended,
                created_at=utc_now(),
            )

    def _build_report_from_llm_response(
        self,
        project_id: str,
        data: dict[str, Any],
        rule_issues: list[AuditIssueDTO],
    ) -> JuryEvaluationReportDTO:
        """Parse structured LLM JSON and merge with deterministic rule-based issues."""
        llm_issues: list[AuditIssueDTO] = []
        for raw_issue in data.get("issues", []):
            try:
                issue_type_str = str(
                    raw_issue.get("issue_type", "methodological_inconsistency")
                ).lower()
                valid_types = {t.value: t for t in AuditIssueType}
                issue_type = valid_types.get(
                    issue_type_str, AuditIssueType.METHODOLOGICAL_INCONSISTENCY
                )

                severity_str = str(raw_issue.get("severity", "major")).lower()
                valid_sevs = {s.value: s for s in AuditSeverity}
                severity = valid_sevs.get(severity_str, AuditSeverity.MAJOR)

                llm_issues.append(
                    AuditIssueDTO(
                        id=uuid.uuid4().hex[:10],
                        issue_type=issue_type,
                        severity=severity,
                        chapter_or_section=str(raw_issue.get("chapter_or_section", "General")),
                        title=str(raw_issue.get("title", "Observación del tribunal")),
                        description=str(raw_issue.get("description", "")),
                        quote_or_passage=raw_issue.get("quote_or_passage"),
                        recommendation=str(raw_issue.get("recommendation", "Revisar y corregir.")),
                    )
                )
            except Exception as err:
                logger.debug("Skipping malformed LLM audit issue item.", extra={"error": str(err)})
                continue

        # Merge unique issues (rule issues prioritized)
        combined_issues = list(rule_issues)
        for issue in llm_issues:
            if not any(
                existing.title.lower() == issue.title.lower() for existing in combined_issues
            ):
                combined_issues.append(issue)

        # Parse juror dimension scores
        juror_evaluations: list[JurorDimensionScoreDTO] = []
        for raw_eval in data.get("juror_evaluations", []):
            try:
                raw_role = str(raw_eval.get("juror_role", ""))
                role_enum = normalize_juror_role(raw_role)
                default_name, default_dim = JUROR_DEFAULTS[role_enum]

                score_val = float(raw_eval.get("score", 75.0))
                score_val = max(0.0, min(100.0, score_val))

                juror_evaluations.append(
                    JurorDimensionScoreDTO(
                        juror_role=role_enum,
                        juror_name=str(raw_eval.get("juror_name") or default_name),
                        dimension_name=str(raw_eval.get("dimension_name") or default_dim),
                        score=round(score_val, 1),
                        criteria_evaluation=str(raw_eval.get("criteria_evaluation", "")),
                        feedback=str(raw_eval.get("feedback", "")),
                        strengths=[str(s) for s in raw_eval.get("strengths", [])],
                        flaws=[str(f) for f in raw_eval.get("flaws", [])],
                    )
                )
            except Exception as err:
                logger.debug("Skipping malformed LLM juror eval item.", extra={"error": str(err)})
                continue

        # If LLM didn't return all 4 jurors, ensure complete 4-juror panel
        for role_enum, (default_name, default_dim) in JUROR_DEFAULTS.items():
            if not any(je.juror_role == role_enum for je in juror_evaluations):
                juror_evaluations.append(
                    JurorDimensionScoreDTO(
                        juror_role=role_enum,
                        juror_name=default_name,
                        dimension_name=default_dim,
                        score=75.0,
                        criteria_evaluation="Evaluación estándar completada.",
                        feedback="El jurado evaluador no emitió objeciones críticas adicionales.",
                        strengths=[],
                        flaws=[],
                    )
                )

        # Calculate weighted overall score
        raw_overall = float(data.get("overall_score", 0.0))
        if raw_overall <= 0.0 and juror_evaluations:
            raw_overall = sum(je.score for je in juror_evaluations) / len(juror_evaluations)
        overall_score = round(max(0.0, min(100.0, raw_overall)), 1)

        verdict = self._determine_verdict(overall_score, combined_issues)
        summary_dictamen = str(
            data.get(
                "summary_dictamen",
                f"El Tribunal Académico emite dictamen de '{verdict.value.upper()}' con calificación de {overall_score}/100.",
            )
        )

        mandatory_fixes = [str(m) for m in data.get("mandatory_fixes", [])] or [
            issue.recommendation
            for issue in combined_issues
            if issue.severity in (AuditSeverity.CRITICAL, AuditSeverity.MAJOR)
        ]
        recommended_improvements = [str(r) for r in data.get("recommended_improvements", [])] or [
            issue.recommendation
            for issue in combined_issues
            if issue.severity in (AuditSeverity.MINOR, AuditSeverity.NOTE)
        ]

        return JuryEvaluationReportDTO(
            id=uuid.uuid4().hex[:12],
            project_id=project_id,
            overall_score=overall_score,
            verdict=verdict,
            summary_dictamen=summary_dictamen,
            juror_evaluations=juror_evaluations,
            issues=combined_issues,
            mandatory_fixes=mandatory_fixes,
            recommended_improvements=recommended_improvements,
            created_at=utc_now(),
        )
