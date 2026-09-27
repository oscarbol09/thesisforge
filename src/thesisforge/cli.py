"""CLI entry point for ThesisForge with Rich terminal UI, spinners, and formatted tables."""

import argparse
import asyncio
import sys

import uvicorn
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from thesisforge import __version__
from thesisforge.config import get_settings
from thesisforge.core.time import utc_now
from thesisforge.drafting.service import DraftService
from thesisforge.exceptions import ThesisForgeError
from thesisforge.export.bundle import ProjectBundleService
from thesisforge.export.service import ExportService
from thesisforge.models import CitationDTO, ExportOptionsDTO, SectionStatus
from thesisforge.rag.apa_formatter import APA7Formatter
from thesisforge.rag.clients.aggregator import AcademicSearchAggregator
from thesisforge.rag.clients.arxiv import ArxivClient
from thesisforge.rag.clients.crossref import CrossRefClient
from thesisforge.rag.clients.openalex import OpenAlexClient
from thesisforge.rag.clients.semantic_scholar import SemanticScholarClient
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository

console = Console()
err_console = Console(stderr=True)


async def _run_search_cli(
    query: str,
    limit: int,
    format_apa: bool,
    sources: list[str] | None = None,
) -> None:
    """Execute asynchronous paper search from CLI with Rich status spinner and tabular output."""
    ss = SemanticScholarClient()
    arxiv = ArxivClient()
    cr = CrossRefClient()
    oa = OpenAlexClient()
    aggregator = AcademicSearchAggregator(ss, arxiv, cr, oa)

    try:
        with console.status(
            f"[bold cyan]Consultando repositorios académicos para '{query}'...[/bold cyan]",
            spinner="dots",
        ):
            results = await aggregator.search(
                query=query,
                limit_per_source=limit,
                sources=sources,
            )

        if not results:
            console.print(
                f"\n[yellow]No se encontraron publicaciones académicas para '{query}'.[/yellow]\n"
            )
            return

        if format_apa:
            console.print(
                f"\n[bold green]Resultados encontrados para:[/bold green] '{query}' ({len(results)} artículos):\n"
            )
            for idx, paper in enumerate(results[:limit], start=1):
                cit = CitationDTO(
                    doi=paper.doi,
                    title=paper.title,
                    authors=paper.authors,
                    year=paper.year or utc_now().year,
                    journal=paper.venue,
                    abstract=paper.abstract,
                    url=paper.url,
                    source=paper.source,
                )
                console.print(
                    f"[bold cyan][{idx}][/bold cyan] {APA7Formatter.format_reference_entry(cit)}"
                )
                console.print("[dim]" + "─" * 70 + "[/dim]")
        else:
            table = Table(
                title=f"Resultados de Literatura Científica — '{query}' ({len(results)} artículos)",
                box=box.ROUNDED,
                show_lines=True,
                header_style="bold blue",
            )
            table.add_column("#", justify="center", style="bold cyan", no_wrap=True)
            table.add_column("Título", style="bold white", max_width=45)
            table.add_column("Autores", style="italic", max_width=25)
            table.add_column("Año", justify="center", style="yellow")
            table.add_column("Fuente", justify="center", style="magenta")
            table.add_column("DOI / Acceso", style="blue", max_width=30)

            for idx, paper in enumerate(results[:limit], start=1):
                authors_str = ", ".join(paper.authors[:2]) + (
                    " et al." if len(paper.authors) > 2 else ""
                )
                year_str = str(paper.year) if paper.year else "s.f."
                doi_or_url = (
                    f"DOI: {paper.doi}"
                    if paper.doi
                    else (paper.open_access_pdf or paper.url or "N/A")
                )
                table.add_row(
                    str(idx),
                    paper.title,
                    authors_str or "Desconocido",
                    year_str,
                    paper.source or "académico",
                    doi_or_url,
                )
            console.print(table)
    finally:
        await ss.close()
        await arxiv.close()
        await cr.close()
        await oa.close()


