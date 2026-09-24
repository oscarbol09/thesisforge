"""Domain data models and DTOs using Pydantic v2."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from thesisforge.core.time import utc_now


class AcademicLevel(str, Enum):
    """Academic level of the research project."""

    PREGRADO = "pregrado"
    MAESTRIA = "maestria"
    DOCTORADO = "doctorado"


class ResearchApproach(str, Enum):
    """Methodological approach."""

    CUANTITATIVO = "cuantitativo"
    CUALITATIVO = "cualitativo"
    MIXTO = "mixto"


class EpistemologicalParadigm(str, Enum):
    """Epistemological and philosophical research paradigm."""

    POSITIVISTA = "positivista"
    POSTPOSITIVISTA = "postpositivista"
    INTERPRETATIVO = "interpretativo"
    SOCIOCRITICO = "sociocritico"
    PRAGMATICO = "pragmatico"


class SamplingTechnique(str, Enum):
    """Scientific sampling strategy and selection technique."""

    PROBABILISTICO_ALEATORIO = "probabilistico_aleatorio"
    PROBABILISTICO_ESTRATIFICADO = "probabilistico_estratificado"
    PROBABILISTICO_CONGLOMERADOS = "probabilistico_conglomerados"
    NO_PROBABILISTICO_INTENCIONAL = "no_probabilistico_intencional"
    NO_PROBABILISTICO_BOLA_NIEVE = "no_probabilistico_bola_nieve"
    NO_PROBABILISTICO_POR_CUOTAS = "no_probabilistico_por_cuotas"
    CENSO_COMPLETO = "censo_completo"


class VariableType(str, Enum):
    """Classification of empirical research variables."""

    INDEPENDIENTE = "independiente"
    DEPENDIENTE = "dependiente"
    INTERVINIENTE = "interviniente"
    MODERADORA = "moderadora"
    CONTROL = "control"
    CATEGORIA_CUALITATIVA = "categoria_cualitativa"


class MeasurementScale(str, Enum):
    """Statistical scale of measurement for variable operationalization."""

    NOMINAL = "nominal"
    ORDINAL = "ordinal"
    INTERVALO = "intervalo"
    RAZON = "razon"


class ProjectPhase(str, Enum):
    """Current milestone/phase in the thesis construction pipeline."""

    SETUP = "setup"
    ORIENTATION = "orientation"
    CONTEXT = "context"
    DRAFTING = "drafting"
    REVIEW = "review"
    COMPLETED = "completed"


class SectionStatus(str, Enum):
    """Status of an individual chapter or section draft."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"


class JurorRole(str, Enum):
    """Role and profile of a member of the academic evaluation jury."""

    METODOLOGO = "metodologo"
    ESPECIALISTA_TEMATICO = "especialista_tematico"
    AUDITOR_ESTADISTICO = "auditor_estadistico"
    ABOGADO_DEL_DIABLO = "abogado_del_diablo"


class AuditSeverity(str, Enum):
    """Severity level of an audit observation or detected defect."""

    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    NOTE = "note"


class AuditIssueType(str, Enum):
    """Taxonomy of scientific audit issues and methodological biases."""

    METHODOLOGICAL_INCONSISTENCY = "methodological_inconsistency"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    CONCEPTUAL_CONTRADICTION = "conceptual_contradiction"
    SAMPLING_BIAS = "sampling_bias"
    INVALID_INSTRUMENT = "invalid_instrument"
    MISSING_LIMITATIONS = "missing_limitations"


class JuryVerdict(str, Enum):
    """Formal academic verdict emitted by the multi-perspective jury."""

    APROBADO_CON_DISTINCION = "aprobado_con_distincion"
    APROBADO = "aprobado"
    MODIFICACIONES_MENORES = "modificaciones_menores"
    MODIFICACIONES_MAYORES = "modificaciones_mayores"
    NO_APROBADO = "no_aprobado"


class DefenseStatus(str, Enum):
    """Status and final verdict of an interactive oral defense session."""

    IN_PROGRESS = "in_progress"
    PASSED_WITH_HONORS = "passed_with_honors"
    PASSED = "passed"
    NEEDS_REVISION = "needs_revision"
    FAILED = "failed"


