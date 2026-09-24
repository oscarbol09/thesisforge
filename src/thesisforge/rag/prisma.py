"""PRISMA 2020 Systematic Literature Review Flow Generator and Protocol Tracker.

Complies with the PRISMA 2020 statement (Page et al., 2021) for transparent,
reproducible, and audit-ready academic literature retrieval pipelines.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from thesisforge.core.time import utc_now


class PRISMAIdentificationPhase(BaseModel):
    """PRISMA 2020 Stage 1: Identification of academic records."""

    model_config = ConfigDict(extra="ignore")

    database_counts: dict[str, int] = Field(default_factory=dict)
    register_counts: dict[str, int] = Field(default_factory=dict)
    total_records_identified: int = Field(default=0, ge=0)
    duplicate_records_removed: int = Field(default=0, ge=0)
    records_marked_ineligible_automation: int = Field(default=0, ge=0)
    records_removed_other_reasons: int = Field(default=0, ge=0)


class PRISMAScreeningPhase(BaseModel):
    """PRISMA 2020 Stage 2: Title and abstract screening."""

    model_config = ConfigDict(extra="ignore")

    records_screened: int = Field(default=0, ge=0)
    records_excluded: int = Field(default=0, ge=0)
    exclusion_reasons: dict[str, int] = Field(default_factory=dict)


class PRISMAEligibilityPhase(BaseModel):
    """PRISMA 2020 Stage 3: Full-text report retrieval and eligibility assessment."""

    model_config = ConfigDict(extra="ignore")

    reports_sought_for_retrieval: int = Field(default=0, ge=0)
    reports_not_retrieved: int = Field(default=0, ge=0)
    reports_assessed_for_eligibility: int = Field(default=0, ge=0)
    reports_excluded: int = Field(default=0, ge=0)
    eligibility_exclusion_reasons: dict[str, int] = Field(default_factory=dict)


class PRISMAIncludedPhase(BaseModel):
    """PRISMA 2020 Stage 4: Studies and citations included in the synthesis."""

    model_config = ConfigDict(extra="ignore")

    new_studies_included: int = Field(default=0, ge=0)
    total_reports_included: int = Field(default=0, ge=0)
    included_citation_ids: list[str] = Field(default_factory=list)


class PRISMAFlowReport(BaseModel):
    """Full PRISMA 2020 flow diagram state and synthesis report."""

    model_config = ConfigDict(extra="ignore")

    project_id: str
    query_string: str = ""
    search_timestamp: str = Field(default_factory=lambda: utc_now().isoformat())
    identification: PRISMAIdentificationPhase = Field(default_factory=PRISMAIdentificationPhase)
    screening: PRISMAScreeningPhase = Field(default_factory=PRISMAScreeningPhase)
    eligibility: PRISMAEligibilityPhase = Field(default_factory=PRISMAEligibilityPhase)
    included: PRISMAIncludedPhase = Field(default_factory=PRISMAIncludedPhase)

    def record_database_search(self, provider: str, count: int) -> None:
        """Add record count identified from a specific academic database/provider."""
        self.identification.database_counts[provider] = count
        self.identification.total_records_identified = sum(
            self.identification.database_counts.values()
        ) + sum(self.identification.register_counts.values())

    def record_deduplication(self, removed_count: int) -> None:
        """Record duplicate records eliminated prior to screening."""
        self.identification.duplicate_records_removed = removed_count

    def record_screening(
        self,
        screened: int,
        excluded: int,
        reasons: dict[str, int] | None = None,
    ) -> None:
        """Record results from title and abstract screening."""
        self.screening.records_screened = screened
        self.screening.records_excluded = excluded
        if reasons:
            self.screening.exclusion_reasons.update(reasons)

    def record_eligibility(
        self,
        sought: int,
        not_retrieved: int,
        assessed: int,
        excluded: int,
        reasons: dict[str, int] | None = None,
        included_ids: list[str] | None = None,
    ) -> None:
        """Record full-text eligibility assessment and final inclusions."""
        self.eligibility.reports_sought_for_retrieval = sought
        self.eligibility.reports_not_retrieved = not_retrieved
        self.eligibility.reports_assessed_for_eligibility = assessed
        self.eligibility.reports_excluded = excluded
        if reasons:
            self.eligibility.eligibility_exclusion_reasons.update(reasons)

        final_included = max(0, assessed - excluded)
        self.included.new_studies_included = final_included
        self.included.total_reports_included = final_included
        if included_ids:
            self.included.included_citation_ids = included_ids

    def to_markdown_flowchart(self) -> str:
        """Render an audit-ready PRISMA 2020 Flow Diagram in Markdown."""
        id_phase = self.identification
        sc_phase = self.screening
        el_phase = self.eligibility
        inc_phase = self.included

        db_breakdown = (
            ", ".join(f"{k}: {v}" for k, v in id_phase.database_counts.items()) or "Ninguna"
        )
        scr_exclusions = (
            ", ".join(f"{k}: {v}" for k, v in sc_phase.exclusion_reasons.items())
            or "No especificado"
        )
        el_exclusions = (
            ", ".join(f"{k}: {v}" for k, v in el_phase.eligibility_exclusion_reasons.items())
            or "No especificado"
        )

        return f"""# Diagrama de Flujo PRISMA 2020

```text
================================================================================
                           FASE 1: IDENTIFICACIÓN
================================================================================
 Registros identificados en bases de datos (n = {id_phase.total_records_identified})
 [{db_breakdown}]
                                   │
                                   ▼
 [Registros duplicados eliminados (n = {id_phase.duplicate_records_removed})]
                                   │
                                   ▼
================================================================================
                             FASE 2: CRIBADO
================================================================================
 Registros cribados por título/resumen (n = {sc_phase.records_screened})
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
   [Registros excluidos (n = {sc_phase.records_excluded})]     [Informes solicitados para recuperación (n = {el_phase.reports_sought_for_retrieval})]
   Causas: {scr_exclusions}
                                                  │
                                                  ▼
                               [Informes no recuperados (n = {el_phase.reports_not_retrieved})]
                                                  │
                                                  ▼
================================================================================
                           FASE 3: ELEGIBILIDAD
================================================================================
 Informes evaluados a texto completo (n = {el_phase.reports_assessed_for_eligibility})
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
   [Informes excluidos (n = {el_phase.reports_excluded})]       ================================================================
   Causas: {el_exclusions}                                 FASE 4: INCLUSIÓN
                                                ================================================================
                                                 Estudios incluidos en la síntesis (n = {inc_phase.new_studies_included})
================================================================================
```
"""

    def to_dict(self) -> dict[str, Any]:
        """Convert PRISMA flow model to dict for persistence and API transport."""
        return self.model_dump()
