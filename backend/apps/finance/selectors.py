"""Read layer for finance: queries and aggregations (no writes)."""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

from django.db.models import DecimalField, Q, QuerySet, Sum, Value
from django.db.models.functions import Coalesce

from apps.core.enums import TxKind, TxStatus
from apps.core.money import ZERO

from .models import Transaction

_ZERO = Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2))


def transactions_qs() -> QuerySet[Transaction]:
    return Transaction.objects.select_related("business", "category", "site_object")


def confirmed_qs() -> QuerySet[Transaction]:
    return transactions_qs().filter(status=TxStatus.CONFIRMED)


def business_totals(
    *,
    business_id: int | None = None,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    include_barter: bool = False,
) -> dict[str, Decimal]:
    """Confirmed income / expense / profit for a business over a period (ФНС-04).

    Barter is excluded from revenue/expense totals by default (БЕТ-62).
    """
    qs = confirmed_qs()
    if business_id is not None:
        qs = qs.filter(business_id=business_id)
    if date_from is not None:
        qs = qs.filter(occurred_on__gte=date_from)
    if date_to is not None:
        qs = qs.filter(occurred_on__lte=date_to)
    if not include_barter:
        qs = qs.filter(is_barter=False)

    agg = qs.aggregate(
        income=Coalesce(Sum("amount", filter=Q(kind=TxKind.INCOME)), _ZERO),
        expense=Coalesce(Sum("amount", filter=Q(kind=TxKind.EXPENSE)), _ZERO),
    )
    income = agg["income"] or ZERO
    expense = agg["expense"] or ZERO
    return {"income": income, "expense": expense, "profit": income - expense}


def profit_by_business(
    *, date_from: dt.date | None = None, date_to: dt.date | None = None
) -> list[dict]:
    """Income/expense/profit grouped by business (ФНС-04, feeds reports ФНС-10)."""
    qs = confirmed_qs().filter(is_barter=False)
    if date_from is not None:
        qs = qs.filter(occurred_on__gte=date_from)
    if date_to is not None:
        qs = qs.filter(occurred_on__lte=date_to)

    rows = (
        qs.values("business_id", "business__name")
        .annotate(
            income=Coalesce(Sum("amount", filter=Q(kind=TxKind.INCOME)), _ZERO),
            expense=Coalesce(Sum("amount", filter=Q(kind=TxKind.EXPENSE)), _ZERO),
        )
        .order_by("business__name")
    )
    result = []
    for r in rows:
        income = r["income"] or ZERO
        expense = r["expense"] or ZERO
        result.append(
            {
                "business_id": r["business_id"],
                "business_name": r["business__name"],
                "income": income,
                "expense": expense,
                "profit": income - expense,
            }
        )
    return result
