"""Unit tests for PyWebView desktop launcher and port resolution."""

import socket
import sys
from unittest.mock import MagicMock, patch

import pytest

from thesisforge.cli import main
from thesisforge.desktop.launcher import (
    find_available_port,
    launch_desktop,
    wait_for_server,
)


def test_find_available_port_returns_valid_port() -> None:
    """Verify that find_available_port returns an integer port on loopback."""
    port = find_available_port(host="127.0.0.1")
    assert isinstance(port, int)
    assert 1024 <= port <= 65535

    # Ensure the returned port can actually be bound
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", port))
        assert s.getsockname()[1] == port


def test_wait_for_server_timeout_on_unreachable_port() -> None:
    """Verify wait_for_server returns False when polling an inactive port."""
    # Find an unused port and don't start any server on it
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        unused_port = s.getsockname()[1]

    is_ready = wait_for_server(host="127.0.0.1", port=unused_port, timeout_seconds=0.3)
    assert is_ready is False


def test_launch_desktop_missing_webview_raises_importerror() -> None:
    """Verify launch_desktop raises a clear ImportError when pywebview is not installed."""
    with (
        patch.dict(sys.modules, {"webview": None}),
        pytest.raises(ImportError, match="pywebview"),
    ):
        launch_desktop(host="127.0.0.1", port=8999)


def test_launch_desktop_successful_orchestration() -> None:
    """Verify launch_desktop starts background server and initializes webview window."""
    mock_webview = MagicMock()
    mock_window = MagicMock()
    mock_webview.create_window.return_value = mock_window

    with (
        patch.dict(sys.modules, {"webview": mock_webview}),
        patch("thesisforge.desktop.launcher.start_server_thread") as mock_start_server,
        patch("thesisforge.desktop.launcher.wait_for_server", return_value=True) as mock_wait,
    ):
        launch_desktop(host="127.0.0.1", port=9123, debug=True)

        mock_start_server.assert_called_once_with(host="127.0.0.1", port=9123)
        mock_wait.assert_called_once_with(host="127.0.0.1", port=9123)
        mock_webview.create_window.assert_called_once()
        mock_webview.start.assert_called_once_with(debug=True)


def test_cli_gui_subcommand_dispatch() -> None:
    """Verify that CLI 'gui' subcommand calls launch_desktop with parsed arguments."""
    with (
        patch("sys.argv", ["thesisforge", "gui", "--port", "8888", "--debug"]),
        patch("thesisforge.desktop.launcher.launch_desktop") as mock_launch,
    ):
        main()
        mock_launch.assert_called_once_with(
            host="127.0.0.1",
            port=8888,
            debug=True,
        )
