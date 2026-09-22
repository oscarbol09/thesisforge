"""CLI entry point for ThesisForge."""

import argparse
import asyncio
import sys

import uvicorn

from thesisforge import __version__
from thesisforge.config import get_settings
from thesisforge.drafting.service import DraftService
from thesisforge.export.service import ExportService
from thesisforge.models import CitationDTO, ExportOptionsDTO
from thesisforge.rag.apa_formatter import APA7Formatter
from thesisforge.rag.clients.aggregator import AcademicSearchAggregator
from thesisforge.rag.clients.arxiv import ArxivClient
from thesisforge.rag.clients.crossref import CrossRefClient
from thesisforge.rag.clients.semantic_scholar import SemanticScholarClient
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


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


async def _run_export_docx_cli(
    project_id: str,
    output_path: str,
    author: str = "",
    institution: str = "",
    advisor: str = "",
) -> None:
    """Compile and export project to Word (.docx) APA 7."""
    settings = get_settings()
    db = DatabaseManager(settings.database_url)
    await db.initialize()
    try:
        repo = ProjectRepository(db)
        export_service = ExportService(db_manager=db, project_repo=repo)
        opts = ExportOptionsDTO(
            author_name=author,
            institution_name=institution,
            advisor_name=advisor,
        )
        saved = await export_service.save_project_docx(project_id, output_path, opts)
        size_kb = saved.stat().st_size / 1024
        print(f"Documento APA 7 compilado exitosamente: {saved} ({size_kb:.1f} KB)")
    finally:
        await db.close()


async def _run_draft_init_cli(project_id: str) -> None:
    """Initialize canonical 5-chapter thesis outline."""
    settings = get_settings()
    db = DatabaseManager(settings.database_url)
    await db.initialize()
    try:
        repo = ProjectRepository(db)
        draft_service = DraftService(db_manager=db, project_repo=repo)
        sections = await draft_service.initialize_thesis_sections(project_id)
        print(f"Estructura capitular inicializada ({len(sections)} secciones creadas):")
        for s in sections:
            print(f"  [Cap. {s.chapter_number}] {s.section_id}: {s.title} ({s.status.value})")
    finally:
        await db.close()


async def _run_draft_list_cli(project_id: str) -> None:
    """List all sections belonging to a project."""
    settings = get_settings()
    db = DatabaseManager(settings.database_url)
    await db.initialize()
    try:
        repo = ProjectRepository(db)
        project = await repo.get_project(project_id)
        if not project:
            print(f"Proyecto '{project_id}' no encontrado.")
            return

        print(
            f"\nSecciones de tesis para el proyecto: '{project.title}' (ID: {project.id})\n"
            + "=" * 70
        )
        sorted_sections = sorted(project.sections, key=lambda s: (s.chapter_number, s.order_index))
        if not sorted_sections:
            print("  No hay secciones inicializadas aún. Ejecute 'draft-init' primero.")
            return

        for s in sorted_sections:
            words = f"{s.word_count} palabras"
            print(
                f"  [Cap. {s.chapter_number}] {s.section_id:<12} | {s.status.value:<12} | {words:<14} | {s.title}"
            )
        print("=" * 70)
    finally:
        await db.close()


async def _run_jury_audit_cli(project_id: str) -> None:
    """Execute scientific jury audit from CLI and display formatted report."""
    settings = get_settings()
    db = DatabaseManager(settings.database_url)
    await db.initialize()
    try:
        from thesisforge.jury.service import JuryService
        from thesisforge.repository.jury_repository import JuryRepository

        repo = ProjectRepository(db)
        jury_repo = JuryRepository(db)
        jury_service = JuryService(db_manager=db, project_repo=repo, jury_repo=jury_repo)

        print(f"\nEjecutando auditoría del Tribunal Académico para el proyecto '{project_id}'...")
        report = await jury_service.audit_project(project_id)

        print("\n" + "=" * 70)
        print(f"DICTAMEN OFICIAL DEL TRIBUNAL ACADÉMICO (ThesisForge v{__version__})")
        print("=" * 70)
        print(f"Calificación Global: {report.overall_score:.1f} / 100.0")
        print(f"Veredicto:           {report.verdict.value.upper()}")
        print(f"Dictamen Síntesis:   {report.summary_dictamen}")
        print("\n--- EVALUACIONES POR MIEMBRO DEL TRIBUNAL ---")
        for je in report.juror_evaluations:
            print(f"\n• {je.juror_name} ({je.juror_role.value}) — {je.score:.1f}/100")
            print(f"  Dimensión: {je.dimension_name}")
            print(f"  Criterio:  {je.criteria_evaluation}")
            print(f"  Feedback:  {je.feedback}")
            if je.flaws:
                print(f"  Objeciones: {', '.join(je.flaws)}")

        if report.issues:
            print("\n--- DEFECTOS E INCONSISTENCIAS DETECTADAS ---")
            for idx, issue in enumerate(report.issues, start=1):
                print(f"[{idx}] [{issue.severity.value.upper()}] {issue.title} ({issue.chapter_or_section})")
                print(f"    Descripción: {issue.description}")
                print(f"    Corrección:  {issue.recommendation}")

        if report.mandatory_fixes:
            print("\n--- MODIFICACIONES OBLIGATORIAS PARA APROBACIÓN ---")
            for fix in report.mandatory_fixes:
                print(f"  * {fix}")

        print("=" * 70 + "\n")
    finally:
        await db.close()


