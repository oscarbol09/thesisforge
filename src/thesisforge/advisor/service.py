"""Methodological advisory service orchestrating AI interview, validation, and project state."""

from typing import Any

from thesisforge.advisor.consistency_matrix import (
    ConsistencyMatrixEngine,
    ConsistencyMatrixReport,
)
from thesisforge.advisor.state_machine import AdvisorStateMachine, AdvisorStep
from thesisforge.advisor.validators import MethodologyValidator
from thesisforge.core.logging import get_logger
from thesisforge.exceptions import InvalidPhaseTransitionError, MethodologyValidationError
from thesisforge.llm.prompts import (
    ADVISOR_SYSTEM_PROMPT,
    CONSISTENCY_AUDIT_PROMPT,
    METHODOLOGY_DESIGN_PROMPT,
    OBJECTIVES_PROMPT,
    PROBLEM_FORMULATION_PROMPT,
)
from thesisforge.llm.router import LLMRouter
from thesisforge.models import (
    MethodologyDTO,
    ProjectPhase,
    ProjectStateDTO,
    ResearchApproach,
)
from thesisforge.repository.project_repository import ProjectRepository

logger = get_logger(__name__)


class AdvisorService:
    """Orchestrator for the Socratic Methodological Interview."""

    def __init__(self, project_repo: ProjectRepository, llm_router: LLMRouter) -> None:
        self.repo = project_repo
        self.llm = llm_router

    async def get_interview_status(self, project_id: str) -> dict[str, Any]:
        """Fetch current interview progression for a given project."""
        project = await self.repo.get_project(project_id)
        step_sequence = AdvisorStateMachine.get_step_sequence_for_approach(
            project.methodology.approach.value if project.methodology.approach else None
        )
        current_step = self._determine_current_step(project)
        skipped_steps = self._determine_skipped_steps(project)
        progress = AdvisorStateMachine.calculate_progress(
            current_step, skipped_steps=skipped_steps, step_order=step_sequence
        )
        audit = MethodologyValidator.audit_project(project)

        return {
            "project_id": project.id,
            "title": project.title,
            "academic_level": project.academic_level.value,
            "current_step": current_step.value,
            "skipped_steps": [s.value for s in skipped_steps],
            "progress_percentage": progress,
            "can_advance": audit["is_consistent"],
            "audit": audit,
        }

    def _determine_skipped_steps(self, project: ProjectStateDTO) -> list[AdvisorStep]:
        """Determine intentionally skipped steps based on research approach."""
        skipped: list[AdvisorStep] = []
        if project.methodology.approach == ResearchApproach.CUALITATIVO:
            skipped.append(AdvisorStep.HYPOTHESIS)
            skipped.append(AdvisorStep.OPERATIONALIZATION)
        elif project.methodology.approach == ResearchApproach.CUANTITATIVO:
            skipped.append(AdvisorStep.CATEGORIES)
        return skipped

    def _determine_current_step(self, project: ProjectStateDTO) -> AdvisorStep:
        """Derive current interview step from existing project fields."""
        if not project.topic or not project.area_of_study:
            return AdvisorStep.TOPIC_AND_AREA
        if not project.research_problem:
            return AdvisorStep.PROBLEM_STATEMENT
        if not project.research_question:
            return AdvisorStep.RESEARCH_QUESTION
        if not project.general_objective or not project.specific_objectives:
            return AdvisorStep.OBJECTIVES
        if project.methodology.approach == ResearchApproach.CUANTITATIVO and not project.hypothesis:
            return AdvisorStep.HYPOTHESIS
        if not project.methodology.design or not project.methodology.analysis_technique:
            return AdvisorStep.METHODOLOGY_DESIGN

        audit = MethodologyValidator.audit_project(project)
        if not audit["is_consistent"]:
            return AdvisorStep.CONSISTENCY_AUDIT

        return AdvisorStep.APPROVED

    async def process_step(
        self,
        project_id: str,
        step: AdvisorStep,
        user_input: str,
        form_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Process a specific interview step with AI feedback and state update."""
        project = await self.repo.get_project(project_id)
        form = form_data or {}
        system_prompt = ADVISOR_SYSTEM_PROMPT.format(academic_level=project.academic_level.value)

        ai_response: dict[str, Any] = {}

        if step == AdvisorStep.TOPIC_AND_AREA:
            project.area_of_study = form.get("area_of_study", project.area_of_study) or user_input
            project.topic = form.get("topic", project.topic) or user_input
            if form.get("title"):
                project.title = form["title"]
            ai_response = {
                "message": f"Área '{project.area_of_study}' y tema '{project.topic}' registrados. Procedamos al planteamiento del problema."
            }

        elif step == AdvisorStep.PROBLEM_STATEMENT:
            prompt = PROBLEM_FORMULATION_PROMPT.format(
                area_of_study=project.area_of_study,
                topic=project.topic,
                user_input=user_input,
                academic_level=project.academic_level.value,
            )
            try:
                ai_response = await self.llm.complete_json(prompt, system_prompt=system_prompt)
                refined = ai_response.get("refined_problem", user_input)
                project.research_problem = refined
                if form.get("research_question"):
                    project.research_question = form["research_question"]
                elif ai_response.get("suggested_questions"):
                    project.research_question = ai_response["suggested_questions"][0]
            except Exception as e:
                logger.warning(
                    "LLM JSON completion failed in problem statement, using raw input.",
                    extra={"error": str(e)},
                )
                project.research_problem = user_input
                ai_response = {
                    "critique": "Problema registrado directamente.",
                    "refined_problem": user_input,
                }

        elif step == AdvisorStep.RESEARCH_QUESTION:
            project.research_question = user_input.strip()
            issues = MethodologyValidator.validate_research_question(project.research_question)
            ai_response = {
                "question": project.research_question,
                "issues": issues,
                "is_valid": len(issues) == 0,
            }

        elif step == AdvisorStep.OBJECTIVES:
            approach_val = (
                project.methodology.approach.value
                if project.methodology.approach
                else "cuantitativo"
            )
            prompt = OBJECTIVES_PROMPT.format(
                research_problem=project.research_problem,
                research_question=project.research_question,
                approach=approach_val,
                academic_level=project.academic_level.value,
                user_input=user_input,
            )
            try:
                ai_response = await self.llm.complete_json(prompt, system_prompt=system_prompt)
                if form.get("general_objective"):
                    project.general_objective = form["general_objective"]
                elif ai_response.get("general_objective"):
                    project.general_objective = ai_response["general_objective"]

                if form.get("specific_objectives"):
                    project.specific_objectives = form["specific_objectives"]
                elif ai_response.get("specific_objectives"):
                    project.specific_objectives = ai_response["specific_objectives"]

                if ai_response.get("variables_or_categories"):
                    project.variables = ai_response["variables_or_categories"]
            except Exception as e:
                logger.warning("LLM objective extraction fallback.", extra={"error": str(e)})
                project.general_objective = user_input
                ai_response = {"general_objective": user_input}

        elif step == AdvisorStep.HYPOTHESIS:
            project.hypothesis = user_input.strip() or form.get("hypothesis")
            issues = MethodologyValidator.validate_hypothesis(
                project.hypothesis, project.methodology.approach
            )
            ai_response = {
                "hypothesis": project.hypothesis,
                "issues": issues,
                "is_valid": len(issues) == 0,
            }

        elif step == AdvisorStep.METHODOLOGY_DESIGN:
            approach_str = form.get(
                "approach",
                project.methodology.approach.value
                if project.methodology.approach
                else "cuantitativo",
            )
            try:
                project.methodology.approach = ResearchApproach(approach_str)
            except ValueError:
                project.methodology.approach = ResearchApproach.CUANTITATIVO

            prompt = METHODOLOGY_DESIGN_PROMPT.format(
                academic_level=project.academic_level.value,
                research_question=project.research_question,
                general_objective=project.general_objective,
                user_input=user_input,
                approach=project.methodology.approach.value,
            )
            try:
                ai_response = await self.llm.complete_json(prompt, system_prompt=system_prompt)
                project.methodology.design = form.get(
                    "design", ai_response.get("design", "Descriptivo")
                )
                project.methodology.population = form.get(
                    "population", ai_response.get("population", "")
                )
                project.methodology.sample = form.get("sample", ai_response.get("sample", ""))
                project.methodology.instruments = form.get(
                    "instruments", ai_response.get("instruments", [])
                )
                project.methodology.analysis_technique = form.get(
                    "analysis_technique", ai_response.get("analysis_technique", "")
                )
            except Exception as e:
                logger.warning(
                    "Methodology design fallback to direct form.", extra={"error": str(e)}
                )
                project.methodology = MethodologyDTO(
                    approach=project.methodology.approach,
                    design=form.get("design", user_input),
                    population=form.get("population", ""),
                    sample=form.get("sample", ""),
                    instruments=form.get("instruments", []),
                    analysis_technique=form.get("analysis_technique", ""),
                )
                ai_response = {"design": project.methodology.design}

        elif step == AdvisorStep.CONSISTENCY_AUDIT:
            prompt = CONSISTENCY_AUDIT_PROMPT.format(
                academic_level=project.academic_level.value,
                title=project.title,
                research_problem=project.research_problem,
                research_question=project.research_question,
                hypothesis=project.hypothesis or "N/A",
                general_objective=project.general_objective,
                specific_objectives="; ".join(project.specific_objectives),
                approach=project.methodology.approach.value
                if project.methodology.approach
                else "N/A",
                design=project.methodology.design,
            )
            try:
                ai_response = await self.llm.complete_json(prompt, system_prompt=system_prompt)
            except Exception as e:
                logger.warning("Audit LLM fallback.", extra={"error": str(e)})
                local_audit = MethodologyValidator.audit_project(project)
                ai_response = {
                    "score": local_audit["score"],
                    "status": local_audit["status"],
                    "verdict": "Auditoría determinista ejecutada.",
                    "flaws": local_audit["issues"],
                }

        # Persist updated project
        await self.repo.update_project(project)
        next_step = self._determine_current_step(project)
        skipped_steps = self._determine_skipped_steps(project)

        return {
            "project_id": project.id,
            "step_processed": step.value,
            "next_step": next_step.value,
            "skipped_steps": [s.value for s in skipped_steps],
            "progress_percentage": AdvisorStateMachine.calculate_progress(
                next_step, skipped_steps=skipped_steps
            ),
            "ai_analysis": ai_response,
            "project_state": project,
        }

    async def approve_methodology(self, project_id: str) -> ProjectStateDTO:
        """Validate consistency and advance the project to Phase 2 (Context/RAG)."""
        project = await self.repo.get_project(project_id)
        audit = MethodologyValidator.audit_project(project)

        if not audit["is_consistent"]:
            raise MethodologyValidationError(
                "No se puede aprobar la ficha metodológica porque existen inconsistencias.",
                details={"issues": ", ".join(audit["issues"])},
            )

        if project.phase not in (ProjectPhase.SETUP, ProjectPhase.ORIENTATION):
            raise InvalidPhaseTransitionError(
                f"Fase inválida para aprobación metodológica: {project.phase.value}"
            )

        project.phase = ProjectPhase.CONTEXT
        await self.repo.update_project(project)
        logger.info(
            "Project methodology approved and transitioned to CONTEXT phase.",
            extra={"project_id": project.id},
        )
        return project

    async def get_consistency_matrix(self, project_id: str) -> ConsistencyMatrixReport:
        """Construct the 6-pillar methodological consistency matrix and validity threats audit."""
        project = await self.repo.get_project(project_id)
        matrix = ConsistencyMatrixEngine.build_matrix(project)
        project.consistency_matrix = matrix.model_dump()
        await self.repo.update_project(project)
        logger.info(
            "Generated methodological consistency matrix.",
            extra={
                "project_id": project_id,
                "score": matrix.overall_alignment_score,
                "is_consistent": matrix.is_fully_consistent,
            },
        )
        return matrix
