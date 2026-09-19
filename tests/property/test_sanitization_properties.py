"""Property-based tests using Hypothesis for sanitization and encryption invariants."""

from hypothesis import given, settings
from hypothesis import strategies as st

from thesisforge.core.logging import sanitize_log_message
from thesisforge.core.security import LocalKeyVault


@given(st.text())
@settings(max_examples=100)
def test_property_keyvault_roundtrip_invariant(text_secret: str):
    """Property Invariant: For all possible strings, decrypt(encrypt(s)) == s."""
    vault = LocalKeyVault()
    encrypted = vault.encrypt(text_secret)
    decrypted = vault.decrypt(encrypted)
    assert decrypted == text_secret


@given(st.text())
@settings(max_examples=100)
def test_property_log_sanitization_crlf_invariant(arbitrary_message: str):
    """Property Invariant: Output of sanitize_log_message NEVER contains raw CR or LF characters."""
    sanitized = sanitize_log_message(arbitrary_message)
    assert "\r" not in sanitized
    assert "\n" not in sanitized
