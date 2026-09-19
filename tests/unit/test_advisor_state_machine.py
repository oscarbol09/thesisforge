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


def test_calculate_progress_with_skipped_steps():
    """Test progress calculation when qualitative/mixed methodologies skip hypothesis."""
    skipped = [AdvisorStep.HYPOTHESIS]
    # Total active steps = 8 (SETUP, TOPIC, PROBLEM, QUESTION, OBJECTIVES, METHODOLOGY, AUDIT, APPROVED)
    assert AdvisorStateMachine.calculate_progress(AdvisorStep.SETUP, skipped_steps=skipped) == 0
    assert (
        AdvisorStateMachine.calculate_progress(AdvisorStep.OBJECTIVES, skipped_steps=skipped) == 57
    )
    assert (
        AdvisorStateMachine.calculate_progress(
            AdvisorStep.METHODOLOGY_DESIGN, skipped_steps=skipped
        )
        == 71
    )
    assert (
        AdvisorStateMachine.calculate_progress(AdvisorStep.APPROVED, skipped_steps=skipped) == 100
    )


def test_next_and_previous_steps():
    """Test navigating through linear interview steps."""
    next_step = AdvisorStateMachine.get_next_step(AdvisorStep.SETUP)
    assert next_step == AdvisorStep.TOPIC_AND_AREA

    prev_step = AdvisorStateMachine.get_previous_step(AdvisorStep.TOPIC_AND_AREA)
    assert prev_step == AdvisorStep.SETUP


def test_next_and_previous_steps_with_skipped():
    """Test navigating steps when HYPOTHESIS is skipped."""
    skipped = [AdvisorStep.HYPOTHESIS]
    next_step = AdvisorStateMachine.get_next_step(AdvisorStep.OBJECTIVES, skipped_steps=skipped)
    assert next_step == AdvisorStep.METHODOLOGY_DESIGN

    prev_step = AdvisorStateMachine.get_previous_step(
        AdvisorStep.METHODOLOGY_DESIGN, skipped_steps=skipped
    )
    assert prev_step == AdvisorStep.OBJECTIVES


def test_validate_transition_allowed():
    """Test allowed transitions (step forward or any backward)."""
    assert (
        AdvisorStateMachine.validate_transition(AdvisorStep.SETUP, AdvisorStep.TOPIC_AND_AREA)
        is True
    )
    assert (
        AdvisorStateMachine.validate_transition(AdvisorStep.OBJECTIVES, AdvisorStep.SETUP) is True
    )


def test_validate_transition_allowed_with_skipped_steps():
    """Test transition from OBJECTIVES to METHODOLOGY_DESIGN when HYPOTHESIS is skipped."""
    assert (
        AdvisorStateMachine.validate_transition(
            AdvisorStep.OBJECTIVES,
            AdvisorStep.METHODOLOGY_DESIGN,
            skipped_steps=[AdvisorStep.HYPOTHESIS],
        )
        is True
    )


def test_validate_transition_disallowed_skip():
    """Test that jumping ahead multiple unskipped steps raises InvalidPhaseTransitionError."""
    with pytest.raises(InvalidPhaseTransitionError):
        AdvisorStateMachine.validate_transition(AdvisorStep.SETUP, AdvisorStep.METHODOLOGY_DESIGN)
