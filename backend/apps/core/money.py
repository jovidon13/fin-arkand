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