async def _run_export_docx_cli(
    project_id: str,
    output_path: str,
    author: str = "",
    institution: str = "",
    advisor: str = "",
) -> None:
    """Compile and export project to Word (.docx) APA 7 with Rich progress indicator."""
    settings = get_settings()
    db = DatabaseManager(settings.database_url)
    await db.initialize()
    try:
        repo = ProjectRepository(db, "local")
        export_service = ExportService(db_manager=db, project_repo=repo)
        opts = ExportOptionsDTO(
            author_name=author,
            institution_name=institution,
            advisor_name=advisor,
        )
        with console.status(
            "[bold cyan]Compilando manuscrito APA 7ª Edición (.docx)...[/bold cyan]",
            spinner="dots",
        ):
            saved = await export_service.save_project_docx(project_id, output_path, opts)

        size_kb = saved.stat().st_size / 1024
        console.print(
            Panel(
                f"[bold green]✓ Documento APA 7 compilado exitosamente[/bold green]\n\n"
                f"[bold]Archivo destino:[/bold]  {saved}\n"
                f"[bold]Tamaño generado:[/bold]  {size_kb:.1f} KB\n"
                f"[bold]Formato:[/bold]            Microsoft Word (.docx) APA 7",
                title="[bold blue]ThesisForge — Exportación Editorial[/bold blue]",
                box=box.ROUNDED,
            )
        )
    finally:
        await db.close()


async def _run_export_bib_cli(
    project_id: str,
    output_path: str | None = None,
) -> None:
    """Compile and export project citations to BibTeX (.bib) file or stdout."""
    settings = get_settings()
    db = DatabaseManager(settings.database_url)
    await db.initialize()
    try:
        repo = ProjectRepository(db, "local")
        export_service = ExportService(db_manager=db, project_repo=repo)
        with console.status(
            "[bold cyan]Compilando bibliografía BibTeX (.bib)...[/bold cyan]",
            spinner="dots",
        ):
            if output_path:
                saved = await export_service.save_project_bibtex(project_id, output_path)
                size_kb = saved.stat().st_size / 1024
                console.print(
                    Panel(
                        f"[bold green]✓ Bibliografía BibTeX exportada exitosamente[/bold green]\n\n"
                        f"[bold]Archivo destino:[/bold]  {saved}\n"
                        f"[bold]Tamaño generado:[/bold]  {size_kb:.1f} KB\n"
                        f"[bold]Compatibilidad:[/bold]   Overleaf, Zotero, Mendeley, JabRef",
                        title="[bold blue]ThesisForge — Exportación BibTeX[/bold blue]",
                        box=box.ROUNDED,
                    )
                )
            else:
                bib_text = await export_service.compile_project_bibtex(project_id)
                console.print(bib_text)
    finally:
        await db.close()


async def _run_export_bundle_cli(
    project_id: str,
    output_path: str,
) -> None:
    """Export self-contained .thesisforge project archive with Rich status indicator."""
    settings = get_settings()
    db = DatabaseManager(settings.database_url)
    await db.initialize()
    try:
        repo = ProjectRepository(db, "local")
        bundle_service = ProjectBundleService(project_repo=repo)
        with console.status(
            "[bold cyan]Empaquetando archivo de proyecto (.thesisforge)...[/bold cyan]",
            spinner="dots",
        ):
            saved = await bundle_service.export_bundle_file(project_id, output_path)

        size_kb = saved.stat().st_size / 1024
        console.print(
            Panel(
                f"[bold green]✓ Paquete .thesisforge exportado exitosamente[/bold green]\n\n"
                f"[bold]Destino:[/bold] {saved}\n"
                f"[bold]Tamaño:[/bold]  {size_kb:.1f} KB",
                title="[bold blue]ThesisForge — Backup Bundle[/bold blue]",
                box=box.ROUNDED,
            )
        )
    finally:
        await db.close()


async def _run_import_bundle_cli(
    file_path: str,
    new_project_id: str | None = None,
) -> None:
    """Import self-contained .thesisforge project archive with Rich output."""
    settings = get_settings()
    db = DatabaseManager(settings.database_url)
    await db.initialize()
    try:
        repo = ProjectRepository(db, "local")
        bundle_service = ProjectBundleService(project_repo=repo)
        with console.status(
            "[bold cyan]Validando y restaurando proyecto desde archivo...[/bold cyan]",
            spinner="dots",
        ):
            project = await bundle_service.import_bundle_file(
                file_path, new_project_id=new_project_id
            )

        console.print(
            Panel(
                f"[bold green]✓ Proyecto importado exitosamente[/bold green]\n\n"
                f"[bold]ID:[/bold]     {project.id}\n"
                f"[bold]Título:[/bold] {project.title}\n"
                f"[bold]Nivel:[/bold]  {project.academic_level.value}",
                title="[bold blue]ThesisForge — Restauración de Proyecto[/bold blue]",
                box=box.ROUNDED,
            )
        )
    finally:
        await db.close()