class CitationDTO(BaseModel):
    """Metadata for verified academic literature with evidence traceability."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:10])
    doi: str | None = Field(default=None, max_length=100)
    title: str = Field(min_length=3, max_length=500)
    authors: list[str] = Field(default_factory=list)
    year: int = Field(ge=1, le=2100)
    journal: str | None = Field(default=None, max_length=300)
    abstract: str | None = Field(default=None, max_length=5000)
    url: str | None = Field(default=None, max_length=1000)
    source: str = Field(default="semantic_scholar", max_length=50)
    apa_formatted: str = Field(default="", max_length=1500)

    # Evidence traceability fields (Sprint 2)
    chunk_id: str | None = Field(default=None, max_length=100)
    section_name: str | None = Field(default=None, max_length=200)
    page_number: int | None = Field(default=None, ge=1)
    relevance_score: float | None = Field(default=None, ge=0.0, le=1.0)
    supports_claim: bool = False
    evidence_text: str | None = Field(default=None, max_length=5000)

    @field_validator("authors", mode="before")
    @classmethod
    def validate_authors(cls, v: list[str] | str) -> list[str]:
        if isinstance(v, str):
            return [a.strip() for a in v.split(";") if a.strip()]
        return [str(a).strip() for a in v if str(a).strip()]


class DocumentChunkDTO(BaseModel):
    """Segment of indexed academic literature with structural provenance."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    document_id: str = Field(min_length=1, max_length=100)
    project_id: str = Field(min_length=1, max_length=100)
    title: str = Field(default="", max_length=500)
    doi: str | None = Field(default=None, max_length=100)
    authors: list[str] = Field(default_factory=list)
    year: int | None = Field(default=None, ge=1800, le=2100)
    page_number: int = Field(default=1, ge=1)
    chunk_index: int = Field(default=0, ge=0)
    section_name: str = Field(default="body", max_length=200)
    text: str = Field(min_length=1)
    char_start: int = 0
    char_end: int = 0
    created_at: datetime = Field(default_factory=utc_now)


class EvidenceVerdictDTO(BaseModel):
    """Validation report verifying whether a claim is substantiated by indexed literature."""

    model_config = ConfigDict(extra="ignore")

    claim: str = Field(default="", min_length=0)
    is_supported: bool
    confidence_score: float = Field(ge=0.0, le=1.0)
    supporting_chunks: list[CitationDTO] = Field(default_factory=list)
    refuting_or_missing_reason: str = ""


class AcademicSearchResultDTO(BaseModel):
    """Unified search result entry across academic providers."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    paper_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    venue: str | None = None
    abstract: str | None = None
    doi: str | None = None
    url: str | None = None
    citation_count: int | None = None
    open_access_pdf: str | None = None
    source: str = "semantic_scholar"


class VariableOperationalizationDTO(BaseModel):
    """Operationalization matrix entry for quantitative or mixed variables."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:10])
    name: str = Field(min_length=1, max_length=200)
    variable_type: VariableType = VariableType.INDEPENDIENTE
    conceptual_definition: str = Field(default="", max_length=2000)
    operational_definition: str = Field(default="", max_length=2000)
    dimensions: list[str] = Field(default_factory=list)
    indicators: list[str] = Field(default_factory=list)
    measurement_scale: MeasurementScale = MeasurementScale.ORDINAL
    instrument_name: str = Field(default="", max_length=300)


class QualitativeCategoryDTO(BaseModel):
    """Categorical and axial coding structure for qualitative investigations."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:10])
    name: str = Field(min_length=1, max_length=200)
    category_type: str = Field(default="central", max_length=100)
    definition: str = Field(default="", max_length=2000)
    subcategories: list[str] = Field(default_factory=list)
    coding_criteria: str = Field(default="", max_length=2000)
    saturation_indicator: str = Field(default="", max_length=1000)


class MethodologyDTO(BaseModel):
    """Validated methodological data sheet created during Phase 1."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    approach: ResearchApproach | None = None
    paradigm: EpistemologicalParadigm | None = None
    design: str = Field(default="", max_length=500)
    population: str = Field(default="", max_length=500)
    sample: str = Field(default="", max_length=500)
    sampling_technique: SamplingTechnique | None = None
    unit_of_analysis: str = Field(default="", max_length=300)
    instruments: list[str] = Field(default_factory=list)
    analysis_technique: str = Field(default="", max_length=500)
    inclusion_criteria: list[str] = Field(default_factory=list)
    exclusion_criteria: list[str] = Field(default_factory=list)
    ethical_considerations: list[str] = Field(default_factory=list)
    data_collection_procedure: str = Field(default="", max_length=3000)
    temporal_scope: str = Field(default="transversal", max_length=100)
    spatial_setting: str = Field(default="", max_length=300)


