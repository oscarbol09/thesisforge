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
    step_history: dict[str, str] = Field(default_factory=dict)
    can_advance: bool = False
    progress_percentage: int = 0


class AdvisorStateMachine:
    """Controls and validates step progression during the interview."""

    @staticmethod
    def calculate_progress(step: AdvisorStep) -> int:
        """Calculate percentage completion based on step."""
        try:
            index = ADVISOR_STEP_ORDER.index(step)
            return int((index / (len(ADVISOR_STEP_ORDER) - 1)) * 100)
        except ValueError:
            return 0

    @staticmethod
    def get_next_step(current_step: AdvisorStep) -> AdvisorStep:
        """Get the immediate next step in the pipeline."""
        try:
            curr_idx = ADVISOR_STEP_ORDER.index(current_step)
            if curr_idx < len(ADVISOR_STEP_ORDER) - 1:
                return ADVISOR_STEP_ORDER[curr_idx + 1]
            return current_step
        except ValueError as err:
            raise InvalidPhaseTransitionError(f"Paso '{current_step}' desconocido.") from err

    @staticmethod
    def get_previous_step(current_step: AdvisorStep) -> AdvisorStep:
        """Get the immediate previous step for review/rollback."""
        try:
            curr_idx = ADVISOR_STEP_ORDER.index(current_step)
            if curr_idx > 0:
                return ADVISOR_STEP_ORDER[curr_idx - 1]
            return current_step
        except ValueError as err:
            raise InvalidPhaseTransitionError(f"Paso '{current_step}' desconocido.") from err

    @classmethod
    def validate_transition(cls, from_step: AdvisorStep, to_step: AdvisorStep) -> bool:
        """Ensure transitions only go forward sequentially or backward for revision."""
        if from_step == to_step:
            return True

        from_idx = ADVISOR_STEP_ORDER.index(from_step)
        to_idx = ADVISOR_STEP_ORDER.index(to_step)

        # Allow moving backward anytime
        if to_idx < from_idx:
            return True

        # Allow advancing only to the next step
        if to_idx == from_idx + 1:
            return True

        raise InvalidPhaseTransitionError(
            f"Transición no permitida desde '{from_step.value}' hasta '{to_step.value}'. Debe completarse el paso intermedio."
        )
