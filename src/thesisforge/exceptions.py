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
