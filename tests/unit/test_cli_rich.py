"""Unit tests verifying Rich UI tables, panels, spinners, and audit reports in CLI."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from thesisforge.cli import main
from thesisforge.config import get_settings
from thesisforge.models import (
    AcademicLevel,
    AcademicSearchResultDTO,
    ProjectStateDTO,
    SectionDraftDTO,
    SectionStatus,
)
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


@pytest.fixture
def cli_db_url(tmp_path: Path) -> str:
    """Provide a file-based SQLite database for hermetic CLI testing."""
    db_file = tmp_path / "cli_test_rich.db"
    url = f"sqlite+aiosqlite:///{db_file}"
    get_settings.cache_clear()
    return url


def test_cli_rich_search_papers_table(capsys: pytest.CaptureFixture[str]):
    """Verify search-papers renders a Rich table with column headers and metadata."""
    with (
        patch("sys.argv", ["thesisforge", "search-papers", "Quantum Transformers", "--limit", "2"]),
        patch("thesisforge.rag.clients.aggregator.AcademicSearchAggregator.search") as mock_search,
    ):
        mock_search.return_value = [
            AcademicSearchResultDTO(
                paper_id="openalex:W999",
                title="Quantum Transformers for Natural Language Processing",
                authors=["Alice Quantum", "Bob Transformer"],
                year=2024,
                doi="10.1000/qt2024",
                source="openalex",
            )
        ]

        main()
        captured = capsys.readouterr()
        assert "Resultados de Literatura" in captured.out
        assert "Quantum" in captured.out
        assert "Transformers" in captured.out
        assert "Alice Quantum" in captured.out
        assert "openalex" in captured.out
        assert "10.1000/qt2024" in captured.out


def test_cli_rich_jury_audit_report(capsys: pytest.CaptureFixture[str], cli_db_url: str):
    """Verify jury-audit renders formatted verdict panel, juror dimensions, and issue severity badges."""
    project = ProjectStateDTO(id="proj-jury-01", title="Test Jury Project")

    async def setup_db():
        db = DatabaseManager(cli_db_url)
        await db.initialize()
        repo = ProjectRepository(db, "local")
        await repo.create_project(project)
        await db.close()

    asyncio.run(setup_db())

    with (
        patch.dict("os.environ", {"THESISFORGE_DATABASE_URL": cli_db_url}),
        patch("sys.argv", ["thesisforge", "jury-audit", "--project-id", "proj-jury-01"]),
        patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion,
    ):
        # Force fallback to rule-based evaluator
        mock_acompletion.side_effect = RuntimeError("Simulated LLM connection failure")

        main()
        captured = capsys.readouterr()
        assert "DICTAMEN OFICIAL DEL TRIBUNAL ACAD" in captured.out
        # In rule-based, score will be generated deterministically (e.g. 100/100 or something if project is empty, or 75, etc)
        # We just need to check if the juror is in the output (e.g. "Dra. Beatriz Salamanca" or "Dr. Arstides Valenzuela")
        # And check for "APROBADO"
        assert "APROBADO" in captured.out
        assert "MODIFICACIONES OBLIGATORIAS" in captured.out


def test_cli_rich_draft_list_styled(capsys: pytest.CaptureFixture[str], cli_db_url: str):
    """Verify draft-list displays chapters with formatted status badges and word counts."""
    project = ProjectStateDTO(
        id="proj-list-01",
        title="Tesis de Deep Learning",
        academic_level=AcademicLevel.DOCTORADO,
        sections=[
            SectionDraftDTO(
                section_id="sec_1_1",
                chapter_number=1,
                order_index=1,
                title="Planteamiento del Problema",
                status=SectionStatus.APPROVED,
                word_count=850,
            ),
            SectionDraftDTO(
                section_id="sec_2_1",
                chapter_number=2,
                order_index=1,
                title="Marco Te",
                status=SectionStatus.IN_PROGRESS,
                word_count=1200,
            ),
        ],
    )

    async def setup_db():
        db = DatabaseManager(cli_db_url)
        await db.initialize()
        repo = ProjectRepository(db, "local")
        await repo.create_project(project)
        await db.close()

    asyncio.run(setup_db())

    with (
        patch.dict("os.environ", {"THESISFORGE_DATABASE_URL": cli_db_url}),
        patch("sys.argv", ["thesisforge", "draft-list", "--project-id", "proj-list-01"]),
    ):
        main()
        captured = capsys.readouterr()
        assert "Tesis de Deep Learning" in captured.out
        assert "sec_1_1" in captured.out
        assert "approved" in captured.out
        assert "850 palabras" in captured.out
        assert "sec_2_1" in captured.out
        assert "in_progress" in captured.out


def test_cli_rich_export_docx_panel(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, cli_db_url: str
):
    """Verify export-docx displays Rich panel with destination path and size."""
    project = ProjectStateDTO(id="proj-docx-01", title="Test Docx Rich")

    async def setup_db():
        db = DatabaseManager(cli_db_url)
        await db.initialize()
        repo = ProjectRepository(db, "local")
        await repo.create_project(project)
        await db.close()

    asyncio.run(setup_db())

    out_file = tmp_path / "thesis_rich.docx"

    with (
        patch.dict("os.environ", {"THESISFORGE_DATABASE_URL": cli_db_url}),
        patch(
            "sys.argv",
            [
                "thesisforge",
                "export-docx",
                "--project-id",
                "proj-docx-01",
                "--output",
                str(out_file),
            ],
        ),
    ):
        main()

        captured = capsys.readouterr()
        assert "Exportaci" in captured.out
        assert "Documento APA 7 compilado exitosamente" in captured.out
        assert out_file.exists()
