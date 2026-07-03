"""Read layer for cash: register visibility, balances and turnover (no writes)."""
from __future__ import annotations

import calendar
import datetime as dt
from decimal import Decimal

from django.db.models import DecimalField, Q, QuerySet, Sum, Value
from django.db.models.functions import Coalesce

from apps.core.enums import TxKind
from apps.core.money import ZERO

from .models import CashOperation, CashRegister

_ZERO = Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2))


def registers_qs() -> QuerySet[CashRegister]:
    return CashRegister.objects.select_related("business")


def registers_visible_to(user) -> QuerySet[CashRegister]:
    """Isolation (КАС-04): finance staff / owners / superuser see all registers;
    a cashier sees only registers where they are responsible."""
    qs = registers_qs()
    if user is None or not getattr(user, "is_authenticated", False):
        return qs.none()
    if user.is_superuser or user.is_finance_staff:
        return qs
    return qs.filter(responsible=user).distinct()


def operations_qs() -> QuerySet[CashOperation]:
    return CashOperation.objects.select_related(
        "register", "register__business", "finance_transaction"
    )


def register_balance(register_id: int) -> Decimal:
    """Balance of a register = sum(income) − sum(expense) of live operations."""
    agg = CashOperation.objects.filter(register_id=register_id).aggregate(
        income=Coalesce(Sum("amount", filter=Q(kind=TxKind.INCOME)), _ZERO),
        expense=Coalesce(Sum("amount", filter=Q(kind=TxKind.EXPENSE)), _ZERO),
    )
    return (agg["income"] or ZERO) - (agg["expense"] or ZERO)


def register_turnover(
    register_id: int,
    *,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> Decimal:
    """Оборот (КАС-03): sum of ALL operation amounts in the window (income + expense)."""
    qs = CashOperation.objects.filter(register_id=register_id)
    if date_from is not None:
        qs = qs.filter(occurred_on__gte=date_from)
    if date_to is not None:
        qs = qs.filter(occurred_on__lte=date_to)
    return qs.aggregate(total=Coalesce(Sum("amount"), _ZERO))["total"] or ZERO


def month_turnover(register_id: int, on_date: dt.date) -> Decimal:
    """Turnover within the calendar month of ``on_date`` (КАС-03 window)."""
    start = on_date.replace(day=1)
    last_day = calendar.monthrange(on_date.year, on_date.month)[1]
    end = on_date.replace(day=last_day)
    return register_turnover(register_id, date_from=start, date_to=end)


def register_balances(
    *,
    user=None,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> list[dict]:
    """Per-register balance + turnover rows (feeds the cash report ФНС-11).

    When ``user`` is given, restricts to registers visible to that user (КАС-04).
    """
    qs = registers_visible_to(user) if user is not None else registers_qs()
    rows: list[dict] = []
    for reg in qs:
        rows.append(
            {
                "register_id": reg.id,
                "register_name": reg.name,
                "business_id": reg.business_id,
                "business_name": reg.business.name,
                "balance": register_balance(reg.id),
                "turnover": register_turnover(
                    reg.id, date_from=date_from, date_to=date_to
                ),
                "limit": reg.turnover_limit,
            }
        )
    return rows
