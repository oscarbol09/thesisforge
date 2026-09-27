"""Methodological advisory service orchestrating AI interview, validation, and project state."""

import contextlib
from typing import Any

from thesisforge.advisor.consistency_matrix import (
    ConsistencyMatrixEngine,
    ConsistencyMatrixReport,
)
from thesisforge.advisor.state_machine import AdvisorStateMachine, AdvisorStep
from thesisforge.advisor.validators import MethodologyValidator
from thesisforge.core.logging import get_logger
from thesisforge.exceptions import MethodologyValidationError
from thesisforge.llm.prompts import (
    ADVISOR_SYSTEM_PROMPT,
    CONSISTENCY_AUDIT_PROMPT,
    METHODOLOGY_DESIGN_PROMPT,
    OBJECTIVES_PROMPT,
    PROBLEM_FORMULATION_PROMPT,
)
from thesisforge.llm.router import LLMRouter
from thesisforge.models import (
    AcademicLevel,
    EpistemologicalParadigm,
    ProjectPhase,
    ProjectStateDTO,
    QualitativeCategoryDTO,
    ResearchApproach,
    SamplingTechnique,
    VariableOperationalizationDTO,
)
from thesisforge.repository.project_repository import ProjectRepository

logger = get_logger(__name__)


class AdvisorService:
    """Orchestrator for the Socratic Methodological Interview."""

    def __init__(self, project_repo: ProjectRepository, llm_router: LLMRouter) -> None:
        self.repo = project_repo
        self.llm = llm_router

    @staticmethod
    def _sanitize(text: str | None) -> str:
        """Sanitize user input to prevent prompt injection."""
        if not text:
            return ""
        # Remove triple quotes and XML tags that could break prompt structure
        return text.replace('"""', '"').replace("<", "").replace(">", "").strip()

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
        if not project.title or not project.academic_level:
            return AdvisorStep.SETUP
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

    def _sync_form_data_to_project(self, project: ProjectStateDTO, form: dict[str, Any]) -> None:
        """Synchronize incoming form fields into the ProjectStateDTO."""
        if not form:
            return

        if form.get("title"):
            project.title = str(form["title"]).strip()

        if form.get("academic_level"):
            with contextlib.suppress(ValueError):
                project.academic_level = AcademicLevel(str(form["academic_level"]).strip())

        if form.get("area_of_study"):
            project.area_of_study = str(form["area_of_study"]).strip()

        if form.get("topic"):
            project.topic = str(form["topic"]).strip()

        if form.get("research_problem") is not None:
            val = str(form["research_problem"]).strip()
            if val:
                project.research_problem = val

        if form.get("justification") is not None:
            project.justification = str(form["justification"]).strip()

        if form.get("scope_limitations") is not None:
            project.scope_limitations = str(form["scope_limitations"]).strip()

        if form.get("research_question") is not None:
            val = str(form["research_question"]).strip()
            if val:
                project.research_question = val

        if form.get("general_objective") is not None:
            val = str(form["general_objective"]).strip()
            if val:
                project.general_objective = val

        if form.get("specific_objectives") is not None and isinstance(
            form["specific_objectives"], list
        ):
            objs = [str(x).strip() for x in form["specific_objectives"] if str(x).strip()]
            if objs:
                project.specific_objectives = objs

        if form.get("hypothesis") is not None:
            project.hypothesis = str(form["hypothesis"]).strip()

        if form.get("variables") is not None and isinstance(form["variables"], list):
            vars_cleaned = [str(x).strip() for x in form["variables"] if str(x).strip()]
            project.variables = vars_cleaned

        # Operationalized variables
        if "operationalized_variables" in form and isinstance(
            form["operationalized_variables"], list
        ):
            parsed_ops: list[VariableOperationalizationDTO] = []
            for item in form["operationalized_variables"]:
                if isinstance(item, dict) and item.get("name"):
                    with contextlib.suppress(Exception):
                        parsed_ops.append(VariableOperationalizationDTO(**item))
            project.operationalized_variables = parsed_ops

        # Qualitative categories
        if "qualitative_categories" in form and isinstance(form["qualitative_categories"], list):
            parsed_cats: list[QualitativeCategoryDTO] = []
            for item in form["qualitative_categories"]:
                if isinstance(item, dict) and item.get("name"):
                    with contextlib.suppress(Exception):
                        parsed_cats.append(QualitativeCategoryDTO(**item))
            project.qualitative_categories = parsed_cats

        # Nested or flat methodology fields
        meth_dict = form["methodology"] if isinstance(form.get("methodology"), dict) else {}
        approach_val = meth_dict.get("approach") or form.get("approach")
        if approach_val:
            with contextlib.suppress(ValueError):
                project.methodology.approach = ResearchApproach(str(approach_val).strip())

        paradigm_val = meth_dict.get("paradigm") or form.get("paradigm")
        if paradigm_val:
            with contextlib.suppress(ValueError):
                project.methodology.paradigm = EpistemologicalParadigm(str(paradigm_val).strip())

        sampling_val = meth_dict.get("sampling_technique") or form.get("sampling_technique")
        if sampling_val:
            with contextlib.suppress(ValueError):
                project.methodology.sampling_technique = SamplingTechnique(
                    str(sampling_val).strip()
                )

        for m_attr in (
            "design",
            "population",
            "sample",
            "unit_of_analysis",
            "analysis_technique",
            "data_collection_procedure",
            "temporal_scope",
            "spatial_setting",
        ):
            raw_m_val = meth_dict.get(m_attr) or form.get(m_attr)
            if raw_m_val is not None:
                setattr(project.methodology, m_attr, str(raw_m_val).strip())

        inst_val = meth_dict.get("instruments") or form.get("instruments")
        if inst_val is not None and isinstance(inst_val, list):
            project.methodology.instruments = [str(i).strip() for i in inst_val if str(i).strip()]

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
        safe_input = self._sanitize(user_input)
        system_prompt = ADVISOR_SYSTEM_PROMPT.format(academic_level=project.academic_level.value)

        # 1. Sync any passed form data immediately
        self._sync_form_data_to_project(project, form)

        ai_response: dict[str, Any] = {}

        if step == AdvisorStep.SETUP:
            if safe_input and not project.title:
                project.title = safe_input
            ai_response = {
                "message": f"Configuración inicial establecida para nivel '{project.academic_level.value}' y título '{project.title}'."
            }

        elif step == AdvisorStep.TOPIC_AND_AREA:
            if safe_input and not project.topic:
                project.topic = safe_input
            ai_response = {
                "message": f"Área '{project.area_of_study}' y tema '{project.topic}' registrados. Procedamos al planteamiento del problema."
            }

        elif step == AdvisorStep.PROBLEM_STATEMENT:
            if safe_input:
                prompt = PROBLEM_FORMULATION_PROMPT.format(
                    area_of_study=project.area_of_study,
                    topic=project.topic,
                    user_input=safe_input,
                    academic_level=project.academic_level.value,
                )
                try:
                    ai_response = await self.llm.complete_json(prompt, system_prompt=system_prompt)
                    refined = ai_response.get("refined_problem")
                    if refined and not project.research_problem:
                        project.research_problem = refined
                    if not project.research_question and ai_response.get("suggested_questions"):
                        project.research_question = ai_response["suggested_questions"][0]
                except Exception as e:
                    logger.warning(
                        "LLM JSON completion failed in problem statement, using raw input.",
                        extra={"error": str(e)},
                    )
                    if not project.research_problem:
                        project.research_problem = safe_input
                    ai_response = {
                        "critique": "Problema registrado directamente.",
                        "refined_problem": project.research_problem,
                    }
            else:
                issues = MethodologyValidator.validate_problem_statement(project.research_problem)
                ai_response = {
                    "refined_problem": project.research_problem,
                    "issues": issues,
                    "is_valid": len(issues) == 0,
                    "message": "Planteamiento del problema registrado correctamente.",
                }

        elif step == AdvisorStep.RESEARCH_QUESTION:
            if safe_input and not project.research_question:
                project.research_question = safe_input
            issues = MethodologyValidator.validate_research_question(project.research_question)
            ai_response = {
                "question": project.research_question,
                "issues": issues,
                "is_valid": len(issues) == 0,
                "message": "Pregunta de investigación validada."
                if len(issues) == 0
                else "Observaciones detectadas en la formulación de la pregunta.",
            }

        elif step == AdvisorStep.OBJECTIVES:
            if safe_input and (not project.general_objective or not project.specific_objectives):
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
                    user_input=safe_input,
                )
                try:
                    ai_response = await self.llm.complete_json(prompt, system_prompt=system_prompt)
                    if not project.general_objective and ai_response.get("general_objective"):
                        project.general_objective = ai_response["general_objective"]
                    if not project.specific_objectives and ai_response.get("specific_objectives"):
                        project.specific_objectives = ai_response["specific_objectives"]
                    if not project.variables and ai_response.get("variables_or_categories"):
                        project.variables = ai_response["variables_or_categories"]
                except Exception as e:
                    logger.warning("LLM objective extraction fallback.", extra={"error": str(e)})
                    if not project.general_objective:
                        project.general_objective = safe_input
                    ai_response = {"general_objective": project.general_objective}

            gen_issues = MethodologyValidator.validate_general_objective(
                project.general_objective, project.research_question
            )
            spec_issues = MethodologyValidator.validate_specific_objectives(
                project.specific_objectives
            )
            all_obj_issues = gen_issues + spec_issues
            if not ai_response:
                ai_response = {
                    "general_objective": project.general_objective,
                    "specific_objectives": project.specific_objectives,
                    "issues": all_obj_issues,
                    "is_valid": len(all_obj_issues) == 0,
                    "message": "Objetivos registrados y validados."
                    if len(all_obj_issues) == 0
                    else "Observaciones metodológicas en objetivos.",
                }
            else:
                ai_response["issues"] = all_obj_issues
                ai_response["is_valid"] = len(all_obj_issues) == 0

        elif step == AdvisorStep.HYPOTHESIS:
            if safe_input and not project.hypothesis:
                project.hypothesis = safe_input
            issues = MethodologyValidator.validate_hypothesis(
                project.hypothesis, project.methodology.approach
            )
            ai_response = {
                "hypothesis": project.hypothesis,
                "issues": issues,
                "is_valid": len(issues) == 0,
                "message": "Formulación de hipótesis/supuestos registrada.",
            }

        elif step == AdvisorStep.METHODOLOGY_DESIGN:
            if safe_input:
                prompt = METHODOLOGY_DESIGN_PROMPT.format(
                    academic_level=project.academic_level.value,
                    research_question=project.research_question,
                    general_objective=project.general_objective,
                    user_input=safe_input,
                    approach=project.methodology.approach.value
                    if project.methodology.approach
                    else "cuantitativo",
                )
                try:
                    ai_response = await self.llm.complete_json(prompt, system_prompt=system_prompt)
                    if not project.methodology.design and ai_response.get("design"):
                        project.methodology.design = ai_response["design"]
                    if not project.methodology.population and ai_response.get("population"):
                        project.methodology.population = ai_response["population"]
                    if not project.methodology.sample and ai_response.get("sample"):
                        project.methodology.sample = ai_response["sample"]
                    if not project.methodology.instruments and ai_response.get("instruments"):
                        project.methodology.instruments = ai_response["instruments"]
                    if not project.methodology.analysis_technique and ai_response.get(
                        "analysis_technique"
                    ):
                        project.methodology.analysis_technique = ai_response["analysis_technique"]
                except Exception as e:
                    logger.warning(
                        "Methodology design fallback to direct form.", extra={"error": str(e)}
                    )
                    ai_response = {"design": project.methodology.design}

            epistem_issues = MethodologyValidator.validate_epistemological_alignment(
                project.methodology.paradigm.value if project.methodology.paradigm else None,
                project.methodology.approach,
                project.methodology.design,
            )
            if not ai_response:
                ai_response = {
                    "design": project.methodology.design,
                    "approach": project.methodology.approach.value
                    if project.methodology.approach
                    else "cuantitativo",
                    "issues": epistem_issues,
                    "is_valid": len(epistem_issues) == 0,
                    "message": "Diseño metodológico registrado correctamente.",
                }
            else:
                ai_response["issues"] = epistem_issues
                ai_response["is_valid"] = len(epistem_issues) == 0

        elif step == AdvisorStep.CONSISTENCY_AUDIT:
            if safe_input:
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
            else:
                local_audit = MethodologyValidator.audit_project(project)
                ai_response = {
                    "score": local_audit["score"],
                    "status": local_audit["status"],
                    "verdict": "Auditoría determinista completada.",
                    "flaws": local_audit["issues"],
                    "is_consistent": local_audit["is_consistent"],
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

        # Idempotent phase progression: transition forward if in SETUP or ORIENTATION
        if project.phase in (ProjectPhase.SETUP, ProjectPhase.ORIENTATION):
            project.phase = ProjectPhase.CONTEXT
            await self.repo.update_project(project)
            logger.info(
                "Project methodology approved and transitioned to CONTEXT phase.",
                extra={"project_id": project.id},
            )
        else:
            logger.info(
                "Project methodology already approved.",
                extra={"project_id": project.id, "current_phase": project.phase.value},
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
