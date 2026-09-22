"""Multi-agent thesis jury evaluation and interactive socratic defense module."""

from thesisforge.jury.defense import ThesisDefenseSimulator
from thesisforge.jury.evaluator import MultiAgentJuryEngine
from thesisforge.jury.service import JuryService

__all__ = [
    "JuryService",
    "MultiAgentJuryEngine",
    "ThesisDefenseSimulator",
]
