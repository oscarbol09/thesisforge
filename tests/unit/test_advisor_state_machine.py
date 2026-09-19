"""Unit tests for Advisor State Machine."""

import pytest

from thesisforge.advisor.state_machine import (
    AdvisorStateMachine,
    AdvisorStep,
)
from thesisforge.exceptions import InvalidPhaseTransitionError


def test_calculate_progress():
    """Test progress percentage calculations."""
    assert AdvisorStateMachine.calculate_progress(AdvisorStep.SETUP) == 0
    assert AdvisorStateMachine.calculate_progress(AdvisorStep.APPROVED) == 100
    assert AdvisorStateMachine.calculate_progress(AdvisorStep.OBJECTIVES) == 50


def test_next_and_previous_steps():
    """Test navigating through linear interview steps."""
    next_step = AdvisorStateMachine.get_next_step(AdvisorStep.SETUP)
    assert next_step == AdvisorStep.TOPIC_AND_AREA

    prev_step = AdvisorStateMachine.get_previous_step(AdvisorStep.TOPIC_AND_AREA)
    assert prev_step == AdvisorStep.SETUP


def test_validate_transition_allowed():
    """Test allowed transitions (step forward or any backward)."""
    assert (
        AdvisorStateMachine.validate_transition(AdvisorStep.SETUP, AdvisorStep.TOPIC_AND_AREA)
        is True
    )
    assert (
        AdvisorStateMachine.validate_transition(AdvisorStep.OBJECTIVES, AdvisorStep.SETUP) is True
    )


def test_validate_transition_disallowed_skip():
    """Test that jumping ahead multiple steps raises InvalidPhaseTransitionError."""
    with pytest.raises(InvalidPhaseTransitionError):
        AdvisorStateMachine.validate_transition(AdvisorStep.SETUP, AdvisorStep.METHODOLOGY_DESIGN)
