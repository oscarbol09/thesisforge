"""Unit tests for ThesisForge CLI entrypoint."""

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest

from thesisforge.cli import main
from thesisforge.config import get_settings
from thesisforge.models import (
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
    db_file = tmp_path / "cli_test.db"
    url = f"sqlite+aiosqlite:///{db_file}"
    # Clear settings cache so the CLI picks up the new environment variable
    get_settings.cache_clear()
    return url


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
        assert "Quantum" in captured.out
        assert "Algorithms" in captured.out
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


def test_cli_export_docx_command(capsys: pytest.CaptureFixture[str], tmp_path: Path, cli_db_url: str):
    """Test CLI export-docx subcommand."""
    project = ProjectStateDTO(id="proj-cli-01", title="Test CLI Docx")

    async def setup_db():
        db = DatabaseManager(cli_db_url)
        await db.initialize()
        repo = ProjectRepository(db, "local")
        await repo.create_project(project)
        await db.close()

    asyncio.run(setup_db())

    out_file = tmp_path / "output.docx"

    with (
        patch.dict("os.environ", {"THESISFORGE_DATABASE_URL": cli_db_url}),
        patch(
            "sys.argv",
            [
                "thesisforge",
                "export-docx",
                "--project-id",
                "proj-cli-01",
                "--output",
                str(out_file),
                "--author",
                "Mario Vargas",
            ],
        ),
    ):
        main()

        captured = capsys.readouterr()
        assert "Documento APA 7 compilado exitosamente" in captured.out
        assert out_file.exists()


def test_cli_draft_init_command(capsys: pytest.CaptureFixture[str], tmp_path: Path, cli_db_url: str):
    """Test CLI draft-init subcommand."""
    project = ProjectStateDTO(id="proj-cli-02", title="Test CLI Init")

    async def setup_db():
        db = DatabaseManager(cli_db_url)
        await db.initialize()
        repo = ProjectRepository(db, "local")
        await repo.create_project(project)
        await db.close()

    asyncio.run(setup_db())

    with (
        patch.dict("os.environ", {"THESISFORGE_DATABASE_URL": cli_db_url}),
        patch(
            "sys.argv",
            ["thesisforge", "draft-init", "--project-id", "proj-cli-02"],
        ),
    ):
        main()

        captured = capsys.readouterr()
        assert "Estructura Capitular Inicializada" in captured.out


def test_cli_draft_list_command(capsys: pytest.CaptureFixture[str], tmp_path: Path, cli_db_url: str):
    """Test CLI draft-list subcommand."""
    project = ProjectStateDTO(
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

    async def setup_db():
        db = DatabaseManager(cli_db_url)
        await db.initialize()
        repo = ProjectRepository(db, "local")
        await repo.create_project(project)
        await db.close()

    asyncio.run(setup_db())

    with (
        patch.dict("os.environ", {"THESISFORGE_DATABASE_URL": cli_db_url}),
        patch(
            "sys.argv",
            ["thesisforge", "draft-list", "--project-id", "proj-cli-03"],
        ),
    ):
        main()

        captured = capsys.readouterr()
        assert "Secciones de tesis para el proyecto" in captured.out
        assert "450 palabras" in captured.out


def test_cli_export_bundle_command(capsys: pytest.CaptureFixture[str], tmp_path: Path, cli_db_url: str):
    """Test CLI export-bundle subcommand."""
    project = ProjectStateDTO(id="proj-bundle-01", title="Test Bundle Export")

    async def setup_db():
        db = DatabaseManager(cli_db_url)
        await db.initialize()
        repo = ProjectRepository(db, "local")
        await repo.create_project(project)
        await db.close()

    asyncio.run(setup_db())

    fake_bundle = tmp_path / "backup.thesisforge"

    with (
        patch.dict("os.environ", {"THESISFORGE_DATABASE_URL": cli_db_url}),
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
    ):
        main()

        captured = capsys.readouterr()
        assert "Paquete .thesisforge exportado exitosamente" in captured.out
        assert fake_bundle.exists()


def test_cli_import_bundle_command(capsys: pytest.CaptureFixture[str], tmp_path: Path, cli_db_url: str):
    """Test CLI import-bundle subcommand."""
    project = ProjectStateDTO(id="proj-bundle-source", title="Source Project")

    source_db_url = f"sqlite+aiosqlite:///{tmp_path}/source.db"
    async def setup_source_db():
        db = DatabaseManager(source_db_url)
        await db.initialize()
        repo = ProjectRepository(db, "local")
        await repo.create_project(project)
        from thesisforge.export.bundle import ProjectBundleService
        bundle_service = ProjectBundleService(project_repo=repo)
        path = await bundle_service.export_bundle_file("proj-bundle-source", str(tmp_path / "backup.thesisforge"))
        await db.close()
        return path

    bundle_path = asyncio.run(setup_source_db())

    async def init_dest_db():
        db = DatabaseManager(cli_db_url)
        await db.initialize()
        await db.close()

    asyncio.run(init_dest_db())

    with (
        patch.dict("os.environ", {"THESISFORGE_DATABASE_URL": cli_db_url}),
        patch(
            "sys.argv",
            [
                "thesisforge",
                "import-bundle",
                str(bundle_path),
                "--new-id",
                "proj-restored-cli",
            ],
        ),
    ):
        main()

        captured = capsys.readouterr()
        assert "Proyecto importado exitosamente" in captured.out
        assert "proj-restored-cli" in captured.out
