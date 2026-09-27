"""Unit tests for BibTeXExporter, citekey generation, LaTeX character escaping, and export routes."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from thesisforge.api.app import app
from thesisforge.cli import main
from thesisforge.export.bibtex_exporter import (
    BibTeXExporter,
    escape_latex,
    extract_first_author_lastname,
    extract_title_keyword,
    generate_citekey,
)
from thesisforge.export.service import ExportService
from thesisforge.models import (
    AcademicSearchResultDTO,
    CitationDTO,
    ProjectStateDTO,
)
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


def test_escape_latex():
    """Verify LaTeX special character escaping."""
    raw = r"Analysis of 50% & $100 #1 _tag_ ~wave ^caret"
    escaped = escape_latex(raw)
    assert r"\%" in escaped
    assert r"\&" in escaped
    assert r"\$" in escaped
    assert r"\#" in escaped
    assert r"\_" in escaped
    assert r"\textasciitilde{}" in escaped
    assert r"\textasciicircum{}" in escaped
    assert escape_latex(None) == ""


def test_extract_first_author_lastname_and_title():
    """Verify author lastname extraction with accents and formats."""
    # Lastname, Firstname
    assert extract_first_author_lastname(["García Márquez, Gabriel"]) == "garciamarquez"
    # Firstname Lastname
    assert extract_first_author_lastname(["Patrick Lewis"]) == "lewis"
    # Accented Müller
    assert extract_first_author_lastname(["Thomas Müller"]) == "muller"
    # Empty author list
    assert extract_first_author_lastname([]) == "thesisforge"

    # Stopwords skipping
    assert extract_title_keyword("A Comprehensive Study on Deep Learning") == "comprehensive"
    assert extract_title_keyword("The Architecture of Modern LLMs") == "architecture"
    assert extract_title_keyword("El Impacto de la Inteligencia Artificial") == "impacto"
    assert extract_title_keyword(None) == "doc"


def test_generate_citekey_collisions():
    """Verify citekey generation and collision resolution suffixing."""
    seen: set[str] = set()

    k1 = generate_citekey(
        ["Ashish Vaswani", "Noam Shazeer"], 2017, "Attention Is All You Need", seen
    )
    assert k1 == "vaswani2017attention"

    # Second citation with same author, year, title
    k2 = generate_citekey(["Ashish Vaswani"], 2017, "Attention Is All You Need (Extended)", seen)
    assert k2 == "vaswani2017attentiona"

    # Third collision
    k3 = generate_citekey(["Vaswani, A."], 2017, "Attention and Transformers", seen)
    assert k3 == "vaswani2017attentionb"


def test_bibtex_exporter_single_citation_article():
    """Verify BibTeX export of an academic article."""
    exporter = BibTeXExporter()
    citation = CitationDTO(
        id="cit-001",
        title="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        authors=["Patrick Lewis", "Ethan Perez", "Aleksandra Piktus"],
        year=2020,
        journal="Advances in Neural Information Processing Systems",
        doi="10.5555/rag2020",
        url="https://arxiv.org/abs/2005.11401",
        abstract="Building models that combine parametric and non-parametric memory.",
        source="arxiv",
    )

    bib_entry = exporter.export_citation(citation)
    assert bib_entry.startswith("@misc{lewis2020retrieval,") or "@article" in bib_entry
    assert (
        "title = {{Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks}}" in bib_entry
    )
    assert "author = {Patrick Lewis and Ethan Perez and Aleksandra Piktus}" in bib_entry
    assert "year = {2020}" in bib_entry
    assert "doi = {10.5555/rag2020}" in bib_entry
    assert "eprint = {2005.11401}" in bib_entry
    assert "archivePrefix = {arXiv}" in bib_entry


def test_bibtex_exporter_academic_search_dto():
    """Verify BibTeX export from an AcademicSearchResultDTO."""
    exporter = BibTeXExporter()
    dto = AcademicSearchResultDTO(
        paper_id="openalex:W12345",
        title="Deep Residual Learning for Image Recognition",
        authors=["He, Kaiming", "Zhang, Xiangyu", "Ren, Shaoqing"],
        year=2016,
        venue="IEEE Conference on Computer Vision and Pattern Recognition",
        doi="10.1109/cvpr.2016.90",
        citation_count=180000,
        source="openalex",
    )

    bib_entry = exporter.export_citation(dto)
    assert "@inproceedings{" in bib_entry
    assert "booktitle = {IEEE Conference on Computer Vision and Pattern Recognition}" in bib_entry
    assert "doi = {10.1109/cvpr.2016.90}" in bib_entry


@pytest.mark.asyncio
async def test_export_service_bibtex(in_memory_db: DatabaseManager, tmp_path: Path):
    """Verify ExportService compiles and saves project bibliography as .bib file."""
    repo = ProjectRepository(in_memory_db, "local")
    project = ProjectStateDTO(
        id="proj-bib-test-01",
        title="Investigación de Modelos Fundacionales",
        validated_citations=[
            CitationDTO(
                id="c1",
                title="Attention Is All You Need",
                authors=["Vaswani, Ashish", "Shazeer, Noam"],
                year=2017,
                doi="10.48550/arXiv.1706.03762",
                journal="NeurIPS",
            ),
            CitationDTO(
                id="c2",
                title="Language Models are Few-Shot Learners",
                authors=["Brown, Tom", "Mann, Benjamin"],
                year=2020,
                doi="10.48550/arXiv.2005.14165",
                journal="NeurIPS",
            ),
        ],
    )
    await repo.create_project(project)

    export_service = ExportService(db_manager=in_memory_db, project_repo=repo)
    bib_text = await export_service.compile_project_bibtex("proj-bib-test-01")

    assert "BibTeX Project Bibliography" in bib_text
    assert "vaswani2017attention" in bib_text
    assert "brown2020language" in bib_text

    target_file = tmp_path / "test_refs.bib"
    saved = await export_service.save_project_bibtex("proj-bib-test-01", target_file)

    assert saved.exists()
    assert saved.stat().st_size > 0
    content = saved.read_text(encoding="utf-8")
    assert "Attention Is All You Need" in content


@pytest.mark.asyncio
async def test_api_export_project_bibtex(in_memory_db: DatabaseManager):
    """Verify REST API endpoint GET /api/export/projects/{project_id}/bibtex."""
    from httpx import ASGITransport, AsyncClient

    from thesisforge.api.deps import get_db_manager

    app.dependency_overrides[get_db_manager] = lambda: in_memory_db
    try:
        repo = ProjectRepository(in_memory_db, "local")
        project = ProjectStateDTO(
            id="proj-api-bib-01",
            title="Proyecto API BibTeX",
            validated_citations=[
                CitationDTO(
                    id="c1",
                    title="Transformer Models in NLP",
                    authors=["Wolf, Thomas"],
                    year=2020,
                )
            ],
        )
        await repo.create_project(project)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/export/projects/proj-api-bib-01/bibtex")
            assert response.status_code == 200
            assert "text/plain" in response.headers["content-type"]
            assert (
                'attachment; filename="bibliografia_proj-api-bib-01.bib"'
                in response.headers["content-disposition"]
            )
            assert "wolf2020transformer" in response.text
    finally:
        app.dependency_overrides.clear()


def test_cli_export_bib_command(capsys: pytest.CaptureFixture[str], tmp_path: Path):
    """Test CLI export-bib subcommand with output file."""
    fake_bib = tmp_path / "output_test.bib"
    fake_bib.write_text("@article{test2024,\n  title = {{Test}}\n}\n", encoding="utf-8")

    with (
        patch(
            "sys.argv",
            [
                "thesisforge",
                "export-bib",
                "--project-id",
                "proj-cli-bib-01",
                "--output",
                str(fake_bib),
            ],
        ),
        patch(
            "thesisforge.export.service.ExportService.save_project_bibtex", new_callable=AsyncMock
        ) as mock_save,
        patch("thesisforge.repository.database.DatabaseManager.initialize", new_callable=AsyncMock),
        patch("thesisforge.repository.database.DatabaseManager.close", new_callable=AsyncMock),
    ):
        mock_save.return_value = fake_bib
        main()

        captured = capsys.readouterr()
        assert "Bibliografía BibTeX exportada exitosamente" in captured.out