async def _run_draft_init_cli(project_id: str) -> None:
    """Initialize canonical 5-chapter thesis outline with Rich formatted table."""
    settings = get_settings()
    db = DatabaseManager(settings.database_url)
    await db.initialize()
    try:
        repo = ProjectRepository(db, "local")
        draft_service = DraftService(db_manager=db, project_repo=repo)
        with console.status(
            "[bold cyan]Inicializando estructura capitular canónica...[/bold cyan]",
            spinner="dots",
        ):
            sections = await draft_service.initialize_thesis_sections(project_id)

        table = Table(
            title=f"Estructura Capitular Inicializada ({len(sections)} secciones creadas)",
            box=box.ROUNDED,
            header_style="bold blue",
        )
        table.add_column("Cap.", justify="center", style="cyan")
        table.add_column("ID Sección", style="bold white")
        table.add_column("Estado", justify="center", style="dim")
        table.add_column("Título", style="italic")

        for s in sections:
            table.add_row(f"Cap. {s.chapter_number}", s.section_id, s.status.value, s.title)
        console.print(table)
    finally:
        await db.close()


async def _run_draft_list_cli(project_id: str) -> None:
    """List all sections belonging to a project with Rich table."""
    settings = get_settings()
    db = DatabaseManager(settings.database_url)
    await db.initialize()
    try:
        repo = ProjectRepository(db, "local")
        project = await repo.get_project(project_id)
        if not project:
            console.print(f"[bold red]Error:[/bold red] Proyecto '{project_id}' no encontrado.")
            return

        sorted_sections = sorted(project.sections, key=lambda s: (s.chapter_number, s.order_index))
        if not sorted_sections:
            console.print(
                "[yellow]No hay secciones inicializadas aún. Ejecute 'draft-init' primero.[/yellow]"
            )
            return

        table = Table(
            title=f"Secciones de tesis para el proyecto: '{project.title}' (ID: {project.id})",
            box=box.ROUNDED,
            show_lines=True,
            header_style="bold blue",
        )
        table.add_column("Cap.", justify="center", style="cyan", no_wrap=True)
        table.add_column("ID Sección", style="bold white", no_wrap=True)
        table.add_column("Estado", justify="center")
        table.add_column("Palabras", justify="right", style="yellow")
        table.add_column("Título de la Sección", style="italic")

        status_styles = {
            SectionStatus.APPROVED: "[bold green]approved[/bold green]",
            SectionStatus.READY_FOR_REVIEW: "[bold cyan]ready_for_review[/bold cyan]",
            SectionStatus.IN_PROGRESS: "[bold yellow]in_progress[/bold yellow]",
            SectionStatus.PENDING: "[dim]pending[/dim]",
        }

        for s in sorted_sections:
            status_label = status_styles.get(s.status, str(s.status.value))
            words = f"{s.word_count} palabras"
            table.add_row(
                f"Cap. {s.chapter_number}",
                s.section_id,
                status_label,
                words,
                s.title,
            )
        console.print(table)
    finally:
        await db.close()


