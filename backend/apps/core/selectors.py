"""Shared read helpers usable by any domain (period parsing, etc.)."""
from __future__ import annotations

import datetime as dt


def parse_date(value: str | None) -> dt.date | None:
    if not value:
        return None
    return dt.date.fromisoformat(value)


def parse_period(query_params) -> tuple[dt.date | None, dt.date | None]:
    """Read ``date_from`` / ``date_to`` (ISO ``YYYY-MM-DD``) from query params.

    Returns ``(None, None)`` when absent — callers treat that as "all time".
    """
    date_from = parse_date(query_params.get("date_from"))
    date_to = parse_date(query_params.get("date_to"))
    return date_from, date_to
