"""State machine and step transitions for the Methodological Advisory Interview."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from thesisforge.exceptions import InvalidPhaseTransitionError


class AdvisorStep(str, Enum):
    """Sequential steps of the methodological advisory interview."""

    SETUP = "setup"
    TOPIC_AND_AREA = "topic_and_area"
    PROBLEM_STATEMENT = "problem_statement"
    RESEARCH_QUESTION = "research_question"
    OBJECTIVES = "objectives"
    HYPOTHESIS = "hypothesis"
    METHODOLOGY_DESIGN = "methodology_design"
    CONSISTENCY_AUDIT = "consistency_audit"
    APPROVED = "approved"


# Linear transition order
ADVISOR_STEP_ORDER: list[AdvisorStep] = [
    AdvisorStep.SETUP,
    AdvisorStep.TOPIC_AND_AREA,
    AdvisorStep.PROBLEM_STATEMENT,
    AdvisorStep.RESEARCH_QUESTION,
    AdvisorStep.OBJECTIVES,
    AdvisorStep.HYPOTHESIS,
    AdvisorStep.METHODOLOGY_DESIGN,
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
    """Controls and validates step progression during the interview."""

    @staticmethod
    def calculate_progress(
        step: AdvisorStep, skipped_steps: list[AdvisorStep] | None = None
    ) -> int:
        """Calculate percentage completion based on step and optional skipped steps."""
        try:
            skipped = skipped_steps or []
            effective_steps = [s for s in ADVISOR_STEP_ORDER if s not in skipped]
            if not effective_steps:
                return 0
            if step not in effective_steps:
                curr_idx = ADVISOR_STEP_ORDER.index(step)
                passed = len(
                    [s for s in effective_steps if ADVISOR_STEP_ORDER.index(s) <= curr_idx]
                )
                total = len(effective_steps) - 1
                return int((passed / total) * 100) if total > 0 else 100
            index = effective_steps.index(step)
            total = len(effective_steps) - 1
            return int((index / total) * 100) if total > 0 else 100
        except ValueError:
            return 0

    @staticmethod
    def get_next_step(
        current_step: AdvisorStep, skipped_steps: list[AdvisorStep] | None = None
    ) -> AdvisorStep:
        """Get the immediate next active step in the pipeline."""
        try:
            skipped = skipped_steps or []
            curr_idx = ADVISOR_STEP_ORDER.index(current_step)
            for step in ADVISOR_STEP_ORDER[curr_idx + 1 :]:
                if step not in skipped:
                    return step
            return current_step
        except ValueError as err:
            raise InvalidPhaseTransitionError(f"Paso '{current_step}' desconocido.") from err

    @staticmethod
    def get_previous_step(
        current_step: AdvisorStep, skipped_steps: list[AdvisorStep] | None = None
    ) -> AdvisorStep:
        """Get the immediate previous active step for review/rollback."""
        try:
            skipped = skipped_steps or []
            curr_idx = ADVISOR_STEP_ORDER.index(current_step)
            for step in reversed(ADVISOR_STEP_ORDER[:curr_idx]):
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
    ) -> bool:
        """Ensure transitions only go forward sequentially (skipping bypassed steps) or backward for revision."""
        if from_step == to_step:
            return True

        skipped = skipped_steps or []
        from_idx = ADVISOR_STEP_ORDER.index(from_step)
        to_idx = ADVISOR_STEP_ORDER.index(to_step)

        # Allow moving backward anytime
        if to_idx < from_idx:
            return True

        # Allow advancing if all intermediate steps between from_idx and to_idx are skipped
        intermediates = ADVISOR_STEP_ORDER[from_idx + 1 : to_idx]
        if all(s in skipped for s in intermediates):
            return True

        raise InvalidPhaseTransitionError(
            f"Transición no permitida desde '{from_step.value}' hasta '{to_step.value}'. Debe completarse el paso intermedio."
        )
