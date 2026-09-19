"""Unit tests for structured JSON logging and redaction."""

import json
import logging

from thesisforge.core.logging import (
    StructuredJsonFormatter,
    get_logger,
    redact_sensitive_dict,
    sanitize_log_message,
)


def test_sanitize_log_message_non_string():
    """Test sanitizing non-string objects."""
    res = sanitize_log_message(12345)  # type: ignore[arg-type]
    assert res == "12345"


def test_redact_sensitive_dict():
    """Test deep redaction of sensitive key-value pairs in dictionaries and lists."""
    sample_data = {
        "api_key": "secret_key_value",
        "nested": {
            "password": "super_secret_pwd",
            "username": "oscar",
            "token_list": ["clean_token", "Bearer sk-1234567890abcdef123456"],
        },
        "count": 42,
    }

    cleaned = redact_sensitive_dict(sample_data)
    assert cleaned["api_key"] == "[REDACTED]"
    assert cleaned["nested"]["password"] == "[REDACTED]"
    assert cleaned["nested"]["username"] == "oscar"
    assert cleaned["count"] == 42


def test_structured_json_formatter():
    """Test StructuredJsonFormatter output format."""
    formatter = StructuredJsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Execution started",
        args=(),
        exc_info=None,
    )
    record.custom_field = "custom_value"  # type: ignore[attr-defined]
    record.secret_dict = {"api_key": "my_secret"}  # type: ignore[attr-defined]

    formatted_str = formatter.format(record)
    parsed = json.loads(formatted_str)

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"
    assert parsed["message"] == "Execution started"
    assert parsed["custom_field"] == "custom_value"
    assert parsed["secret_dict"]["api_key"] == "[REDACTED]"


def test_get_logger():
    """Test get_logger singleton helper."""
    logger = get_logger("thesisforge.test_instantiation")
    assert logger.name == "thesisforge.test_instantiation"
    assert len(logger.handlers) >= 1