async def _run_defense_start_cli(project_id: str) -> None:
    """Launch interactive thesis oral defense session in console."""
    settings = get_settings()
    db = DatabaseManager(settings.database_url)
    await db.initialize()
    try:
        from thesisforge.jury.service import JuryService
        from thesisforge.repository.jury_repository import JuryRepository

        repo = ProjectRepository(db)
        jury_repo = JuryRepository(db)
        jury_service = JuryService(db_manager=db, project_repo=repo, jury_repo=jury_repo)

        session = await jury_service.start_defense_session(project_id)
        project = await repo.get_project(project_id)

        print("\n" + "=" * 70)
        print(f"TRIBUNAL DE SUSTENTACIÓN ORAL DE TESIS — NIVEL {project.academic_level.value.upper()}")
        print(f"Proyecto: '{project.title}' (ID: {project.id})")
        print(f"Sesión:   {session.id} ({session.total_turns} rondas de preguntas)")
        print("=" * 70)

        while session.current_turn_index < session.total_turns:
            turn = session.turns[session.current_turn_index]
            print(f"\n[Ronda {turn.turn_index + 1}/{session.total_turns}] {turn.juror_name} ({turn.juror_role.value})")
            print(f"Área: {turn.focus_area}")
            print(f'Pregunta: "{turn.question}"')
            print("-" * 70)

            # Check if running interactively
            try:
                answer = input("\nIngrese su argumentación y réplica oral (o 'exit' para pausar):\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nSustentación pausada por el usuario.")
                break

            if not answer or answer.lower() == "exit":
                print("Sesión guardada. Puede continuar en cualquier momento con el mismo comando.")
                break

            session = await jury_service.submit_defense_answer(
                session_id=session.id,
                turn_index=turn.turn_index,
                student_answer=answer,
            )

            answered_turn = session.turns[turn.turn_index]
            print(f"\nRetroalimentación del Jurado (Calificación: {answered_turn.turn_score:.1f}/100):")
            print(f'"{answered_turn.juror_feedback}"')
            print("=" * 70)

        if session.current_turn_index >= session.total_turns:
            print("\n" + "=" * 70)
            print("VEREDICTO FINAL DE LA SUSTENTACIÓN ORAL DE TESIS")
            print("=" * 70)
            print(f"Calificación Final de Defensa: {session.final_score:.1f} / 100.0")
            print(f"Resultado Oficial:             {session.final_verdict.value.upper() if session.final_verdict else 'N/A'}")
            print(f"Observaciones del Tribunal:    {session.final_remarks}")
            print("=" * 70 + "\n")
    finally:
        await db.close()


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

    # export-docx command
    export_parser = subparsers.add_parser(
        "export-docx",
        help="Compile and export a thesis project into APA 7th Edition Word document (.docx)",
    )
    export_parser.add_argument(
        "--project-id", type=str, required=True, help="ID of the research project"
    )
    export_parser.add_argument("--output", type=str, required=True, help="Target .docx file path")
    export_parser.add_argument("--author", type=str, default="", help="Author / Student name")
    export_parser.add_argument("--institution", type=str, default="", help="Institution name")
    export_parser.add_argument("--advisor", type=str, default="", help="Advisor name")

    # draft-init command
    init_parser = subparsers.add_parser(
        "draft-init",
        help="Initialize canonical 5-chapter outline sections for a thesis project",
    )
    init_parser.add_argument(
        "--project-id", type=str, required=True, help="ID of the research project"
    )

    # draft-list command
    list_parser = subparsers.add_parser(
        "draft-list",
        help="List all chapter sections and draft statuses for a project",
    )
    list_parser.add_argument(
        "--project-id", type=str, required=True, help="ID of the research project"
    )

    # jury-audit command
    jury_parser = subparsers.add_parser(
        "jury-audit",
        help="Run comprehensive scientific jury evaluation and bias audit on a project",
    )
    jury_parser.add_argument(
        "--project-id", type=str, required=True, help="ID of the research project"
    )

    # defense-start command
    defense_parser = subparsers.add_parser(
        "defense-start",
        help="Start interactive oral thesis defense simulation with the academic jury",
    )
    defense_parser.add_argument(
        "--project-id", type=str, required=True, help="ID of the research project"
    )

    args = parser.parse_args()
    settings = get_settings()

    if args.command == "search-papers":
        format_apa = args.format_type == "apa"
        asyncio.run(_run_search_cli(query=args.query, limit=args.limit, format_apa=format_apa))
    elif args.command == "export-docx":
        asyncio.run(
            _run_export_docx_cli(
                project_id=args.project_id,
                output_path=args.output,
                author=args.author,
                institution=args.institution,
                advisor=args.advisor,
            )
        )
    elif args.command == "draft-init":
        asyncio.run(_run_draft_init_cli(project_id=args.project_id))
    elif args.command == "draft-list":
        asyncio.run(_run_draft_list_cli(project_id=args.project_id))
    elif args.command == "jury-audit":
        asyncio.run(_run_jury_audit_cli(project_id=args.project_id))
    elif args.command == "defense-start":
        asyncio.run(_run_defense_start_cli(project_id=args.project_id))
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
