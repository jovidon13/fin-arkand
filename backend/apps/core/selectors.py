"""Shared read helpers usable by any domain (period parsing, etc.)."""
from __future__ import annotations

import datetime as dt

from apps.core.exceptions import DomainError


def parse_date(value: str | None) -> dt.date | None:
    """Parse an ISO ``YYYY-MM-DD`` string; a malformed value is a 400, not a 500."""
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        raise DomainError(
            "invalid_date",
            f"Неверный формат даты: {value!r} (ожидается YYYY-MM-DD)",
        ) from None


def parse_period(query_params) -> tuple[dt.date | None, dt.date | None]:
    """Read ``date_from`` / ``date_to`` (ISO ``YYYY-MM-DD``) from query params.

    Returns ``(None, None)`` when absent — callers treat that as "all time".
    """
    date_from = parse_date(query_params.get("date_from"))
    date_to = parse_date(query_params.get("date_to"))
    return date_from, date_to


def parse_int_param(query_params, name: str) -> int | None:
    """Read an optional integer query param; a non-numeric value is a 400, not a 500."""
    raw = query_params.get(name)
    if raw in (None, ""):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise DomainError(
            "invalid_param", f"Параметр «{name}» должен быть числом"
        ) from None
