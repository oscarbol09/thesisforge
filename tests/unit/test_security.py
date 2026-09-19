"""Unit tests for security components: SSRF Guard, LocalKeyVault, and Logging."""

import pytest

from thesisforge.core.logging import sanitize_log_message
from thesisforge.core.security import LocalKeyVault, assert_safe_academic_url
from thesisforge.exceptions import KeyVaultError, SSRFBlockedError


def test_keyvault_encryption_roundtrip(vault: LocalKeyVault):
    """Test encrypting and decrypting arbitrary secrets."""
    original_secret = "sk-ant-api03-abcdef1234567890-XYZ!@#$_ñáéíóú"
    encrypted = vault.encrypt(original_secret)

    assert encrypted != original_secret
    assert isinstance(encrypted, str)

    decrypted = vault.decrypt(encrypted)
    assert decrypted == original_secret


def test_keyvault_empty_strings(vault: LocalKeyVault):
    """Test handling of empty secrets."""
    assert vault.encrypt("") == ""
    assert vault.decrypt("") == ""


def test_keyvault_tampered_token_fails(vault: LocalKeyVault):
    """Test that tampering with cipher text raises KeyVaultError."""
    token = vault.encrypt("secret_data")
    tampered = token[:-4] + "AAAA"

    with pytest.raises(KeyVaultError):
        vault.decrypt(tampered)


def test_keyvault_wrong_key_fails(master_key: str):
    """Test decryption with a different key raises KeyVaultError."""
    vault1 = LocalKeyVault(master_key)
    other_key = LocalKeyVault.generate_key()
    vault2 = LocalKeyVault(other_key)

    token = vault1.encrypt("confidential_password")
    with pytest.raises(KeyVaultError):
        vault2.decrypt(token)


def test_keyvault_invalid_master_key():
    """Test initializing vault with an invalid key string fails."""
    with pytest.raises(KeyVaultError):
        LocalKeyVault("not_a_valid_fernet_key")


@pytest.mark.parametrize(
    "blocked_url",
    [
        "http://127.0.0.1:8000/api",
        "http://127.0.0.1",
        "http://localhost:3000",
        "http://10.0.0.1/admin",
        "http://192.168.1.100/data",
        "http://172.16.0.5/status",
        "http://169.254.169.254/latest/meta-data",
        "http://[::1]/secret",
        "file:///etc/passwd",
        "ftp://internal-server.local",
        "javascript:alert(1)",
        "",
        "   ",
    ],
)
def test_ssrf_blocks_insecure_urls(blocked_url: str):
    """Test that SSRF guard blocks internal, private, metadata, and invalid protocol URLs."""
    with pytest.raises(SSRFBlockedError):
        assert_safe_academic_url(blocked_url)


def test_log_sanitizer_crlf_and_secrets():
    """Test that log sanitizer strips newlines and redacts secrets."""
    dirty_log = "User logged in\r\nBearer sk-ant-secret-api-key-1234567890abcdef\nNext line"
    cleaned = sanitize_log_message(dirty_log)

    assert "\r" not in cleaned
    assert "\n" not in cleaned
    assert "sk-ant-secret-api-key-1234567890abcdef" not in cleaned
    assert "[REDACTED_SECRET]" in cleaned


def test_keyvault_properties_and_bytes_init(master_key: str):
    """Test initializing vault with bytes and checking property getters."""
    vault = LocalKeyVault(master_key.encode("utf-8"))
    assert isinstance(vault.key_bytes, bytes)
    assert vault.key_str == master_key


def test_assert_safe_academic_url_allowed(monkeypatch: pytest.MonkeyPatch):
    """Test that valid public academic URLs pass SSRF validation."""
    # Mock DNS lookup to return a known safe public IP
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda host, port, proto: [(2, 1, 6, "", ("142.250.190.46", 443))],
    )

    url = "https://api.semanticscholar.org/graph/v1/paper/search?query=RAG"
    validated = assert_safe_academic_url(url)
    assert validated == url
