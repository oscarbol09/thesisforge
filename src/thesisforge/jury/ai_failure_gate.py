"""7 AI Failure Modes Academic Audit Gate.

Defends academic projects against the failure modes identified in autonomous scientific AI
(Lu et al., 2026; Zhao et al., 2026), including bug-as-insight reframing, ghost citations,
sample overgeneralization, epistemic frame-lock, survivorship bias, and proxy fallacies.
"""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from thesisforge.core.time import utc_now
from thesisforge.models import AuditSeverity, ProjectStateDTO, ResearchApproach


class AIFailureMode(StrEnum):
    """Taxonomy of the 7 Critical AI Failure Modes in Academic Research."""

    BUG_AS_INSIGHT = "bug_as_insight"
    LITERATURE_FABRICATION = "literature_fabrication"
    SAMPLE_OVERGENERALIZATION = "sample_overgeneralization"
    EPISTEMIC_FRAME_LOCK = "epistemic_frame_lock"
    SURVIVORSHIP_BIAS = "survivorship_bias"
    PROXY_FALLACY = "proxy_fallacy"
    HEDGING_FOG = "hedging_fog"


class FailureFinding(BaseModel):
    """Diagnostic record of an identified AI failure risk."""

    model_config = ConfigDict(extra="ignore")

    mode: AIFailureMode
    severity: AuditSeverity
    chapter_or_field: str
    summary: str
    detailed_evidence: str
    mitigation_strategy: str


