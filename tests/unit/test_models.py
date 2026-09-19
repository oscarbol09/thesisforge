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
    """Test CitationDTO rejects invalid years outside 1900-2100."""
    with pytest.raises(ValidationError):
        CitationDTO(title="Invalid Year", authors=["Author"], year=1850)

    with pytest.raises(ValidationError):
        CitationDTO(title="Invalid Year", authors=["Author"], year=2250)


def test_invalid_academic_level():
    """Test that invalid academic levels are rejected by Pydantic."""
    with pytest.raises(ValidationError):
        ProjectCreateDTO(title="Test", academic_level="post-doc")  # type: ignore[arg-type]
