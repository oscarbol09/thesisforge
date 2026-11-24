"""Regression coverage for the advisor's Phase 1 drafting flow."""

from unittest.mock import create_autospec

import pytest

from thesisforge.advisor.service import AdvisorService
from thesisforge.llm.router import LLMRouter
from thesisforge.models import (
    AcademicLevel,
    ProjectPhase,
    ProjectStateDTO,
    SectionDraftDTO,
    SectionStatus,
)
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("component", "academic_level", "auto_apply", "with_scope_section"),
    [
        ("justification", AcademicLevel.PREGRADO, False, False),
        ("objectives", AcademicLevel.MAESTRIA, False, False),
        ("scope_limitations", AcademicLevel.DOCTORADO, False, False),
        pytest.param("scope_limitations", AcademicLevel.DOCTORADO, True, False, id="scope-phase-1"),
        pytest.param(
            "scope_limitations", AcademicLevel.DOCTORADO, True, True, id="scope-existing-section"
        ),
    ],
)
async def test_assisted_draft_uses_academic_level_and_saves_scope_when_requested(
    in_memory_db: DatabaseManager,
    component: str,
    academic_level: AcademicLevel,
    auto_apply: bool,
    with_scope_section: bool,
) -> None:
    repository = ProjectRepository(in_memory_db, "local")
    previous_scope = "Alcance anterior."
    draft = "El estudio abarca escuelas públicas durante 2025."
    project = ProjectStateDTO(
        title="Participación escolar",
        topic="Participación estudiantil",
        academic_level=academic_level,
        phase=ProjectPhase.ORIENTATION,
        scope_limitations=previous_scope,
    )
    if with_scope_section:
        project.sections.append(
            SectionDraftDTO(section_id="sec_1_5", title="Alcances y limitaciones")
        )
    await repository.create_project(project)

    llm = create_autospec(LLMRouter, instance=True)
    llm.complete_json.return_value = {"draft_text": draft}
    advisor = AdvisorService(repository, llm)

    result = await advisor.assist_drafting(project.id, component, auto_apply=auto_apply)

    assert result["draft_text"] == draft
    saved = await repository.get_project(project.id)
    assert saved.scope_limitations == (draft if auto_apply else previous_scope)
    if with_scope_section:
        assert saved.sections[0].content == draft
        assert saved.sections[0].status == SectionStatus.READY_FOR_REVIEW
    else:
        assert saved.sections == []
    llm.complete_json.assert_awaited_once()
    system_prompt = llm.complete_json.await_args.kwargs["system_prompt"]
    assert "{academic_level}" not in system_prompt
    assert f"({academic_level.value})" in system_prompt
