"""
Money helpers. Money is ALWAYS ``Decimal`` quantized to 2 decimal places —
never float (design doc, financial invariants).
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

Number = int | str | float | Decimal

#: Canonical zero amount.
ZERO = Decimal("0.00")

#: Quantum for holding currency (сомони) — 2 decimal places.
_CENTS = Decimal("0.01")


def money(value: Number) -> Decimal:
    """Coerce any numeric-like value to a 2-dp ``Decimal``.

    ``float`` is accepted for convenience (e.g. seed data) but immediately
    stringified to avoid binary-float representation error before quantizing.
    """
    if isinstance(value, float):
        value = str(value)
    return Decimal(value).quantize(_CENTS, rounding=ROUND_HALF_UP)


def is_positive(value: Number) -> bool:
    return money(value) > ZERO


def stringify(value):
    """Recursively convert ``Decimal`` amounts to 2-dp strings for JSON output.

    Money in JSON is always a string with two decimals (money invariant): a raw
    ``Decimal`` in a Response would otherwise be rendered as a float by DRF, and
    an un-quantized aggregate (e.g. ``Decimal("30500")``) would serialize as
    ``"30500"`` instead of ``"30500.00"``. Use at the API boundary for payloads
    built from selectors that return plain dicts/lists.
    """
    if isinstance(value, Decimal):
        return str(money(value))
    if isinstance(value, dict):
        return {k: stringify(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [stringify(v) for v in value]
    return value