async def _run_jury_audit_cli(project_id: str) -> None:
    """Execute scientific jury audit from CLI and display formatted Rich telemetry."""
    settings = get_settings()
    db = DatabaseManager(settings.database_url)
    await db.initialize()
    try:
        from thesisforge.jury.service import JuryService
        from thesisforge.repository.jury_repository import JuryRepository

        repo = ProjectRepository(db, "local")
        jury_repo = JuryRepository(db, "local")
        jury_service = JuryService(db_manager=db, project_repo=repo, jury_repo=jury_repo)

        with console.status(
            f"[bold cyan]Ejecutando auditoría del Tribunal Académico para el proyecto '{project_id}'...[/bold cyan]",
            spinner="dots",
        ):
            report = await jury_service.audit_project(project_id)

        verdict_style = {
            "aprobado_con_distincion": "[bold green]APROBADO CON DISTINCIÓN[/bold green]",
            "aprobado": "[bold green]APROBADO[/bold green]",
            "modificaciones_menores": "[bold yellow]MODIFICACIONES MENORES[/bold yellow]",
            "modificaciones_mayores": "[bold red]MODIFICACIONES MAYORES[/bold red]",
            "no_aprobado": "[bold red]NO APROBADO[/bold red]",
        }.get(report.verdict.value, report.verdict.value.upper())

        console.print(
            Panel(
                f"[bold]Calificación Global:[/bold] [bold cyan]{report.overall_score:.1f} / 100.0[/bold cyan]\n"
                f"[bold]Veredicto Oficial:[/bold]   {verdict_style}\n\n"
                f"[bold]Dictamen Síntesis:[/bold]\n{report.summary_dictamen}",
                title=f"[bold blue]DICTAMEN OFICIAL DEL TRIBUNAL ACADÉMICO (ThesisForge v{__version__})[/bold blue]",
                box=box.ROUNDED,
            )
        )

        eval_table = Table(
            title="Evaluaciones por Miembro del Tribunal",
            box=box.ROUNDED,
            show_lines=True,
            header_style="bold blue",
        )
        eval_table.add_column("Miembro", style="bold white")
        eval_table.add_column("Rol", style="cyan")
        eval_table.add_column("Dimensión", style="magenta")
        eval_table.add_column("Puntaje", justify="center", style="yellow")
        eval_table.add_column("Dictamen y Feedback", style="italic")

        for je in report.juror_evaluations:
            objections = f"\n[red]Objeciones: {', '.join(je.flaws)}[/red]" if je.flaws else ""
            eval_table.add_row(
                je.juror_name,
                je.juror_role.value,
                je.dimension_name,
                f"{je.score:.1f}/100",
                f"{je.feedback}{objections}",
            )
        console.print(eval_table)

        if report.issues:
            issue_table = Table(
                title="Defectos e Inconsistencias Metodológicas Detectadas",
                box=box.ROUNDED,
                show_lines=True,
                header_style="bold red",
            )
            issue_table.add_column("#", justify="center", style="bold cyan")
            issue_table.add_column("Severidad", justify="center")
            issue_table.add_column("Sección", style="dim")
            issue_table.add_column("Hallazgo", style="bold white")
            issue_table.add_column("Recomendación de Corrección", style="green")

            severity_map = {
                "critical": "[bold red][CRITICAL][/bold red]",
                "major": "[bold yellow][MAJOR][/bold yellow]",
                "minor": "[bold cyan][MINOR][/bold cyan]",
                "note": "[dim][NOTE][/dim]",
            }
            for idx, issue in enumerate(report.issues, start=1):
                sev = severity_map.get(issue.severity.value.lower(), issue.severity.value.upper())
                issue_table.add_row(
                    str(idx),
                    sev,
                    issue.chapter_or_section,
                    f"{issue.title}\n[dim]{issue.description}[/dim]",
                    issue.recommendation,
                )
            console.print(issue_table)

        if report.mandatory_fixes:
            console.print(
                "\n[bold red]─── MODIFICACIONES OBLIGATORIAS PARA APROBACIÓN ───[/bold red]"
            )
            for fix in report.mandatory_fixes:
                console.print(f"  [bold red]•[/bold red] {fix}")
            console.print("")
    finally:
        await db.close()


