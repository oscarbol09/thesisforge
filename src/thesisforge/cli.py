"""CLI entry point for ThesisForge."""

import argparse
import asyncio
import sys

import uvicorn

from thesisforge import __version__
from thesisforge.config import get_settings
from thesisforge.models import CitationDTO
from thesisforge.rag.apa_formatter import APA7Formatter
from thesisforge.rag.clients.aggregator import AcademicSearchAggregator
from thesisforge.rag.clients.arxiv import ArxivClient
from thesisforge.rag.clients.crossref import CrossRefClient
from thesisforge.rag.clients.semantic_scholar import SemanticScholarClient


async def _run_search_cli(query: str, limit: int, format_apa: bool) -> None:
    """Execute asynchronous paper search from CLI."""
    ss = SemanticScholarClient()
    arxiv = ArxivClient()
    cr = CrossRefClient()
    aggregator = AcademicSearchAggregator(ss, arxiv, cr)

    try:
        results = await aggregator.search(query=query, limit_per_source=limit)
        if not results:
            print(f"No se encontraron publicaciones académicas para '{query}'.")
            return

        print(f"\nResultados encontrados para: '{query}' ({len(results)} artículos):\n" + "=" * 60)
        for idx, paper in enumerate(results[:limit], start=1):
            if format_apa:
                cit = CitationDTO(
                    doi=paper.doi,
                    title=paper.title,
                    authors=paper.authors,
                    year=paper.year or 2024,
                    journal=paper.venue,
                    abstract=paper.abstract,
                    url=paper.url,
                    source=paper.source,
                )
                print(f"[{idx}] {APA7Formatter.format_reference_entry(cit)}")
            else:
                authors_str = ", ".join(paper.authors[:3]) + (
                    " et al." if len(paper.authors) > 3 else ""
                )
                year_str = f"({paper.year})" if paper.year else "(s.f.)"
                print(f"[{idx}] {paper.title} — {authors_str} {year_str}")
                if paper.doi:
                    print(f"    DOI: https://doi.org/{paper.doi}")
                if paper.open_access_pdf:
                    print(f"    PDF: {paper.open_access_pdf}")
            print("-" * 60)
    finally:
        await ss.close()
        await arxiv.close()
        await cr.close()


def main() -> None:
    """Main CLI entrypoint for ThesisForge."""
    parser = argparse.ArgumentParser(
        prog="thesisforge",
        description="ThesisForge — Asistente y Forjador de Investigación Académica con IA, RAG y BYOK.",
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

    # search-papers command
    search_parser = subparsers.add_parser(
        "search-papers",
        help="Search academic literature across Semantic Scholar, ArXiv and CrossRef",
    )
    search_parser.add_argument("query", type=str, help="Search query or research topic")
    search_parser.add_argument(
        "--limit", type=int, default=5, help="Maximum number of papers to display (default: 5)"
    )
    search_parser.add_argument(
        "--format",
        dest="format_type",
        choices=["standard", "apa"],
        default="standard",
        help="Output format: standard or apa",
    )

    args = parser.parse_args()
    settings = get_settings()

    if args.command == "search-papers":
        format_apa = args.format_type == "apa"
        asyncio.run(_run_search_cli(query=args.query, limit=args.limit, format_apa=format_apa))
    elif args.command == "run" or args.command is None:
        host = args.host or settings.host
        port = args.port or settings.port
        reload = (
            bool(args.reload)
            if (hasattr(args, "reload") and args.reload)
            else (settings.environment == "development")
        )

        print(f"Starting ThesisForge v{__version__} on http://{host}:{port}")
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