class SectionDraftDTO(BaseModel):
    """Structured draft of a thesis chapter or subsection."""

    model_config = ConfigDict(extra="ignore")

    section_id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=300)
    chapter_number: int = Field(default=1, ge=1, le=10)
    order_index: int = Field(default=0, ge=0)
    content: str = ""
    summary: str = Field(default="", max_length=2000)
    status: SectionStatus = SectionStatus.PENDING
    word_count: int = Field(default=0, ge=0)
    citations_used: list[str] = Field(default_factory=list)
    user_feedback: str | None = None
    version: int = Field(default=1, ge=1)
    updated_at: datetime = Field(default_factory=utc_now)


class ExportFormat(str, Enum):
    """Supported document export formats."""

    DOCX = "docx"
    PDF = "pdf"
    MARKDOWN = "markdown"


class ExportOptionsDTO(BaseModel):
    """Configuration options for thesis compilation and document export."""

    model_config = ConfigDict(extra="ignore")

    format: ExportFormat = ExportFormat.DOCX
    include_cover_page: bool = True
    include_table_of_contents: bool = True
    include_references: bool = True
    font_name: str = Field(default="Times New Roman", max_length=50)
    font_size_pt: int = Field(default=12, ge=10, le=14)
    line_spacing: float = Field(default=2.0, ge=1.0, le=3.0)
    margin_inches: float = Field(default=1.0, ge=0.5, le=2.0)
    institution_name: str = Field(default="", max_length=200)
    faculty_or_program: str = Field(default="", max_length=200)
    author_name: str = Field(default="", max_length=200)
    advisor_name: str = Field(default="", max_length=200)
    city_and_country: str = Field(default="", max_length=200)
    year: int | None = Field(default=None, ge=1900, le=2100)


class ProjectCreateDTO(BaseModel):
    """DTO for creating a new research project."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(min_length=3, max_length=300)
    academic_level: AcademicLevel = AcademicLevel.PREGRADO
    area_of_study: str = Field(default="", max_length=200)
    topic: str = Field(default="", max_length=300)
    language: str = Field(default="es", max_length=10)


class ProjectSummaryDTO(BaseModel):
    """Lightweight summary of a project for listings."""

    model_config = ConfigDict(extra="ignore")

    id: str
    title: str
    academic_level: AcademicLevel
    phase: ProjectPhase
    created_at: datetime
    updated_at: datetime
    total_sections: int = 0
    approved_sections: int = 0


class ProjectStateDTO(BaseModel):
    """Global master state of a research project."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    phase: ProjectPhase = ProjectPhase.SETUP
    academic_level: AcademicLevel = AcademicLevel.PREGRADO

    # Phase 1: Problem Formulation & Methodology
    area_of_study: str = Field(default="", max_length=200)
    topic: str = Field(default="", max_length=300)
    title: str = Field(default="", max_length=300)
    research_problem: str = Field(default="", max_length=5000)
    research_question: str = Field(default="", max_length=1000)
    hypothesis: str | None = Field(default=None, max_length=2000)
    general_objective: str = Field(default="", max_length=1000)
    specific_objectives: list[str] = Field(default_factory=list)
    justification: str = Field(default="", max_length=5000)
    scope_limitations: str = Field(default="", max_length=3000)
    variables: list[str] = Field(default_factory=list)
    operationalized_variables: list[VariableOperationalizationDTO] = Field(default_factory=list)
    qualitative_categories: list[QualitativeCategoryDTO] = Field(default_factory=list)
    methodology: MethodologyDTO = Field(default_factory=MethodologyDTO)
    ethical_approval_status: str = Field(default="not_required", max_length=100)

    # Phase 2: Context & Academic Literature
    validated_citations: list[CitationDTO] = Field(default_factory=list)
    indexed_documents: list[str] = Field(default_factory=list)

    # Phase 3: Drafting & Chapter Sections
    sections: list[SectionDraftDTO] = Field(default_factory=list)

    # Document & Output Settings
    citation_style: str = Field(default="apa7", max_length=20)
    language: str = Field(default="es", max_length=10)

    def to_summary(self) -> ProjectSummaryDTO:
        """Derive a lightweight summary for UI dashboard."""
        approved = sum(1 for s in self.sections if s.status == SectionStatus.APPROVED)
        return ProjectSummaryDTO(
            id=self.id,
            title=self.title or "Proyecto sin título",
            academic_level=self.academic_level,
            phase=self.phase,
            created_at=self.created_at,
            updated_at=self.updated_at,
            total_sections=len(self.sections),
            approved_sections=approved,
        )