async def _run_defense_start_cli(project_id: str) -> None:
    """Launch interactive thesis oral defense session in console with Rich UI."""
    settings = get_settings()
    db = DatabaseManager(settings.database_url)
    await db.initialize()
    try:
        from thesisforge.jury.service import JuryService
        from thesisforge.repository.jury_repository import JuryRepository

        repo = ProjectRepository(db, "local")
        jury_repo = JuryRepository(db, "local")
        jury_service = JuryService(db_manager=db, project_repo=repo, jury_repo=jury_repo)

        session = await jury_service.start_defense_session(project_id)
        project = await repo.get_project(project_id)

        console.print(
            Panel(
                f"[bold]Proyecto:[/bold] '{project.title}' (ID: {project.id})\n"
                f"[bold]Nivel:[/bold]    {project.academic_level.value.upper()}\n"
                f"[bold]Sesión:[/bold]   {session.id} ({session.total_turns} rondas de sustentación)",
                title="[bold blue]TRIBUNAL DE SUSTENTACIÓN ORAL DE TESIS[/bold blue]",
                box=box.ROUNDED,
            )
        )

        while session.current_turn_index < session.total_turns:
            turn = session.turns[session.current_turn_index]
            console.print(
                Panel(
                    f'[bold]Pregunta del Jurado:[/bold]\n"{turn.question}"',
                    title=f"[bold cyan]Ronda {turn.turn_index + 1}/{session.total_turns} — {turn.juror_name} ({turn.juror_role.value}) • {turn.focus_area}[/bold cyan]",
                    box=box.ROUNDED,
                )
            )

            try:
                answer = input(
                    "\nIngrese su argumentación y réplica oral (o 'exit' para pausar):\n> "
                ).strip()
            except (EOFError, KeyboardInterrupt):
                console.print("\n[yellow]Sustentación pausada por el usuario.[/yellow]")
                break

            if not answer or answer.lower() == "exit":
                console.print(
                    "[yellow]Sesión guardada. Puede continuar en cualquier momento con el mismo comando.[/yellow]"
                )
                break

            with console.status(
                "[bold cyan]Evaluando respuesta de sustentación con el Jurado...[/bold cyan]",
                spinner="dots",
            ):
                session = await jury_service.submit_defense_answer(
                    session_id=session.id,
                    turn_index=turn.turn_index,
                    student_answer=answer,
                )

            answered_turn = session.turns[turn.turn_index]
            score_color = "green" if (answered_turn.turn_score or 0) >= 70 else "yellow"
            console.print(
                Panel(
                    f"[bold]Calificación de Ronda:[/bold] [{score_color}]{answered_turn.turn_score:.1f}/100[/{score_color}]\n\n"
                    f'[bold]Dictamen del Evaluador:[/bold]\n"{answered_turn.juror_feedback}"',
                    title="[bold blue]Retroalimentación Inmediata del Jurado[/bold blue]",
                    box=box.ROUNDED,
                )
            )

        if session.current_turn_index >= session.total_turns:
            console.print(
                Panel(
                    f"[bold]Calificación Final de Defensa:[/bold] [bold cyan]{session.final_score:.1f} / 100.0[/bold cyan]\n"
                    f"[bold]Resultado Oficial:[/bold]             [bold green]{session.final_verdict.value.upper() if session.final_verdict else 'N/A'}[/bold green]\n\n"
                    f"[bold]Observaciones del Tribunal:[/bold]    {session.final_remarks}",
                    title="[bold blue]VEREDICTO FINAL DE LA SUSTENTACIÓN ORAL DE TESIS[/bold blue]",
                    box=box.ROUNDED,
                )
            )
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
        help="Search academic literature across Semantic Scholar, OpenAlex, ArXiv and CrossRef",
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
        "project_id", nargs="?", default=None, help="ID of the research project"
    )
    export_parser.add_argument(
        "--project-id",
        dest="project_id_flag",
        type=str,
        default=None,
        help="ID of the research project",
    )
    export_parser.add_argument("--output", type=str, required=True, help="Target .docx file path")
    export_parser.add_argument("--author", type=str, default="", help="Author / Student name")
    export_parser.add_argument("--institution", type=str, default="", help="Institution name")
    export_parser.add_argument("--advisor", type=str, default="", help="Advisor name")

    # export-bib command
    export_bib_parser = subparsers.add_parser(
        "export-bib",
        help="Compile and export validated project citations into BibTeX (.bib) format for Zotero and Overleaf",
    )
    export_bib_parser.add_argument(
        "project_id", nargs="?", default=None, help="ID of the research project"
    )
    export_bib_parser.add_argument(
        "--project-id",
        dest="project_id_flag",
        type=str,
        default=None,
        help="ID of the research project",
    )
    export_bib_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Target .bib file path (optional; prints to standard output if omitted)",
    )

    # export-bundle command
    export_bundle_parser = subparsers.add_parser(
        "export-bundle",
        help="Export a full project backup bundle as a .thesisforge file",
    )
    export_bundle_parser.add_argument(
        "project_id", nargs="?", default=None, help="ID of the research project"
    )
    export_bundle_parser.add_argument(
        "--project-id",
        dest="project_id_flag",
        type=str,
        default=None,
        help="ID of the research project",
    )
    export_bundle_parser.add_argument(
        "--output", type=str, required=True, help="Target .thesisforge file path"
    )

    # import-bundle command
    import_bundle_parser = subparsers.add_parser(
        "import-bundle",
        help="Import a project from a .thesisforge backup bundle",
    )
    import_bundle_parser.add_argument("bundle_file", type=str, help="Path to .thesisforge archive")
    import_bundle_parser.add_argument(
        "--new-id",
        dest="new_project_id",
        type=str,
        default=None,
        help="Optional new project ID to assign during import",
    )

    # draft-init command
    init_parser = subparsers.add_parser(
        "draft-init",
        help="Initialize canonical 5-chapter outline sections for a thesis project",
    )
    init_parser.add_argument(
        "project_id", nargs="?", default=None, help="ID of the research project"
    )
    init_parser.add_argument(
        "--project-id",
        dest="project_id_flag",
        type=str,
        default=None,
        help="ID of the research project",
    )

    # draft-list command
    list_parser = subparsers.add_parser(
        "draft-list",
        help="List all chapter sections and draft statuses for a project",
    )
    list_parser.add_argument(
        "project_id", nargs="?", default=None, help="ID of the research project"
    )
    list_parser.add_argument(
        "--project-id",
        dest="project_id_flag",
        type=str,
        default=None,
        help="ID of the research project",
    )

    # jury-audit command
    jury_parser = subparsers.add_parser(
        "jury-audit",
        help="Run comprehensive scientific jury evaluation and bias audit on a project",
    )
    jury_parser.add_argument(
        "project_id", nargs="?", default=None, help="ID of the research project"
    )
    jury_parser.add_argument(
        "--project-id",
        dest="project_id_flag",
        type=str,
        default=None,
        help="ID of the research project",
    )

    # defense-start command
    defense_parser = subparsers.add_parser(
        "defense-start",
        help="Start interactive oral thesis defense simulation with the academic jury",
    )
    defense_parser.add_argument(
        "project_id", nargs="?", default=None, help="ID of the research project"
    )
    defense_parser.add_argument(
        "--project-id",
        dest="project_id_flag",
        type=str,
        default=None,
        help="ID of the research project",
    )

    # gui command
    gui_parser = subparsers.add_parser(
        "gui",
        help="Launch ThesisForge in a native PyWebView desktop window",
    )
    gui_parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="Host interface (default: 127.0.0.1)"
    )
    gui_parser.add_argument(
        "--port", type=int, default=0, help="Port to bind (default: 0 for automatic port discovery)"
    )
    gui_parser.add_argument("--debug", action="store_true", help="Enable WebView Developer Tools")

    args = parser.parse_args()
    settings = get_settings()

    def resolve_pid(arguments: argparse.Namespace) -> str:
        pid = getattr(arguments, "project_id_flag", None) or getattr(arguments, "project_id", None)
        if not pid:
            err_console.print(
                "[bold red]Error:[/bold red] Se requiere el identificador del proyecto (--project-id o argumento posicional)."
            )
            sys.exit(1)
        return str(pid)

    try:
        if args.command == "search-papers":
            format_apa = args.format_type == "apa"
            asyncio.run(_run_search_cli(query=args.query, limit=args.limit, format_apa=format_apa))
        elif args.command == "export-docx":
            pid = resolve_pid(args)
            asyncio.run(
                _run_export_docx_cli(
                    project_id=pid,
                    output_path=args.output,
                    author=args.author,
                    institution=args.institution,
                    advisor=args.advisor,
                )
            )
        elif args.command == "export-bib":
            pid = resolve_pid(args)
            asyncio.run(
                _run_export_bib_cli(
                    project_id=pid,
                    output_path=args.output,
                )
            )
        elif args.command == "export-bundle":
            pid = resolve_pid(args)
            asyncio.run(
                _run_export_bundle_cli(
                    project_id=pid,
                    output_path=args.output,
                )
            )
        elif args.command == "import-bundle":
            asyncio.run(
                _run_import_bundle_cli(
                    file_path=args.bundle_file,
                    new_project_id=args.new_project_id,
                )
            )
        elif args.command == "draft-init":
            pid = resolve_pid(args)
            asyncio.run(_run_draft_init_cli(project_id=pid))
        elif args.command == "draft-list":
            pid = resolve_pid(args)
            asyncio.run(_run_draft_list_cli(project_id=pid))
        elif args.command == "jury-audit":
            pid = resolve_pid(args)
            asyncio.run(_run_jury_audit_cli(project_id=pid))
        elif args.command == "defense-start":
            pid = resolve_pid(args)
            asyncio.run(_run_defense_start_cli(project_id=pid))
        elif args.command == "gui":
            from thesisforge.desktop.launcher import launch_desktop

            launch_desktop(
                host=args.host,
                port=args.port,
                debug=args.debug,
            )
        elif args.command == "run" or args.command is None:
            host = args.host or settings.host
            port = args.port or settings.port
            reload = (
                bool(args.reload)
                if (hasattr(args, "reload") and args.reload)
                else (settings.environment == "development")
            )

            console.print(
                f"[bold blue]Starting ThesisForge v{__version__} on http://{host}:{port}[/bold blue]"
            )
            uvicorn.run(
                "thesisforge.api.app:app",
                host=host,
                port=port,
                reload=reload,
            )
        else:
            parser.print_help()
            sys.exit(1)
    except ThesisForgeError as exc:
        err_console.print(f"\n[bold red][Error ThesisForge][/bold red] {exc}\n")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operación cancelada por el usuario.[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()

