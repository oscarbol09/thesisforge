"""Domain exception hierarchy for ThesisForge."""


class ThesisForgeError(Exception):
    """Base domain exception for all ThesisForge application errors."""

    def __init__(self, message: str, details: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SecurityError(ThesisForgeError):
    """Raised on security policy or AppSec validation failures."""


class SSRFBlockedError(SecurityError):
    """Raised when an outbound URL violates SSRF boundaries."""


class KeyVaultError(SecurityError):
    """Raised when encryption or decryption operations fail in LocalKeyVault."""


class ProjectNotFoundError(ThesisForgeError):
    """Raised when a requested project ID does not exist in the repository."""


class InvalidPhaseTransitionError(ThesisForgeError):
    """Raised when a state transition is not allowed by the methodology flow."""


class MethodologyValidationError(ThesisForgeError):
    """Raised when scientific consistency validation fails between problem/objectives/hypothesis."""


class ConfigurationError(ThesisForgeError):
    """Raised when application or provider configuration is missing or invalid."""


class LLMProviderError(ThesisForgeError):
    """Raised when an LLM provider call fails or exhausts retry attempts."""


class RAGSearchError(ThesisForgeError):
    """Raised when academic literature retrieval or indexing fails."""


class AcademicAPIError(RAGSearchError):
    """Raised when an external academic API (Semantic Scholar, CrossRef, ArXiv) fails."""


class DocumentProcessingError(ThesisForgeError):
    """Raised when document parsing, text extraction, or chunking encounters an unrecoverable error."""


class RAGIndexError(ThesisForgeError):
    """Raised when indexing or querying vector embeddings in vector stores fails."""


class CitationValidationError(ThesisForgeError):
    """Raised when citation format, DOI validation, or academic metadata verification fails."""


class SectionNotFoundError(ThesisForgeError):
    """Raised when a specific chapter or section draft ID does not exist in the project."""


class ExportError(ThesisForgeError):
    """Raised when document compilation, DOCX formatting, or export pipeline fails."""


class JuryEvaluationError(ThesisForgeError):
    """Raised when multi-agent jury evaluation or thesis audit execution encounters a failure."""


class DefenseSessionError(ThesisForgeError):
    """Raised when thesis oral defense session orchestration or state update fails."""


class DefenseTurnNotFoundError(DefenseSessionError):
    """Raised when an requested defense turn index is invalid or does not exist."""
