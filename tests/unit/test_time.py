"""Unit tests for time utilities."""

from datetime import UTC, datetime

from thesisforge.core.time import format_iso_utc, parse_iso_utc, utc_now


def test_utc_now():
    """Ensure utc_now returns UTC timezone-aware datetime."""
    now = utc_now()
    assert now.tzinfo is not None
    assert now.tzinfo == UTC


def test_format_iso_utc():
    """Test format_iso_utc with None and specific datetimes."""
    res_none = format_iso_utc(None)
    assert "+00:00" in res_none or "Z" in res_none

    naive = datetime(2026, 1, 15, 10, 30, 0)
    res_naive = format_iso_utc(naive)
    assert res_naive == "2026-01-15T10:30:00+00:00"

    aware = datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC)
    res_aware = format_iso_utc(aware)
    assert res_aware == "2026-01-15T10:30:00+00:00"


def test_parse_iso_utc():
    """Test parse_iso_utc on ISO formatted strings."""
    parsed = parse_iso_utc("2026-01-15T10:30:00+00:00")
    assert parsed.year == 2026
    assert parsed.tzinfo == UTC

    parsed_naive = parse_iso_utc("2026-01-15T10:30:00")
    assert parsed_naive.tzinfo == UTC
