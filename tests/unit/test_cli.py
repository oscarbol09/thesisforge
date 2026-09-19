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
