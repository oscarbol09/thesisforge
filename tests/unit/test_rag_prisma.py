"""Unit tests for PRISMA 2020 systematic review flow generator."""

import pytest

from thesisforge.models import AcademicSearchResultDTO, CitationDTO, ProjectStateDTO
from thesisforge.rag.prisma import PRISMAFlowReport
from thesisforge.rag.service import RAGService
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


def test_prisma_flow_record_stages_and_counts() -> None:
    report = PRISMAFlowReport(
        project_id="proj_prisma_test",
        query_string="Machine Learning in Education",
    )

    # Stage 1: Identification
    report.record_database_search("semantic_scholar", 50)
    report.record_database_search("arxiv", 30)
    report.record_database_search("crossref", 20)
    assert report.identification.total_records_identified == 100

    report.record_deduplication(15)
    assert report.identification.duplicate_records_removed == 15

    # Stage 2: Screening
    report.record_screening(
        screened=85,
        excluded=35,
        reasons={"fuera_de_alcance": 25, "idioma_no_valido": 10},
    )
    assert report.screening.records_screened == 85
    assert report.screening.records_excluded == 35
    assert report.screening.exclusion_reasons["fuera_de_alcance"] == 25

    # Stage 3: Eligibility & Stage 4: Included
    report.record_eligibility(
        sought=50,
        not_retrieved=5,
        assessed=45,
        excluded=15,
        reasons={"metodologia_inadecuada": 10, "datos_insuficientes": 5},
        included_ids=["10.1016/j.compedu.2023", "10.1145/345"],
    )
    assert report.eligibility.reports_sought_for_retrieval == 50
    assert report.eligibility.reports_not_retrieved == 5
    assert report.eligibility.reports_assessed_for_eligibility == 45
    assert report.eligibility.reports_excluded == 15
    assert report.included.new_studies_included == 30
    assert len(report.included.included_citation_ids) == 2


def test_prisma_markdown_diagram_generation() -> None:
    report = PRISMAFlowReport(project_id="proj_md_test")
    report.record_database_search("semantic_scholar", 10)
    report.record_deduplication(2)
    report.record_screening(8, 3, {"no_relevante": 3})
    report.record_eligibility(5, 0, 5, 1, {"calidad_baja": 1}, ["10.1234/test"])

    diagram = report.to_markdown_flowchart()
    assert "# Diagrama de Flujo PRISMA 2020" in diagram
    assert "FASE 1: IDENTIFICACIÓN" in diagram
    assert "FASE 2: CRIBADO" in diagram
    assert "FASE 3: ELEGIBILIDAD" in diagram
    assert "FASE 4: INCLUSIÓN" in diagram
    assert "Estudios incluidos en la síntesis (n = 4)" in diagram


def test_prisma_serialization_to_dict() -> None:
    report = PRISMAFlowReport(project_id="proj_dict_test")
    d = report.to_dict()
    assert d["project_id"] == "proj_dict_test"
    assert "identification" in d
    assert "screening" in d
    assert "eligibility" in d
    assert "included" in d


def test_prisma_exploratory_synthesis_fields_and_dict() -> None:
    """Verify is_exploratory_synthesis and protocol_notice fields and serialization."""
    report = PRISMAFlowReport(project_id="proj_exploratory")
    # Defaults
    assert report.is_exploratory_synthesis is False
    assert "PROSPERO" in report.protocol_notice
    assert "riesgo de sesgo" in report.protocol_notice

    # Customization and serialization
    report.is_exploratory_synthesis = True
    d = report.to_dict()
    assert d["is_exploratory_synthesis"] is True
    assert "PROSPERO" in d["protocol_notice"]


def test_prisma_exploratory_markdown_flowchart_header_and_notice() -> None:
    """Verify markdown output changes title and embeds protocol notice for exploratory synthesis."""
    report = PRISMAFlowReport(project_id="proj_exploratory_md", is_exploratory_synthesis=True)
    report.record_database_search("citas_indexadas_proyecto", 5)
    report.record_screening(5, 0)
    report.record_eligibility(5, 0, 5, 0, included_ids=["id1", "id2"])

    diagram = report.to_markdown_flowchart()
    assert (
        "# Diagrama de Flujo de Literatura (Inspirado en PRISMA 2020 - Síntesis Exploratoria)"
        in diagram
    )
    assert report.protocol_notice in diagram
    assert "citas_indexadas_proyecto: 5" in diagram


@pytest.mark.asyncio
async def test_build_prisma_flow_exploratory_without_search_results(
    in_memory_db: DatabaseManager,
) -> None:
    """When build_prisma_flow is called without search_results, it must be marked exploratory."""
    repo = ProjectRepository(in_memory_db, "local")
    rag = RAGService(db_manager=in_memory_db, project_repo=repo, is_memory=True)

    project = ProjectStateDTO(
        id="proj_prisma_exploratory",
        title="Estudio de Machine Learning",
        topic="ML en educación",
        validated_citations=[
            CitationDTO(id="c1", title="Paper A", doi="10.1000/a"),
            CitationDTO(id="c2", title="Paper B", doi="10.1000/b"),
        ],
    )
    await repo.create_project(project)

    # Call build_prisma_flow with search_results=None
    report = await rag.build_prisma_flow(
        project_id="proj_prisma_exploratory",
        search_results=None,
    )

    assert report.is_exploratory_synthesis is True
    assert "citas_indexadas_proyecto" in report.identification.database_counts
    assert report.identification.database_counts["citas_indexadas_proyecto"] == 2
    assert report.included.new_studies_included == 2

    # Check persisted state
    saved_project = await repo.get_project("proj_prisma_exploratory")
    assert saved_project.prisma_flow is not None
    assert saved_project.prisma_flow["is_exploratory_synthesis"] is True


@pytest.mark.asyncio
async def test_build_prisma_flow_standard_with_search_results(
    in_memory_db: DatabaseManager,
) -> None:
    """When build_prisma_flow is called with search_results, it is standard (not exploratory)."""
    repo = ProjectRepository(in_memory_db, "local")
    rag = RAGService(db_manager=in_memory_db, project_repo=repo, is_memory=True)

    project = ProjectStateDTO(
        id="proj_prisma_standard",
        title="Estudio Sistemático",
        topic="Robótica médica",
    )
    await repo.create_project(project)

    search_results = [
        AcademicSearchResultDTO(
            paper_id="p1",
            title="Paper One",
            doi="10.1000/1",
            source="crossref",
        ),
        AcademicSearchResultDTO(
            paper_id="p2",
            title="Paper Two",
            doi="10.1000/2",
            source="semantic_scholar",
        ),
    ]

    report = await rag.build_prisma_flow(
        project_id="proj_prisma_standard",
        search_results=search_results,
    )

    assert report.is_exploratory_synthesis is False
    assert report.identification.database_counts.get("crossref") == 1
    assert report.identification.database_counts.get("semantic_scholar") == 1
