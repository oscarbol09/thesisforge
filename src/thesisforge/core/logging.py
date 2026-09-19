"""Structured JSON logging with CWE-117 sanitization and secret redaction."""

import json
import logging
import re
from collections.abc import Mapping
from typing import Any

from thesisforge.core.time import format_iso_utc

# Regex for common secret patterns (API keys, bearer tokens, passwords)
SECRET_PATTERNS = [
    re.compile(r"(sk-[a-zA-Z0-9_-]{20,})", re.IGNORECASE),
    re.compile(r"(ghp_[a-zA-Z0-9]{36,})", re.IGNORECASE),
    re.compile(r"(gho_[a-zA-Z0-9]{36,})", re.IGNORECASE),
    re.compile(r"(AIza[0-9A-Za-z-_]{35})", re.IGNORECASE),
    re.compile(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),
    re.compile(r"(keyvault:[a-zA-Z0-9_\-\+=]{20,})", re.IGNORECASE),
]

SENSITIVE_FIELD_NAMES = {
    "api_key",
    "password",
    "secret",
    "token",
    "authorization",
    "master_key",
    "private_key",
}


def sanitize_log_message(msg: object) -> str:
    """Sanitize log string against CWE-117 (CRLF injection) and mask secrets."""
    msg_str = str(msg) if msg is not None else ""
    # Neutralize CRLF and control characters
    sanitized = msg_str.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    for pattern in SECRET_PATTERNS:
        sanitized = pattern.sub(r"[REDACTED_SECRET]", sanitized)
    return sanitized


def redact_sensitive_dict(data: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively redact sensitive key-value pairs from dictionary logs."""
    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        if any(s in key.lower() for s in SENSITIVE_FIELD_NAMES):
            cleaned[key] = "[REDACTED]"
        elif isinstance(value, Mapping):
            cleaned[key] = redact_sensitive_dict(value)
        elif isinstance(value, str):
            cleaned[key] = sanitize_log_message(value)
        elif isinstance(value, list):
            cleaned[key] = [
                redact_sensitive_dict(item)
                if isinstance(item, Mapping)
                else (sanitize_log_message(item) if isinstance(item, str) else item)
                for item in value
            ]
        else:
            cleaned[key] = value
    return cleaned


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: dict[str, Any] = {
            "timestamp": format_iso_utc(),
            "level": record.levelname,
            "logger": record.name,
            "message": sanitize_log_message(record.getMessage()),
        }

        if record.exc_info and record.exc_text:
            log_payload["exception"] = sanitize_log_message(record.exc_text)

        # Include structured extra fields if provided
        for key, value in record.__dict__.items():
            if key not in {
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "id",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
            }:
                if isinstance(value, Mapping):
                    log_payload[key] = redact_sensitive_dict(value)
                elif isinstance(value, str):
                    log_payload[key] = sanitize_log_message(value)
                else:
                    log_payload[key] = value

        return json.dumps(log_payload, ensure_ascii=False)


def get_logger(name: str = "thesisforge", level: int = logging.INFO) -> logging.Logger:
    """Obtain or configure a structured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False
    return logger
