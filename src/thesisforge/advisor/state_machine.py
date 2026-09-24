"""State machine and step transitions for the Methodological Advisory Interview."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from thesisforge.exceptions import InvalidPhaseTransitionError


class AdvisorStep(str, Enum):
    """Sequential and approach-aware steps of the methodological advisory interview."""

    SETUP = "setup"
    TOPIC_AND_AREA = "topic_and_area"
    PARADIGM_AND_APPROACH = "paradigm_and_approach"
    PROBLEM_STATEMENT = "problem_statement"
    RESEARCH_QUESTION = "research_question"
    OBJECTIVES = "objectives"
    HYPOTHESIS = "hypothesis"
    OPERATIONALIZATION = "operationalization"
    CATEGORIES = "categories"
    METHODOLOGY_DESIGN = "methodology_design"
    ETHICS_AND_SAMPLING = "ethics_and_sampling"
    CONSISTENCY_AUDIT = "consistency_audit"
    APPROVED = "approved"


# Global canonical sequence
ADVISOR_STEP_ORDER: list[AdvisorStep] = [
    AdvisorStep.SETUP,
    AdvisorStep.TOPIC_AND_AREA,
    AdvisorStep.PARADIGM_AND_APPROACH,
    AdvisorStep.PROBLEM_STATEMENT,
    AdvisorStep.RESEARCH_QUESTION,
    AdvisorStep.OBJECTIVES,
    AdvisorStep.HYPOTHESIS,
    AdvisorStep.OPERATIONALIZATION,
    AdvisorStep.CATEGORIES,
    AdvisorStep.METHODOLOGY_DESIGN,
    AdvisorStep.ETHICS_AND_SAMPLING,
    AdvisorStep.CONSISTENCY_AUDIT,
    AdvisorStep.APPROVED,
]


class AdvisorStateDTO(BaseModel):
    """Current progression state of the advisory interview."""

    model_config = ConfigDict(extra="forbid")

    current_step: AdvisorStep = AdvisorStep.SETUP
    completed_steps: list[AdvisorStep] = Field(default_factory=list)
    skipped_steps: list[AdvisorStep] = Field(default_factory=list)
    step_history: dict[str, str] = Field(default_factory=dict)
    can_advance: bool = False
    progress_percentage: int = 0


class AdvisorStateMachine:
    """Controls, validates, and routes step progression during the methodological interview."""

    @classmethod
    def get_step_sequence_for_approach(
        cls, approach: str | None = None
    ) -> list[AdvisorStep]:
        """Derive specialized linear sequence tailored to Quantitative, Qualitative, or Mixed paradigm."""
        if not approach:
            return list(ADVISOR_STEP_ORDER)

        normalized = str(approach).lower().strip()
        if "cualitativ" in normalized:
            # Qualitative research: omit quantitative hypothesis and numerical operationalization
            return [
                AdvisorStep.SETUP,
                AdvisorStep.TOPIC_AND_AREA,
                AdvisorStep.PARADIGM_AND_APPROACH,
                AdvisorStep.PROBLEM_STATEMENT,
                AdvisorStep.RESEARCH_QUESTION,
                AdvisorStep.OBJECTIVES,
                AdvisorStep.CATEGORIES,
                AdvisorStep.METHODOLOGY_DESIGN,
                AdvisorStep.ETHICS_AND_SAMPLING,
                AdvisorStep.CONSISTENCY_AUDIT,
                AdvisorStep.APPROVED,
            ]
        elif "cuantitativ" in normalized:
            # Quantitative research: omit qualitative emerging categories
            return [
                AdvisorStep.SETUP,
                AdvisorStep.TOPIC_AND_AREA,
                AdvisorStep.PARADIGM_AND_APPROACH,
                AdvisorStep.PROBLEM_STATEMENT,
                AdvisorStep.RESEARCH_QUESTION,
                AdvisorStep.OBJECTIVES,
                AdvisorStep.HYPOTHESIS,
                AdvisorStep.OPERATIONALIZATION,
                AdvisorStep.METHODOLOGY_DESIGN,
                AdvisorStep.ETHICS_AND_SAMPLING,
                AdvisorStep.CONSISTENCY_AUDIT,
                AdvisorStep.APPROVED,
            ]
        elif "mixt" in normalized:
            # Mixed methods: include both hypothesis and categorical matrix
            return list(ADVISOR_STEP_ORDER)

        return list(ADVISOR_STEP_ORDER)

    @classmethod
    def calculate_progress(
        cls,
        step: AdvisorStep,
        skipped_steps: list[AdvisorStep] | None = None,
        step_order: list[AdvisorStep] | None = None,
    ) -> int:
        """Calculate percentage completion based on step, approach-specific sequence, and skipped steps."""
        base_order = step_order or ADVISOR_STEP_ORDER
        skipped = skipped_steps or []
        effective_steps = [s for s in base_order if s not in skipped]

        if not effective_steps:
            return 0

        if step == AdvisorStep.APPROVED:
            return 100

        try:
            if step not in effective_steps:
                curr_idx = base_order.index(step)
                passed = len([s for s in effective_steps if base_order.index(s) <= curr_idx])
                total = len(effective_steps) - 1
                return int((passed / total) * 100) if total > 0 else 100

            index = effective_steps.index(step)
            total = len(effective_steps) - 1
            return int((index / total) * 100) if total > 0 else 100
        except ValueError:
            return 0

    @classmethod
    def get_next_step(
        cls,
        current_step: AdvisorStep,
        skipped_steps: list[AdvisorStep] | None = None,
        step_order: list[AdvisorStep] | None = None,
    ) -> AdvisorStep:
        """Get immediate next active step in the approach-specific pipeline."""
        base_order = step_order or ADVISOR_STEP_ORDER
        skipped = skipped_steps or []
        try:
            curr_idx = base_order.index(current_step)
            for step in base_order[curr_idx + 1 :]:
                if step not in skipped:
                    return step
            return current_step
        except ValueError as err:
            raise InvalidPhaseTransitionError(f"Paso '{current_step}' desconocido.") from err

    @classmethod
    def get_previous_step(
        cls,
        current_step: AdvisorStep,
        skipped_steps: list[AdvisorStep] | None = None,
        step_order: list[AdvisorStep] | None = None,
    ) -> AdvisorStep:
        """Get immediate previous active step for review/rollback."""
        base_order = step_order or ADVISOR_STEP_ORDER
        skipped = skipped_steps or []
        try:
            curr_idx = base_order.index(current_step)
            for step in reversed(base_order[:curr_idx]):
                if step not in skipped:
                    return step
            return current_step
        except ValueError as err:
            raise InvalidPhaseTransitionError(f"Paso '{current_step}' desconocido.") from err

    @classmethod
    def validate_transition(
        cls,
        from_step: AdvisorStep,
        to_step: AdvisorStep,
        skipped_steps: list[AdvisorStep] | None = None,
        step_order: list[AdvisorStep] | None = None,
    ) -> bool:
        """Ensure transitions only go forward sequentially (skipping bypassed steps) or backward for revision."""
        if from_step == to_step:
            return True

        base_order = step_order or ADVISOR_STEP_ORDER
        skipped = skipped_steps or []
        try:
            from_idx = base_order.index(from_step)
            to_idx = base_order.index(to_step)
        except ValueError as err:
            raise InvalidPhaseTransitionError(f"Paso inválido en transición: {err}") from err

        # Allow moving backward anytime
        if to_idx < from_idx:
            return True

        # Allow advancing if all intermediate steps between from_idx and to_idx are skipped
        intermediates = base_order[from_idx + 1 : to_idx]
        if all(s in skipped for s in intermediates):
            return True

        raise InvalidPhaseTransitionError(
            f"Transición no permitida desde '{from_step.value}' hasta '{to_step.value}'. Debe completarse el paso intermedio."
        )


get_step_sequence_for_approach = AdvisorStateMachine.get_step_sequence_for_approach