class AuditIssueDTO(BaseModel):
    """Specific methodological, conceptual, or empirical defect identified in the thesis."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:10])
    issue_type: AuditIssueType
    severity: AuditSeverity = AuditSeverity.MAJOR
    chapter_or_section: str = Field(default="general", max_length=200)
    title: str = Field(min_length=3, max_length=300)
    description: str = Field(min_length=5, max_length=3000)
    quote_or_passage: str | None = Field(default=None, max_length=1500)
    recommendation: str = Field(min_length=5, max_length=2000)


class JurorDimensionScoreDTO(BaseModel):
    """Evaluation score and analytical feedback from a specific juror persona."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    juror_role: JurorRole
    juror_name: str = Field(min_length=2, max_length=200)
    dimension_name: str = Field(min_length=2, max_length=200)
    score: float = Field(ge=0.0, le=100.0)
    criteria_evaluation: str = Field(default="", max_length=3000)
    feedback: str = Field(default="", max_length=3000)
    strengths: list[str] = Field(default_factory=list)
    flaws: list[str] = Field(default_factory=list)


class JuryEvaluationReportDTO(BaseModel):
    """Comprehensive academic jury evaluation report for a thesis project."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    project_id: str = Field(min_length=1, max_length=100)
    overall_score: float = Field(ge=0.0, le=100.0)
    verdict: JuryVerdict
    summary_dictamen: str = Field(min_length=10, max_length=5000)
    juror_evaluations: list[JurorDimensionScoreDTO] = Field(default_factory=list)
    issues: list[AuditIssueDTO] = Field(default_factory=list)
    mandatory_fixes: list[str] = Field(default_factory=list)
    recommended_improvements: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class DefenseTurnDTO(BaseModel):
    """A single turn in an interactive oral thesis defense."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    turn_index: int = Field(ge=0)
    juror_role: JurorRole
    juror_name: str = Field(min_length=2, max_length=200)
    question: str = Field(min_length=5, max_length=2000)
    focus_area: str = Field(default="Metodología", max_length=200)
    student_answer: str | None = Field(default=None, max_length=5000)
    juror_feedback: str | None = Field(default=None, max_length=3000)
    turn_score: float | None = Field(default=None, ge=0.0, le=100.0)
    is_answered: bool = False
    created_at: datetime = Field(default_factory=utc_now)


class DefenseSessionDTO(BaseModel):
    """Stateful interactive oral thesis defense simulation session."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    project_id: str = Field(min_length=1, max_length=100)
    academic_level: AcademicLevel = AcademicLevel.PREGRADO
    status: DefenseStatus = DefenseStatus.IN_PROGRESS
    current_turn_index: int = Field(default=0, ge=0)
    total_turns: int = Field(default=4, ge=1, le=10)
    turns: list[DefenseTurnDTO] = Field(default_factory=list)
    final_verdict: DefenseStatus | None = None
    final_score: float | None = Field(default=None, ge=0.0, le=100.0)
    final_remarks: str | None = Field(default=None, max_length=5000)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
