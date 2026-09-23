"""Desktop launcher embedding FastAPI within PyWebView native window."""

import socket
import threading
import time
import urllib.error
import urllib.request
from typing import Any

import uvicorn

from thesisforge.core.logging import get_logger

logger = get_logger(__name__)


def find_available_port(host: str = "127.0.0.1", default_port: int = 8000) -> int:
    """Find an available TCP port on the loopback interface."""
    # First, test if default_port is available
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, default_port))
            return default_port
        except OSError:
            pass

    # Fallback to OS-assigned ephemeral port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        s.listen(1)
        port = s.getsockname()[1]
        return int(port)


def wait_for_server(host: str, port: int, timeout_seconds: float = 12.0) -> bool:
    """Poll the /health endpoint until FastAPI is ready to receive requests."""
    start_time = time.monotonic()
    health_url = f"http://{host}:{port}/health"

    while time.monotonic() - start_time < timeout_seconds:
        try:
            req = urllib.request.Request(health_url, headers={"User-Agent": "ThesisForge-Launcher"})
            with urllib.request.urlopen(req, timeout=1.0) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            time.sleep(0.15)

    return False


def start_server_thread(host: str, port: int, log_level: str = "warning") -> threading.Thread:
    """Start Uvicorn server in a background daemon thread."""
    config = uvicorn.Config(
        app="thesisforge.api.app:app",
        host=host,
        port=port,
        log_level=log_level,
        access_log=False,
    )
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True, name="ThesisForge-UvicornServer")
    thread.start()
    return thread


def launch_desktop(
    host: str = "127.0.0.1",
    port: int = 0,
    debug: bool = False,
    title: str = "ThesisForge — Asistente de Investigación Académica",
    width: int = 1280,
    height: int = 820,
) -> None:
    """Launch the ThesisForge SPA inside a native PyWebView desktop container."""
    try:
        import webview
    except ImportError as err:
        raise ImportError(
            "El paquete 'pywebview' no está instalado. Instálalo con: pip install pywebview"
        ) from err

    resolved_port = port if port > 0 else find_available_port(host=host)
    logger.info("Starting ThesisForge background server on http://%s:%s", host, resolved_port)

    # Launch background Uvicorn thread
    start_server_thread(host=host, port=resolved_port)

    # Wait for server readiness
    is_ready = wait_for_server(host=host, port=resolved_port)
    if not is_ready:
        logger.error("Timed out waiting for FastAPI server startup on port %d", resolved_port)
        raise RuntimeError(
            f"El servidor FastAPI no respondió a tiempo en el puerto {resolved_port}."
        )

    app_url = f"http://{host}:{resolved_port}"
    logger.info("Opening PyWebView native container at %s", app_url)

    window_kwargs: dict[str, Any] = {
        "title": title,
        "url": app_url,
        "width": width,
        "height": height,
        "min_size": (920, 620),
        "text_select": True,
    }

    # Open PyWebView native GUI window
    webview.create_window(**window_kwargs)
    webview.start(debug=debug)
