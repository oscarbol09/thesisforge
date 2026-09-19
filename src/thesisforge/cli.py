"""CLI entry point for ThesisForge."""

import argparse
import sys

import uvicorn

from thesisforge import __version__
from thesisforge.config import get_settings


def main() -> None:
    """Main CLI entrypoint for ThesisForge."""
    parser = argparse.ArgumentParser(
        prog="thesisforge",
        description="ThesisForge 🔨 — Asistente y Forjador de Investigación Académica con IA, RAG y BYOK.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"ThesisForge v{__version__}",
        help="Show version and exit.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # run command
    run_parser = subparsers.add_parser("run", help="Start the ThesisForge API & Web server")
    run_parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host address to bind to (default: from config/env, typically 127.0.0.1)",
    )
    run_parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind to (default: from config/env, typically 8000)",
    )
    run_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    args = parser.parse_args()
    settings = get_settings()

    if args.command == "run" or args.command is None:
        host = args.host or settings.host
        port = args.port or settings.port
        reload = (
            bool(args.reload)
            if (hasattr(args, "reload") and args.reload)
            else (settings.environment == "development")
        )

        print(f"🔨 Starting ThesisForge v{__version__} on http://{host}:{port}")
        uvicorn.run(
            "thesisforge.api.app:app",
            host=host,
            port=port,
            reload=reload,
        )
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
