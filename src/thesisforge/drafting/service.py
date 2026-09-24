"""Assisted thesis drafting service managing chapter generation, streaming, refinement, and human approvals."""

from collections.abc import AsyncGenerator
from typing import Any

from thesisforge.core.logging import get_logger
from thesisforge.core.time import utc_now
from thesisforge.drafting.detox import DraftQualityAuditResult, audit_scholarly_draft
from thesisforge.drafting.memory import HierarchicalMemoryManager
from thesisforge.drafting.sanitizer import clean_draft_markup
from thesisforge.drafting.templates import get_default_thesis_sections
from thesisforge.exceptions import ConfigurationError, SectionNotFoundError
from thesisforge.llm.prompts import (
    ADVISOR_SYSTEM_PROMPT,
    CHAPTER_DRAFTING_PROMPT,
    SECTION_REFINE_PROMPT,
    SECTION_SUMMARY_PROMPT,
)
from thesisforge.llm.router import LLMRouter
from thesisforge.models import (
    DocumentChunkDTO,
    ProjectPhase,
    ProjectStateDTO,
    ResearchApproach,
    SectionDraftDTO,
    SectionStatus,
)
from thesisforge.rag.service import RAGService
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository

logger = get_logger(__name__)


class DraftService:
    """Service orchestrating thesis chapter drafting, hierarchical memory assembly, and streaming review."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        project_repo: ProjectRepository,
        llm_router: LLMRouter | None = None,
        rag_service: RAGService | None = None,
    ) -> None:
        self.db = db_manager
        self.repo = project_repo
        self.llm = llm_router
        self.rag = rag_service

    async def initialize_thesis_sections(
        self,
        project_id: str,
        force_reset: bool = False,
    ) -> list[SectionDraftDTO]:
        """Populate the canonical 5-chapter thesis outline tailored to the project."""
        project = await self.repo.get_project(project_id)

        if project.sections and not force_reset:
            return project.sections

        approach = (
            project.methodology.approach
            if project.methodology and project.methodology.approach
            else ResearchApproach.CUANTITATIVO
        )
        sections = get_default_thesis_sections(
            approach=approach,
            academic_level=project.academic_level,
        )

        project.sections = sections
        if project.phase in (ProjectPhase.SETUP, ProjectPhase.ORIENTATION, ProjectPhase.CONTEXT):
            project.phase = ProjectPhase.DRAFTING

        await self.repo.update_project(project)
        logger.info(
            "Initialized canonical thesis sections.",
            extra={"project_id": project_id, "sections_count": len(sections)},
        )
        return sections

    async def get_sections(self, project_id: str) -> list[SectionDraftDTO]:
        """List all chapter sections for a project."""
        project = await self.repo.get_project(project_id)
        if not project.sections:
            return await self.initialize_thesis_sections(project_id)
        return project.sections

    def _find_section(self, project: ProjectStateDTO, section_id: str) -> SectionDraftDTO:
        """Locate section within the project state instance."""
        for sec in project.sections:
            if sec.section_id == section_id:
                return sec
        raise SectionNotFoundError(
            f"La sección '{section_id}' no existe en el proyecto '{project.id}'.",
            details={"project_id": project.id, "section_id": section_id},
        )

    async def get_section(self, project_id: str, section_id: str) -> SectionDraftDTO:
        """Fetch a specific section draft from the project."""
        project = await self.repo.get_project(project_id)
        return self._find_section(project, section_id)

    async def _retrieve_rag_context(
        self,
        project: ProjectStateDTO,
        section: SectionDraftDTO,
        top_k: int = 4,
    ) -> list[DocumentChunkDTO]:
        """Query ChromaDB for relevant academic literature chunks matching the section topic."""
        if not self.rag or not project.indexed_documents:
            return []

        template = HierarchicalMemoryManager.get_section_template(section.section_id)
        query_text = f"{section.title} {template.description if template else ''}"
        try:
            return await self.rag.query_relevant_chunks(
                project_id=project.id,
                query=query_text,
                top_k=top_k,
            )
        except Exception as e:
            logger.warning(
                "RAG context retrieval failed during draft generation.",
                extra={"project_id": project.id, "section_id": section.section_id, "error": str(e)},
            )
            return []

    async def generate_section_draft(
        self,
        project_id: str,
        section_id: str,
        user_guidance: str | None = None,
        top_k_rag: int = 4,
    ) -> SectionDraftDTO:
        """Generate a complete chapter or subsection draft utilizing hierarchical memory and RAG."""
        if not self.llm:
            raise ConfigurationError("LLMRouter no está configurado en DraftService.")
        project = await self.repo.get_project(project_id)
        section = self._find_section(project, section_id)

        chunks = await self._retrieve_rag_context(project, section, top_k=top_k_rag)
        context_layers = HierarchicalMemoryManager.build_drafting_context(
            project=project,
            target_section_id=section_id,
            retrieved_chunks=chunks,
            user_guidance=user_guidance,
        )

        prompt = CHAPTER_DRAFTING_PROMPT.format(
            layer_0_methodology=context_layers["layer_0_methodology"],
            layer_1_memory=context_layers["layer_1_memory"],
            layer_2_literature=context_layers["layer_2_literature"],
            target_section_info=context_layers["target_section_info"],
        )

        logger.info(
            "Generating section draft with LLM.",
            extra={"project_id": project_id, "section_id": section_id},
        )

        raw_draft = await self.llm.complete(
            prompt=prompt,
            system_prompt=ADVISOR_SYSTEM_PROMPT.format(academic_level=project.academic_level.value),
            temperature=0.35,
        )

        cleaned_text = clean_draft_markup(raw_draft)
        section.content = cleaned_text
        section.word_count = len(cleaned_text.split())
        section.status = SectionStatus.READY_FOR_REVIEW
        section.version += 1
        section.updated_at = utc_now()

        await self.repo.update_project(project)
        return section

    async def stream_section_draft(
        self,
        project_id: str,
        section_id: str,
        user_guidance: str | None = None,
        top_k_rag: int = 4,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream generated section draft token-by-token over an async generator (WebSocket ready)."""
        if not self.llm:
            raise ConfigurationError("LLMRouter no está configurado en DraftService.")
        project = await self.repo.get_project(project_id)
        section = self._find_section(project, section_id)

        chunks = await self._retrieve_rag_context(project, section, top_k=top_k_rag)
        context_layers = HierarchicalMemoryManager.build_drafting_context(
            project=project,
            target_section_id=section_id,
            retrieved_chunks=chunks,
            user_guidance=user_guidance,
        )

        prompt = CHAPTER_DRAFTING_PROMPT.format(
            layer_0_methodology=context_layers["layer_0_methodology"],
            layer_1_memory=context_layers["layer_1_memory"],
            layer_2_literature=context_layers["layer_2_literature"],
            target_section_info=context_layers["target_section_info"],
        )

        yield {
            "event": "start",
            "section_id": section_id,
            "title": section.title,
            "rag_chunks_found": len(chunks),
        }

        accumulated_tokens: list[str] = []
        async for token in self.llm.stream_completion(
            prompt=prompt,
            system_prompt=ADVISOR_SYSTEM_PROMPT.format(academic_level=project.academic_level.value),
            temperature=0.35,
        ):
            accumulated_tokens.append(token)
            yield {"event": "token", "data": token}

        full_raw_text = "".join(accumulated_tokens)
        cleaned_text = clean_draft_markup(full_raw_text)

        section.content = cleaned_text
        section.word_count = len(cleaned_text.split())
        section.status = SectionStatus.READY_FOR_REVIEW
        section.version += 1
        section.updated_at = utc_now()

        await self.repo.update_project(project)

        yield {
            "event": "complete",
            "section": section.model_dump(mode="json"),
        }

    async def revise_section_draft(
        self,
        project_id: str,
        section_id: str,
        user_feedback: str,
    ) -> SectionDraftDTO:
        """Refine an existing section draft based on user feedback and critiques."""
        if not self.llm:
            raise ConfigurationError("LLMRouter no está configurado en DraftService.")
        project = await self.repo.get_project(project_id)
        section = self._find_section(project, section_id)

        context_layers = HierarchicalMemoryManager.build_drafting_context(
            project=project,
            target_section_id=section_id,
        )

        prompt = SECTION_REFINE_PROMPT.format(
            layer_0_methodology=context_layers["layer_0_methodology"],
            layer_1_memory=context_layers["layer_1_memory"],
            current_draft=section.content or "(Sin contenido previo)",
            user_feedback=user_feedback.strip(),
        )

        raw_revised = await self.llm.complete(
            prompt=prompt,
            system_prompt=ADVISOR_SYSTEM_PROMPT.format(academic_level=project.academic_level.value),
            temperature=0.3,
        )

        cleaned_text = clean_draft_markup(raw_revised)
        section.content = cleaned_text
        section.word_count = len(cleaned_text.split())
        section.user_feedback = user_feedback.strip()
        section.status = SectionStatus.READY_FOR_REVIEW
        section.version += 1
        section.updated_at = utc_now()

        await self.repo.update_project(project)
        return section

    async def stream_revise_section_draft(
        self,
        project_id: str,
        section_id: str,
        user_feedback: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream revised draft tokens based on researcher feedback."""
        if not self.llm:
            raise ConfigurationError("LLMRouter no está configurado en DraftService.")
        project = await self.repo.get_project(project_id)
        section = self._find_section(project, section_id)

        context_layers = HierarchicalMemoryManager.build_drafting_context(
            project=project,
            target_section_id=section_id,
        )

        prompt = SECTION_REFINE_PROMPT.format(
            layer_0_methodology=context_layers["layer_0_methodology"],
            layer_1_memory=context_layers["layer_1_memory"],
            current_draft=section.content or "(Sin contenido previo)",
            user_feedback=user_feedback.strip(),
        )

        yield {
            "event": "start_revision",
            "section_id": section_id,
            "title": section.title,
        }

        accumulated_tokens: list[str] = []
        async for token in self.llm.stream_completion(
            prompt=prompt,
            system_prompt=ADVISOR_SYSTEM_PROMPT.format(academic_level=project.academic_level.value),
            temperature=0.3,
        ):
            accumulated_tokens.append(token)
            yield {"event": "token", "data": token}

        full_raw_text = "".join(accumulated_tokens)
        cleaned_text = clean_draft_markup(full_raw_text)

        section.content = cleaned_text
        section.word_count = len(cleaned_text.split())
        section.user_feedback = user_feedback.strip()
        section.status = SectionStatus.READY_FOR_REVIEW
        section.version += 1
        section.updated_at = utc_now()

        await self.repo.update_project(project)

        yield {
            "event": "complete",
            "section": section.model_dump(mode="json"),
        }

    async def update_section_content(
        self,
        project_id: str,
        section_id: str,
        content: str,
        status: SectionStatus | None = None,
        user_feedback: str | None = None,
    ) -> SectionDraftDTO:
        """Allow manual editing of section draft text by researcher."""
        project = await self.repo.get_project(project_id)
        section = self._find_section(project, section_id)

        section.content = content.strip()
        section.word_count = len(content.strip().split())
        if status:
            section.status = status
        if user_feedback is not None:
            section.user_feedback = user_feedback
        section.updated_at = utc_now()

        await self.repo.update_project(project)
        return section

    async def approve_section(
        self,
        project_id: str,
        section_id: str,
    ) -> SectionDraftDTO:
        """Approve section draft, generate its memory summary if absent, and check project milestone."""
        project = await self.repo.get_project(project_id)
        section = self._find_section(project, section_id)

        section.status = SectionStatus.APPROVED
        section.updated_at = utc_now()

        # Generate summary for hierarchical memory if missing
        if not section.summary and section.content:
            if self.llm:
                try:
                    summary_prompt = SECTION_SUMMARY_PROMPT.format(
                        section_title=section.title,
                        content=section.content[:3000],
                    )
                    summary_text = await self.llm.complete(
                        prompt=summary_prompt,
                        system_prompt=ADVISOR_SYSTEM_PROMPT.format(
                            academic_level=project.academic_level.value
                        ),
                        temperature=0.2,
                    )
                    section.summary = summary_text.strip()
                except Exception as e:
                    logger.warning(
                        "Automatic section summary generation failed on approval.",
                        extra={"error": str(e)},
                    )
                    section.summary = section.content[:250].strip() + "..."
            else:
                section.summary = section.content[:250].strip() + "..."

        # If all sections are approved, advance project phase to REVIEW
        all_approved = all(s.status == SectionStatus.APPROVED for s in project.sections)
        if all_approved and len(project.sections) > 0:
            project.phase = ProjectPhase.REVIEW

        await self.repo.update_project(project)
        logger.info(
            "Section approved by researcher.",
            extra={
                "project_id": project_id,
                "section_id": section_id,
                "phase": project.phase.value,
            },
        )
        return section

    async def audit_section_quality(
        self,
        project_id: str,
        section_id: str,
    ) -> DraftQualityAuditResult:
        """Audit an individual thesis section for AI slop, syntactic cadence, and L3 citation anchors."""
        project = await self.repo.get_project(project_id)
        section = self._find_section(project, section_id)
        return audit_scholarly_draft(section.content or "")

