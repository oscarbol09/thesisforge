"""LLM BYOK routing and prompts module."""

from thesisforge.llm.prompts import (
    ADVISOR_SYSTEM_PROMPT,
    CONSISTENCY_AUDIT_PROMPT,
    METHODOLOGY_DESIGN_PROMPT,
    OBJECTIVES_PROMPT,
    PROBLEM_FORMULATION_PROMPT,
)
from thesisforge.llm.router import LLMRouter

__all__ = [
    "LLMRouter",
    "ADVISOR_SYSTEM_PROMPT",
    "PROBLEM_FORMULATION_PROMPT",
    "OBJECTIVES_PROMPT",
    "METHODOLOGY_DESIGN_PROMPT",
    "CONSISTENCY_AUDIT_PROMPT",
]
