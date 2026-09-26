"""Strict UTC time handling utilities."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current datetime with timezone set to UTC."""
    return datetime.now(UTC)


def format_iso_utc(dt: datetime | None = None) -> str:
    """Format a datetime as an ISO-8601 string in UTC. If None, uses utc_now()."""
    target = dt or utc_now()
    target = target.replace(tzinfo=UTC) if target.tzinfo is None else target.astimezone(UTC)
    return target.isoformat()


def parse_iso_utc(iso_str: str) -> datetime:
    """Parse an ISO-8601 string into a UTC-aware datetime object."""
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)
