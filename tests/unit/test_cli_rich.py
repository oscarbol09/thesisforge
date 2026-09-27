"""Unit tests verifying Rich UI tables, panels, spinners, and audit reports in CLI."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from thesisforge.cli import main
from thesisforge.models import (
    AcademicLevel,
    AcademicSearchResultDTO,
    AuditIssueDTO,
    AuditIssueType,
    AuditSeverity,
    JurorDimensionScoreDTO,
    JurorRole,
    JuryEvaluationReportDTO,
    JuryVerdict,
    ProjectStateDTO,
    SectionDraftDTO,
    SectionStatus,
)


def test_cli_rich_search_papers_table(capsys: pytest.CaptureFixture[str]):
    """Verify search-papers renders a Rich table with column headers and metadata."""
    with (
        patch("sys.argv", ["thesisforge", "search-papers", "Quantum Transformers", "--limit", "2"]),
        patch("thesisforge.rag.clients.aggregator.AcademicSearchAggregator.search") as mock_search,
    ):
        mock_search.return_value = [
            AcademicSearchResultDTO(
                paper_id="openalex:W999",
                title="Quantum Transformers for Natural Language Processing",
                authors=["Alice Quantum", "Bob Transformer"],
                year=2024,
                doi="10.1000/qt2024",
                source="openalex",
            )
        ]

        main()
        captured = capsys.readouterr()
        assert "Resultados de Literatura Científica" in captured.out
        assert "Quantum" in captured.out
        assert "Transformers" in captured.out
        assert "Alice Quantum" in captured.out
        assert "openalex" in captured.out
        assert "10.1000/qt2024" in captured.out


def test_cli_rich_jury_audit_report(capsys: pytest.CaptureFixture[str]):
    """Verify jury-audit renders formatted verdict panel, juror dimensions, and issue severity badges."""
    with (
        patch("sys.argv", ["thesisforge", "jury-audit", "--project-id", "proj-jury-01"]),
        patch(
            "thesisforge.jury.service.JuryService.audit_project", new_callable=AsyncMock
        ) as mock_audit,
        patch("thesisforge.repository.database.DatabaseManager.initialize", new_callable=AsyncMock),
        patch("thesisforge.repository.database.DatabaseManager.close", new_callable=AsyncMock),
    ):
        mock_audit.return_value = JuryEvaluationReportDTO(
            project_id="proj-jury-01",
            overall_score=92.5,
            verdict=JuryVerdict.APROBADO_CON_DISTINCION,
            summary_dictamen="La tesis presenta un rigor metodológico sobresaliente.",
            juror_evaluations=[
                JurorDimensionScoreDTO(
                    juror_role=JurorRole.METODOLOGO,
                    juror_name="Dra. Valenzuela",
                    dimension_name="Diseño Metodológico",
                    score=95.0,
                    criteria_evaluation="Operacionalización impecable.",
                    feedback="Excelente congruencia epistémica.",
                )
            ],
            issues=[
                AuditIssueDTO(
                    issue_type=AuditIssueType.METHODOLOGICAL_INCONSISTENCY,
                    severity=AuditSeverity.MINOR,
                    chapter_or_section="Capítulo 3",
                    title="Aclarar muestreo estratificado",
                    description="Detallar afijación proporcional.",
                    recommendation="Añadir fórmula de afijación.",
                )
            ],
            mandatory_fixes=["Corregir tabla de consistencia en anexo 1."],
        )

        main()
        captured = capsys.readouterr()
        assert "DICTAMEN OFICIAL DEL TRIBUNAL ACADÉMICO" in captured.out
        assert "92.5" in captured.out
        assert "APROBADO CON DISTINCIÓN" in captured.out
        assert "Dra. Valenzuela" in captured.out
        assert "Metodológico" in captured.out
        assert "Aclarar muestreo" in captured.out
        assert "estratificado" in captured.out
        assert "Corregir tabla de consistencia en anexo 1" in captured.out


def test_cli_rich_draft_list_styled(capsys: pytest.CaptureFixture[str]):
    """Verify draft-list displays chapters with formatted status badges and word counts."""
    with (
        patch("sys.argv", ["thesisforge", "draft-list", "--project-id", "proj-list-01"]),
        patch(
            "thesisforge.repository.project_repository.ProjectRepository.get_project",
            new_callable=AsyncMock,
        ) as mock_get,
        patch("thesisforge.repository.database.DatabaseManager.initialize", new_callable=AsyncMock),
        patch("thesisforge.repository.database.DatabaseManager.close", new_callable=AsyncMock),
    ):
        mock_get.return_value = ProjectStateDTO(
            id="proj-list-01",
            title="Tesis de Deep Learning",
            academic_level=AcademicLevel.DOCTORADO,
            sections=[
                SectionDraftDTO(
                    section_id="sec_1_1",
                    chapter_number=1,
                    order_index=1,
                    title="Planteamiento del Problema",
                    status=SectionStatus.APPROVED,
                    word_count=850,
                ),
                SectionDraftDTO(
                    section_id="sec_2_1",
                    chapter_number=2,
                    order_index=1,
                    title="Marco Teórico",
                    status=SectionStatus.IN_PROGRESS,
                    word_count=1200,
                ),
            ],
        )

        main()
        captured = capsys.readouterr()
        assert "Tesis de Deep Learning" in captured.out
        assert "sec_1_1" in captured.out
        assert "approved" in captured.out
        assert "850 palabras" in captured.out
        assert "sec_2_1" in captured.out
        assert "in_progress" in captured.out


def test_cli_rich_export_docx_panel(capsys: pytest.CaptureFixture[str], tmp_path: Path):
    """Verify export-docx displays Rich panel with destination path and size."""
    fake_file = tmp_path / "thesis_rich.docx"
    fake_file.write_bytes(b"PK0000dummycontent")

    with (
        patch(
            "sys.argv",
            [
                "thesisforge",
                "export-docx",
                "--project-id",
                "proj-docx-01",
                "--output",
                str(fake_file),
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
        assert "ThesisForge — Exportación Editorial" in captured.out
        assert "Documento APA 7 compilado exitosamente" in captured.out
