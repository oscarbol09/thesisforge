"""Unit tests for Pydantic v2 domain models."""

import pytest
from pydantic import ValidationError

from thesisforge.models import (
    AcademicLevel,
    CitationDTO,
    ProjectCreateDTO,
    ProjectPhase,
    ProjectStateDTO,
    ResearchApproach,
    SectionStatus,
)


def test_project_state_serialization_roundtrip(sample_project: ProjectStateDTO):
    """Ensure ProjectStateDTO can serialize to JSON and deserialize with full fidelity."""
    json_data = sample_project.model_dump_json()
    reconstructed = ProjectStateDTO.model_validate_json(json_data)

    assert reconstructed.id == sample_project.id
    assert reconstructed.title == sample_project.title
    assert reconstructed.academic_level == AcademicLevel.PREGRADO
    assert reconstructed.methodology.approach == ResearchApproach.CUANTITATIVO
    assert len(reconstructed.sections) == 2
    assert reconstructed.sections[0].status == SectionStatus.APPROVED
    assert len(reconstructed.validated_citations) == 1


def test_project_to_summary(sample_project: ProjectStateDTO):
    """Test generating a lightweight ProjectSummaryDTO."""
    summary = sample_project.to_summary()
    assert summary.id == sample_project.id
    assert summary.title == sample_project.title
    assert summary.total_sections == 2
    assert summary.approved_sections == 1
    assert summary.phase == ProjectPhase.ORIENTATION


def test_citation_dto_author_string_parsing():
    """Test CitationDTO parses semicolon-separated authors string into list."""
    citation = CitationDTO(
        title="Valid Scientific Title",
        authors="Turing, A. ; Lovelace, A.",
        year=2024,
    )
    assert citation.authors == ["Turing, A.", "Lovelace, A."]


def test_citation_dto_year_validation():
    """Test CitationDTO accepts historical classical years (e.g. 1687, 1850) and rejects invalid years."""
    # Historical classics allowed
    cit_newton = CitationDTO(
        title="Philosophiae Naturalis Principia Mathematica", authors=["Isaac Newton"], year=1687
    )
    assert cit_newton.year == 1687

    cit_darwin = CitationDTO(
        title="On the Origin of Species", authors=["Charles Darwin"], year=1859
    )
    assert cit_darwin.year == 1859

    with pytest.raises(ValidationError):
        CitationDTO(title="Invalid Year", authors=["Author"], year=0)

    with pytest.raises(ValidationError):
        CitationDTO(title="Invalid Year", authors=["Author"], year=2250)


def test_invalid_academic_level():
    """Test that invalid academic levels are rejected by Pydantic."""
    with pytest.raises(ValidationError):
        ProjectCreateDTO(title="Test", academic_level="post-doc")  # type: ignore[arg-type]


def test_section_draft_dto_and_export_options():
    """Test SectionDraftDTO chapter metadata and ExportOptionsDTO defaults."""
    from thesisforge.models import ExportFormat, ExportOptionsDTO, SectionDraftDTO

    draft = SectionDraftDTO(
        section_id="sec_1_1",
        title="1.1 Planteamiento del Problema",
        chapter_number=1,
        order_index=1,
        content="Contenido del problema...",
    )
    assert draft.chapter_number == 1
    assert draft.order_index == 1
    assert draft.status == SectionStatus.PENDING

    export_opts = ExportOptionsDTO(
        format=ExportFormat.DOCX,
        author_name="Oscar Madera",
        institution_name="Universidad Nacional",
    )
    assert export_opts.format == ExportFormat.DOCX
    assert export_opts.font_name == "Times New Roman"
    assert export_opts.font_size_pt == 12
    assert export_opts.line_spacing == 2.0
    assert export_opts.include_cover_page is True
