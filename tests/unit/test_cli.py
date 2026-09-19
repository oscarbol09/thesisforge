"""Unit tests for ThesisForge CLI entrypoint."""

from unittest.mock import patch

import pytest

from thesisforge.cli import main


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
