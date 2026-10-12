"""Unit tests for Literature Categories and RAG section routing (preventing cross-contamination)."""

import pytest

from thesisforge.drafting.templates import CANONICAL_THESIS_OUTLINE
from thesisforge.models import (
    DocumentChunkDTO,
    LiteratureCategory,
)
from thesisforge.rag.vectorstore import ChromaVectorStore
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.migrations import DatabaseMigrator


def test_literature_category_enum_values() -> None:
    """Verify all canonical academic literature categories are defined."""
    assert LiteratureCategory.ANTECEDENTES == "antecedentes"
    assert LiteratureCategory.MARCO_TEORICO == "marco_teorico"
    assert LiteratureCategory.MARCO_CONCEPTUAL == "marco_conceptual"
    assert LiteratureCategory.MARCO_LEGAL == "marco_legal"
    assert LiteratureCategory.METODOLOGIA == "metodologia"
    assert LiteratureCategory.GENERAL == "general"


def test_section_templates_declare_allowed_literature_categories() -> None:
    """Verify that canonical sections define appropriate allowed literature categories to prevent cross-contamination."""
    antecedentes_tmpl = next(t for t in CANONICAL_THESIS_OUTLINE if t.section_id == "sec_2_1")
    assert LiteratureCategory.ANTECEDENTES in antecedentes_tmpl.allowed_literature_categories
    assert LiteratureCategory.METODOLOGIA not in antecedentes_tmpl.allowed_literature_categories

    teoria_tmpl = next(t for t in CANONICAL_THESIS_OUTLINE if t.section_id == "sec_2_2")
    assert LiteratureCategory.MARCO_TEORICO in teoria_tmpl.allowed_literature_categories
    assert LiteratureCategory.MARCO_LEGAL not in teoria_tmpl.allowed_literature_categories

    metodologia_tmpl = next(t for t in CANONICAL_THESIS_OUTLINE if t.section_id == "sec_3_1")
    assert LiteratureCategory.METODOLOGIA in metodologia_tmpl.allowed_literature_categories
    assert LiteratureCategory.ANTECEDENTES not in metodologia_tmpl.allowed_literature_categories


@pytest.mark.asyncio
async def test_chroma_query_chunks_filters_by_category() -> None:
    """Verify that ChromaVectorStore filters chunks by category, isolating clusters."""
    store = ChromaVectorStore(is_memory=True)
    project_id = "proj-cat-test"

    chunks = [
        DocumentChunkDTO(
            id="chunk-ant-1",
            document_id="doc-ant",
            project_id=project_id,
            title="Antecedente Empírico 2024",
            section_name="antecedentes",
            category=LiteratureCategory.ANTECEDENTES,
            text="Estudio empírico de López (2024) sobre el impacto de RAG en 120 tesistas.",
        ),
        DocumentChunkDTO(
            id="chunk-met-1",
            document_id="doc-met",
            project_id=project_id,
            title="Manual de Metodología",
            section_name="metodologia",
            category=LiteratureCategory.METODOLOGIA,
            text="Cálculo del tamaño muestral con G*Power para diseños correlacionales.",
        ),
    ]

    await store.add_chunks(project_id, chunks)

    # Query asking specifically for antecedentes
    results_ant = await store.query_chunks(
        project_id=project_id,
        query="estudio muestral en tesis",
        categories=[LiteratureCategory.ANTECEDENTES],
    )
    assert len(results_ant) == 1
    assert results_ant[0].id == "chunk-ant-1"

    # Query asking specifically for metodologia
    results_met = await store.query_chunks(
        project_id=project_id,
        query="estudio muestral en tesis",
        categories=[LiteratureCategory.METODOLOGIA],
    )
    assert len(results_met) == 1
    assert results_met[0].id == "chunk-met-1"


@pytest.mark.asyncio
async def test_database_migration_v6_adds_category_column(in_memory_db: DatabaseManager) -> None:
    """Verify that schema migration v6 safely ensures category column exists on document_index_status."""
    async with in_memory_db.get_connection() as conn:
        version = await DatabaseMigrator.apply_all(conn)
        assert version >= 6

        async with conn.execute("PRAGMA table_info(document_index_status);") as cursor:
            cols = [row[1] async for row in cursor]
        assert "category" in cols
