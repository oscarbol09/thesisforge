"""Unit tests for ThesisForge CLI entrypoint."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from thesisforge.cli import main
from thesisforge.models import SectionDraftDTO, SectionStatus


def test_cli_version(capsys: pytest.CaptureFixture[str]):
    """Test CLI --version flag output."""
    with patch("sys.argv", ["thesisforge", "--version"]), pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "ThesisForge v" in captured.out


def test_cli_run_command():
    """Test CLI run invocation calls uvicorn.run with configured params."""
    with (
        patch(
            "sys.argv", ["thesisforge", "run", "--host", "0.0.0.0", "--port", "9000", "--reload"]
        ),
        patch("uvicorn.run") as mock_run,
    ):
        main()
        mock_run.assert_called_once_with(
            "thesisforge.api.app:app",
            host="0.0.0.0",
            port=9000,
            reload=True,
        )


def test_cli_search_papers_command(capsys: pytest.CaptureFixture[str]):
    """Test CLI search-papers subcommand."""
    with (
        patch("sys.argv", ["thesisforge", "search-papers", "Quantum Computing", "--limit", "2"]),
        patch("thesisforge.rag.clients.aggregator.AcademicSearchAggregator.search") as mock_search,
    ):
        from thesisforge.models import AcademicSearchResultDTO

        mock_search.return_value = [
            AcademicSearchResultDTO(
                paper_id="paper_1",
                title="Quantum Algorithms for Optimization",
                authors=["Author One", "Author Two"],
                year=2023,
                doi="10.1000/182",
                source="semantic_scholar",
            )
        ]

        main()
        captured = capsys.readouterr()
        assert "Quantum Algorithms for Optimization" in captured.out
        assert "DOI:" in captured.out


def test_cli_search_papers_apa_format(capsys: pytest.CaptureFixture[str]):
    """Test CLI search-papers subcommand with --format apa."""
    with (
        patch(
            "sys.argv",
            ["thesisforge", "search-papers", "Transformers", "--limit", "1", "--format", "apa"],
        ),
        patch("thesisforge.rag.clients.aggregator.AcademicSearchAggregator.search") as mock_search,
    ):
        from thesisforge.models import AcademicSearchResultDTO

        mock_search.return_value = [
            AcademicSearchResultDTO(
                paper_id="paper_2",
                title="Attention Is All You Need",
                authors=["Vaswani, Ashish", "Shazeer, Noam"],
                year=2017,
                doi="10.5555/attention",
                source="semantic_scholar",
            )
        ]

        main()
        captured = capsys.readouterr()
        assert "Vaswani, A." in captured.out
        assert "(2017)" in captured.out


def test_cli_export_docx_command(capsys: pytest.CaptureFixture[str], tmp_path: Path):
    """Test CLI export-docx subcommand."""
    fake_file = tmp_path / "thesis_cli.docx"
    fake_file.write_bytes(b"PK0000fake")

    with (
        patch(
            "sys.argv",
            [
                "thesisforge",
                "export-docx",
                "--project-id",
                "proj-cli-01",
                "--output",
                str(fake_file),
                "--author",
                "Mario Vargas",
            ],
        ),
        patch(
            "thesisforge.export.service.ExportService.save_project_docx", new_callable=AsyncMock
        ) as mock_save,
        patch("thesisforge.repository.database.DatabaseManager.initialize", new_callable=AsyncMock),
        patch("thesisforge.repository.database.DatabaseManager.close", new_callable=AsyncMock),
    ):
        mock_save.return_value = fake_file
        main()

        captured = capsys.readouterr()
        assert "Documento APA 7 compilado exitosamente" in captured.out


def test_cli_draft_init_command(capsys: pytest.CaptureFixture[str]):
    """Test CLI draft-init subcommand."""
    with (
        patch(
            "sys.argv",
            ["thesisforge", "draft-init", "--project-id", "proj-cli-02"],
        ),
        patch(
            "thesisforge.drafting.service.DraftService.initialize_thesis_sections",
            new_callable=AsyncMock,
        ) as mock_init,
        patch("thesisforge.repository.database.DatabaseManager.initialize", new_callable=AsyncMock),
        patch("thesisforge.repository.database.DatabaseManager.close", new_callable=AsyncMock),
    ):
        mock_init.return_value = [
            SectionDraftDTO(
                section_id="sec_1_1",
                chapter_number=1,
                order_index=1,
                title="Planteamiento del Problema",
                status=SectionStatus.PENDING,
            )
        ]
        main()

        captured = capsys.readouterr()
        assert "Estructura capitular inicializada" in captured.out
        assert "sec_1_1" in captured.out


def test_cli_draft_list_command(capsys: pytest.CaptureFixture[str]):
    """Test CLI draft-list subcommand."""
    from thesisforge.models import ProjectStateDTO

    with (
        patch(
            "sys.argv",
            ["thesisforge", "draft-list", "--project-id", "proj-cli-03"],
        ),
        patch(
            "thesisforge.repository.project_repository.ProjectRepository.get_project",
            new_callable=AsyncMock,
        ) as mock_get,
        patch("thesisforge.repository.database.DatabaseManager.initialize", new_callable=AsyncMock),
        patch("thesisforge.repository.database.DatabaseManager.close", new_callable=AsyncMock),
    ):
        mock_get.return_value = ProjectStateDTO(
            id="proj-cli-03",
            title="Tesis de CLI",
            sections=[
                SectionDraftDTO(
                    section_id="sec_1_1",
                    chapter_number=1,
                    order_index=1,
                    title="Planteamiento",
                    status=SectionStatus.APPROVED,
                    word_count=450,
                )
            ],
        )
        main()

        captured = capsys.readouterr()
        assert "Secciones de tesis para el proyecto" in captured.out
        assert "450 palabras" in captured.out


def test_cli_export_bundle_command(capsys: pytest.CaptureFixture[str], tmp_path: Path):
    """Test CLI export-bundle subcommand."""
    fake_bundle = tmp_path / "backup.thesisforge"
    fake_bundle.write_bytes(b"PK0000fakebundle")

    with (
        patch(
            "sys.argv",
            [
                "thesisforge",
                "export-bundle",
                "--project-id",
                "proj-bundle-01",
                "--output",
                str(fake_bundle),
            ],
        ),
        patch(
            "thesisforge.export.bundle.ProjectBundleService.export_bundle_file",
            new_callable=AsyncMock,
        ) as mock_export,
        patch("thesisforge.repository.database.DatabaseManager.initialize", new_callable=AsyncMock),
        patch("thesisforge.repository.database.DatabaseManager.close", new_callable=AsyncMock),
    ):
        mock_export.return_value = fake_bundle
        main()

        captured = capsys.readouterr()
        assert "Paquete .thesisforge exportado exitosamente" in captured.out


def test_cli_import_bundle_command(capsys: pytest.CaptureFixture[str], tmp_path: Path):
    """Test CLI import-bundle subcommand."""
    fake_bundle = tmp_path / "backup.thesisforge"
    fake_bundle.write_bytes(b"PK0000fakebundle")
    from thesisforge.models import AcademicLevel, ProjectStateDTO

    with (
        patch(
            "sys.argv",
            [
                "thesisforge",
                "import-bundle",
                str(fake_bundle),
                "--new-id",
                "proj-restored-cli",
            ],
        ),
        patch(
            "thesisforge.export.bundle.ProjectBundleService.import_bundle_file",
            new_callable=AsyncMock,
        ) as mock_import,
        patch("thesisforge.repository.database.DatabaseManager.initialize", new_callable=AsyncMock),
        patch("thesisforge.repository.database.DatabaseManager.close", new_callable=AsyncMock),
    ):
        mock_import.return_value = ProjectStateDTO(
            id="proj-restored-cli",
            title="Proyecto Restaurado",
            academic_level=AcademicLevel.MAESTRIA,
        )
        main()

        captured = capsys.readouterr()
        assert "Proyecto importado exitosamente:" in captured.out
        assert "proj-restored-cli" in captured.out