class AIFailureGateReport(BaseModel):
    """Consolidated audit report from the 7 AI Failure Modes Gate."""

    model_config = ConfigDict(extra="ignore")

    passed: bool
    risk_score: float = Field(
        ge=0.0, le=100.0, description="Failure risk score (0=clean, 100=extreme risk)"
    )
    evaluated_modes_count: int = 7
    findings: list[FailureFinding] = Field(default_factory=list)
    passed_modes: list[AIFailureMode] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class AIFailureGateAuditor:
    """Scientific auditor executing defensive heuristics across project state."""

    @classmethod
    def audit_project(cls, project: ProjectStateDTO) -> AIFailureGateReport:
        """Run systematic verification for all 7 AI Failure Modes on a project."""
        findings: list[FailureFinding] = []
        passed_modes: list[AIFailureMode] = []

        # 1. Check Mode 1: BUG_AS_INSIGHT
        f1 = cls._audit_bug_as_insight(project)
        if f1:
            findings.extend(f1)
        else:
            passed_modes.append(AIFailureMode.BUG_AS_INSIGHT)

        # 2. Check Mode 2: LITERATURE_FABRICATION
        f2 = cls._audit_literature_fabrication(project)
        if f2:
            findings.extend(f2)
        else:
            passed_modes.append(AIFailureMode.LITERATURE_FABRICATION)

        # 3. Check Mode 3: SAMPLE_OVERGENERALIZATION
        f3 = cls._audit_sample_overgeneralization(project)
        if f3:
            findings.extend(f3)
        else:
            passed_modes.append(AIFailureMode.SAMPLE_OVERGENERALIZATION)

        # 4. Check Mode 4: EPISTEMIC_FRAME_LOCK
        f4 = cls._audit_epistemic_frame_lock(project)
        if f4:
            findings.extend(f4)
        else:
            passed_modes.append(AIFailureMode.EPISTEMIC_FRAME_LOCK)

        # 5. Check Mode 5: SURVIVORSHIP_BIAS
        f5 = cls._audit_survivorship_bias(project)
        if f5:
            findings.extend(f5)
        else:
            passed_modes.append(AIFailureMode.SURVIVORSHIP_BIAS)

        # 6. Check Mode 6: PROXY_FALLACY
        f6 = cls._audit_proxy_fallacy(project)
        if f6:
            findings.extend(f6)
        else:
            passed_modes.append(AIFailureMode.PROXY_FALLACY)

        # 7. Check Mode 7: HEDGING_FOG
        f7 = cls._audit_hedging_fog(project)
        if f7:
            findings.extend(f7)
        else:
            passed_modes.append(AIFailureMode.HEDGING_FOG)

        # Calculate risk score (0 to 100)
        penalty = 0.0
        has_critical = False
        for f in findings:
            if f.severity == AuditSeverity.CRITICAL:
                penalty += 35.0
                has_critical = True
            elif f.severity == AuditSeverity.MAJOR:
                penalty += 20.0
            elif f.severity == AuditSeverity.MINOR:
                penalty += 10.0
            else:
                penalty += 4.0

        risk_score = min(100.0, round(penalty, 1))
        passed = (risk_score < 40.0) and not has_critical

        return AIFailureGateReport(
            passed=passed,
            risk_score=risk_score,
            findings=findings,
            passed_modes=passed_modes,
        )

    @classmethod
    def _audit_bug_as_insight(cls, project: ProjectStateDTO) -> list[FailureFinding]:
        """Detect language reframing anomalies, null outliers, or pipeline artifacts as profound discoveries."""
        findings: list[FailureFinding] = []
        suspicious_terms = [
            r"\banomalía reveladora\b",
            r"\bcomportamiento inesperado que demuestra\b",
            r"\bhallazgo accidental que redefine\b",
            r"\berror de medición que sugiere\b",
        ]
        all_text = f"{project.justification} {project.research_problem}"
        for sec in project.sections:
            all_text += f" {sec.content}"

        for pattern in suspicious_terms:
            if re.search(pattern, all_text, re.IGNORECASE):
                findings.append(
                    FailureFinding(
                        mode=AIFailureMode.BUG_AS_INSIGHT,
                        severity=AuditSeverity.MAJOR,
                        chapter_or_field="Contenido General",
                        summary="Posible reinterpretación de anomalía o artefacto metodológico como insight.",
                        detailed_evidence=f"Patrón detectado coincidente con '{pattern}'.",
                        mitigation_strategy="Verificar si la anomalía es un artefacto técnico/de medición antes de atribuirle valor teórico.",
                    )
                )
                break
        return findings

    @classmethod
    def _audit_literature_fabrication(cls, project: ProjectStateDTO) -> list[FailureFinding]:
        """Check for ungrounded citations in sections not present in validated literature registry."""
        findings: list[FailureFinding] = []
        known_authors = {
            author.lower() for cit in project.validated_citations for author in cit.authors
        }
        all_content = " ".join(s.content for s in project.sections if s.content)

        # Look for explicit (Author, Year) in text
        in_text_authors = re.findall(
            r"\(([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)(?:\s+et\s+al\.)?,\s*\d{4}\)", all_content
        )
        unmatched_authors = [
            a for a in in_text_authors if known_authors and a.lower() not in known_authors
        ]
        if in_text_authors and not project.validated_citations:
            findings.append(
                FailureFinding(
                    mode=AIFailureMode.LITERATURE_FABRICATION,
                    severity=AuditSeverity.CRITICAL,
                    chapter_or_field="Citas y Referencias",
                    summary="Citas en el texto sin bibliografía validada en el proyecto.",
                    detailed_evidence=f"Se detectaron {len(in_text_authors)} citas textuales sin respaldo en 'validated_citations'.",
                    mitigation_strategy="Indexe las fuentes primarias en el módulo RAG y valide los DOIs con CrossRef/Semantic Scholar.",
                )
            )
        elif unmatched_authors:
            findings.append(
                FailureFinding(
                    mode=AIFailureMode.LITERATURE_FABRICATION,
                    severity=AuditSeverity.MAJOR,
                    chapter_or_field="Citas y Referencias",
                    summary="Citas en el texto que no coinciden con los autores indexados.",
                    detailed_evidence=f"Autores citados no encontrados en la base indexada: {', '.join(unmatched_authors[:3])}.",
                    mitigation_strategy="Verifique que todas las citas del texto provengan de artículos registrados en el repositorio bibliográfico.",
                )
            )
        return findings

    @classmethod
    def _audit_sample_overgeneralization(cls, project: ProjectStateDTO) -> list[FailureFinding]:
        """Check for small sample sizes making universal or causal claims."""
        findings: list[FailureFinding] = []
        meth = project.methodology
        if not meth:
            return findings

        # Check sample size keywords
        sample_str = (meth.sample or "").lower()
        numbers = re.findall(r"\b\d+\b", sample_str)
        if numbers:
            sample_size = int(numbers[0])
            # If sample size is under 30 in a quantitative study with causal claims
            if (
                meth.approach == ResearchApproach.CUANTITATIVO
                and sample_size < 30
                and "causal" in (meth.design or "").lower()
            ):
                findings.append(
                    FailureFinding(
                        mode=AIFailureMode.SAMPLE_OVERGENERALIZATION,
                        severity=AuditSeverity.MAJOR,
                        chapter_or_field="Metodología (Muestra)",
                        summary="Muestra reducida para inferencias explicativo-causales.",
                        detailed_evidence=f"Tamaño muestral indicado ({sample_size}) es insuficiente para potencia estadística causal sin justificación previa.",
                        mitigation_strategy="Amplíe la muestra o restrinja el alcance a un estudio exploratorio/piloto.",
                    )
                )
        return findings

    @classmethod
    def _audit_epistemic_frame_lock(cls, project: ProjectStateDTO) -> list[FailureFinding]:
        """Verify that the project explicitly discusses limitations and boundary conditions."""
        findings: list[FailureFinding] = []
        has_scope_lim = bool(
            project.scope_limitations and len(project.scope_limitations.strip()) >= 50
        )
        if not has_scope_lim:
            findings.append(
                FailureFinding(
                    mode=AIFailureMode.EPISTEMIC_FRAME_LOCK,
                    severity=AuditSeverity.MAJOR,
                    chapter_or_field="Alcance y Limitaciones",
                    summary="Ausencia de delimitación explícita de limitaciones del estudio.",
                    detailed_evidence="El campo 'scope_limitations' está vacío o es inferior a 50 caracteres.",
                    mitigation_strategy="Declare explícitamente las condiciones de borde, sesgos potenciales y amenazas a la validez.",
                )
            )
        return findings

    @classmethod
    def _audit_survivorship_bias(cls, project: ProjectStateDTO) -> list[FailureFinding]:
        """Verify inclusion/exclusion criteria transparency to avoid survivorship/selection bias."""
        findings: list[FailureFinding] = []
        meth = project.methodology
        if (
            meth
            and meth.approach in (ResearchApproach.CUANTITATIVO, ResearchApproach.MIXTO)
            and (not meth.inclusion_criteria or not meth.exclusion_criteria)
        ):
            findings.append(
                FailureFinding(
                    mode=AIFailureMode.SURVIVORSHIP_BIAS,
                    severity=AuditSeverity.MINOR,
                    chapter_or_field="Metodología (Criterios)",
                    summary="Falta de criterios explícitos de inclusión y exclusión de participantes/casos.",
                    detailed_evidence="No se definieron 'inclusion_criteria' o 'exclusion_criteria' formales.",
                    mitigation_strategy="Establezca criterios rigurosos de inclusión/exclusión para prevenir sesgos de selección.",
                )
            )
        return findings

    @classmethod
    def _audit_proxy_fallacy(cls, project: ProjectStateDTO) -> list[FailureFinding]:
        """Check if quantitative variables have clear operational dimensions/indicators."""
        findings: list[FailureFinding] = []
        if (
            project.methodology
            and project.methodology.approach == ResearchApproach.CUANTITATIVO
            and project.variables
            and not project.operationalized_variables
        ):
            findings.append(
                FailureFinding(
                    mode=AIFailureMode.PROXY_FALLACY,
                    severity=AuditSeverity.MAJOR,
                    chapter_or_field="Variables",
                    summary="Variables declaradas sin matriz de operacionalización.",
                    detailed_evidence=f"Se listan {len(project.variables)} variables pero ninguna tiene dimensiones o indicadores definidos.",
                    mitigation_strategy="Complete la matriz de operacionalización indicando dimensiones, escala de medición e instrumentos.",
                )
            )
        return findings

    @classmethod
    def _audit_hedging_fog(cls, project: ProjectStateDTO) -> list[FailureFinding]:
        """Check if problem formulation is excessively vague or hedging-heavy."""
        findings: list[FailureFinding] = []
        problem = project.research_problem or ""
        hedges = re.findall(
            r"\b(?:quizás|tal vez|posiblemente|se podría suponer|podría ser que|en cierta medida)\b",
            problem,
            re.IGNORECASE,
        )
        if len(hedges) >= 4:
            findings.append(
                FailureFinding(
                    mode=AIFailureMode.HEDGING_FOG,
                    severity=AuditSeverity.MINOR,
                    chapter_or_field="Planteamiento del Problema",
                    summary="Densidad excesiva de lenguaje evasivo/condicional en el planteamiento.",
                    detailed_evidence=f"Se detectaron {len(hedges)} expresiones de duda o atenuación excesiva.",
                    mitigation_strategy="Sustituya afirmaciones especulativas por datos fácticos y preguntas de investigación directas.",
                )
            )
        return findings
