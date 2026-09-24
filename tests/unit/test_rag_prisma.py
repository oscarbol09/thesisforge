"""Unit tests for PRISMA 2020 systematic review flow generator."""


from thesisforge.rag.prisma import PRISMAFlowReport


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
