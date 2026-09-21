"""Unit tests for canonical thesis templates and HierarchicalMemoryManager."""

from thesisforge.drafting.memory import HierarchicalMemoryManager
from thesisforge.drafting.templates import (
    CANONICAL_THESIS_OUTLINE,
    get_default_thesis_sections,
)
from thesisforge.models import (
    AcademicLevel,
    DocumentChunkDTO,
    MethodologyDTO,
    ProjectPhase,
    ProjectStateDTO,
    ResearchApproach,
    SectionDraftDTO,
    SectionStatus,
)


def test_canonical_thesis_outline_structure():
    """Verify standard outline contains all 5 chapters and valid order indexes."""
    assert len(CANONICAL_THESIS_OUTLINE) >= 15
    chapter_numbers = {t.chapter_number for t in CANONICAL_THESIS_OUTLINE}
    assert chapter_numbers == {1, 2, 3, 4, 5}

    # Verify order indexes are strictly ascending
    order_indexes = [t.order_index for t in CANONICAL_THESIS_OUTLINE]
    assert order_indexes == sorted(order_indexes)


def test_get_default_thesis_sections_quantitative_vs_qualitative():
    """Verify quantitative projects include hypothesis section while qualitative projects exclude it."""
    quant_sections = get_default_thesis_sections(approach=ResearchApproach.CUANTITATIVO)
    qual_sections = get_default_thesis_sections(approach=ResearchApproach.CUALITATIVO)

    quant_ids = {s.section_id for s in quant_sections}
    qual_ids = {s.section_id for s in qual_sections}

    assert "sec_2_4" in quant_ids  # Hypothesis & Variables
    assert "sec_2_4" not in qual_ids  # Excluded in Qualitative
    assert len(quant_sections) > len(qual_sections)


def test_hierarchical_memory_manager_builds_layers():
    """Verify HierarchicalMemoryManager assembles Layer 0, Layer 1 preceding memory, and Layer 2 RAG."""
    project = ProjectStateDTO(
        id="proj-mem-01",
        title="Impacto de la Inteligencia Artificial en Tesis Universitarias",
        academic_level=AcademicLevel.MAESTRIA,
        phase=ProjectPhase.DRAFTING,
        research_problem="Uso acrítico de LLMs en posgrado.",
        research_question="¿Cómo influye el uso guiado de RAG en la precisión metodológica?",
        general_objective="Determinar la influencia de la arquitectura RAG en la precisión metodológica.",
        specific_objectives=[
            "Diagnosticar la tasa de alucinaciones en marcos teóricos.",
            "Diseñar un sistema de verificación socrática y de citación.",
            "Evaluar el impacto en la coherencia de los capítulos.",
        ],
        hypothesis="El uso de RAG reduce significativamente las citas alucinadas.",
        variables=["Arquitectura RAG", "Precisión metodológica"],
        methodology=MethodologyDTO(
            approach=ResearchApproach.CUANTITATIVO,
            design="Cuasi-experimental",
            population="200 tesistas",
            sample="60 tesistas",
            instruments=["Rúbrica de evaluación metodológica"],
        ),
        sections=[
            SectionDraftDTO(
                section_id="sec_1_1",
                title="1.1 Planteamiento del Problema",
                chapter_number=1,
                order_index=1,
                content="El problema radica en la proliferación de referencias falsas.",
                summary="Se identificó una tasa del 40% de alucinaciones en borradores iniciales.",
                status=SectionStatus.APPROVED,
            ),
            SectionDraftDTO(
                section_id="sec_2_1",
                title="2.1 Antecedentes de la Investigación",
                chapter_number=2,
                order_index=6,
                content="",
                status=SectionStatus.PENDING,
            ),
        ],
    )

    chunks = [
        DocumentChunkDTO(
            id="chunk_1",
            document_id="doc_1",
            project_id="proj-mem-01",
            title="Estudio sobre Alucinaciones",
            doi="10.1000/eval",
            authors=["Gómez, M."],
            year=2024,
            text="Los sistemas RAG reducen el error factual a menos del 1% en corpus técnicos.",
        )
    ]

    context = HierarchicalMemoryManager.build_drafting_context(
        project=project,
        target_section_id="sec_2_1",
        retrieved_chunks=chunks,
        user_guidance="Enfocarse en antecedentes latinoamericanos de los últimos 3 años.",
    )

    # Assert Layer 0 present
    assert "[FUNDACIÓN METODOLÓGICA DEL PROYECTO]" in context["layer_0_methodology"]
    assert "Determinar la influencia de la arquitectura RAG" in context["layer_0_methodology"]
    assert "Diagnosticar la tasa de alucinaciones" in context["layer_0_methodology"]

    # Assert Layer 1 contains preceding summary from Chapter 1
    assert "[MEMORIA DE CAPÍTULOS PRECEDENTES]" in context["layer_1_memory"]
    assert "1.1 Planteamiento del Problema" in context["layer_1_memory"]
    assert "tasa del 40% de alucinaciones" in context["layer_1_memory"]

    # Assert Layer 2 contains RAG chunk
    assert "[LITERATURA CIENTÍFICA RECUPERADA" in context["layer_2_literature"]
    assert "10.1000/eval" in context["layer_2_literature"]
    assert "Gómez, M." in context["layer_2_literature"]

    # Assert target guidance included
    assert "Enfocarse en antecedentes latinoamericanos" in context["target_section_info"]
