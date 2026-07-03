"""Read layer for payroll: queries and aggregations (no writes) — ЗРП, ФНС-13."""
from __future__ import annotations

from decimal import Decimal

from django.db.models import DecimalField, QuerySet, Sum, Value
from django.db.models.functions import Coalesce

from apps.core.enums import PayrollStatus
from apps.core.money import ZERO

from .models import Employee, PayrollItem, PayrollRun

_ZERO = Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2))

#: Runs whose items count towards the payroll fund (ФНС-13).
_FUND_STATUSES = (PayrollStatus.CALCULATED, PayrollStatus.APPROVED, PayrollStatus.PAID)


def employees_qs() -> QuerySet[Employee]:
    return Employee.objects.select_related("business", "scheme", "user")


def runs_qs() -> QuerySet[PayrollRun]:
    return PayrollRun.objects.select_related("created_by", "approved_by")


def items_qs() -> QuerySet[PayrollItem]:
    return PayrollItem.objects.select_related(
        "run", "employee", "employee__business"
    )


def run_total(run_id: int) -> Decimal:
    """Sum of item totals for a run (independent recompute of ``run.total``)."""
    agg = PayrollItem.objects.filter(run_id=run_id).aggregate(
        total=Coalesce(Sum("total_amount"), _ZERO)
    )
    return agg["total"] or ZERO


def payroll_fund(
    *, year: int | None = None, month: int | None = None, business_id: int | None = None
) -> Decimal:
    """Payroll fund (ФОТ) for a period — ФНС-13.

    Sum of ``total_amount`` of items belonging to runs that are CALCULATED,
    APPROVED or PAID for the given period. Optionally scoped to one business.
    """
    qs = PayrollItem.objects.filter(run__status__in=_FUND_STATUSES)
    if year is not None:
        qs = qs.filter(run__year=year)
    if month is not None:
        qs = qs.filter(run__month=month)
    if business_id is not None:
        qs = qs.filter(employee__business_id=business_id)

    agg = qs.aggregate(fund=Coalesce(Sum("total_amount"), _ZERO))
    return agg["fund"] or ZERO


def fund_by_business(*, year: int | None = None, month: int | None = None) -> list[dict]:
    """Payroll fund grouped by business for a period (ФНС-13, feeds reports)."""
    qs = PayrollItem.objects.filter(run__status__in=_FUND_STATUSES)
    if year is not None:
        qs = qs.filter(run__year=year)
    if month is not None:
        qs = qs.filter(run__month=month)

    rows = (
        qs.values("employee__business_id", "employee__business__name")
        .annotate(fund=Coalesce(Sum("total_amount"), _ZERO))
        .order_by("employee__business__name")
    )
    return [
        {
            "business_id": r["employee__business_id"],
            "business_name": r["employee__business__name"],
            "fund": r["fund"] or ZERO,
        }
        for r in rows
    ]
