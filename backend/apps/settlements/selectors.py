"""Read layer for settlements: queries and aggregations (no writes)."""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

from django.db.models import QuerySet

from apps.core.enums import DebtStatus
from apps.core.money import ZERO

from .models import Debt, ExternalDebt, Settlement, Transfer


def transfers_qs() -> QuerySet[Transfer]:
    return Transfer.objects.select_related(
        "from_business", "to_business", "created_by", "approved_by"
    )


def debts_qs() -> QuerySet[Debt]:
    return Debt.objects.select_related("debtor", "creditor", "source_transfer")


def settlements_qs() -> QuerySet[Settlement]:
    return Settlement.objects.select_related(
        "debt", "debt__debtor", "debt__creditor", "counter_debt", "created_by"
    )


def open_debts() -> QuerySet[Debt]:
    """All debts not yet fully settled (БАР-02)."""
    return debts_qs().exclude(status=DebtStatus.SETTLED)


def debt_registry(
    *,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    include_settled: bool = False,
) -> list[dict]:
    """Transparent debt register (БАР-02 / ХОЛ-31; feeds report ФНС-12).

    Returns rows with debtor/creditor identity, the outstanding balance and the
    original amount. Fully-closed debts (``outstanding == 0``) are excluded
    unless ``include_settled``.
    """
    qs = debts_qs()
    if not include_settled:
        qs = qs.filter(outstanding__gt=ZERO)
    if date_from is not None:
        qs = qs.filter(occurred_on__gte=date_from)
    if date_to is not None:
        qs = qs.filter(occurred_on__lte=date_to)

    rows: list[dict] = []
    for debt in qs.order_by("debtor__name", "creditor__name", "-occurred_on"):
        rows.append(
            {
                "debt_id": debt.id,
                "debtor_id": debt.debtor_id,
                "debtor_name": debt.debtor.name,
                "creditor_id": debt.creditor_id,
                "creditor_name": debt.creditor.name,
                "outstanding": debt.outstanding,
                "amount": debt.amount,
                "is_barter": debt.is_barter,
                "occurred_on": debt.occurred_on,
                "status": debt.status,
            }
        )
    return rows


def net_between(business_a_id: int, business_b_id: int) -> Decimal:
    """Net outstanding between two businesses (БАР-03).

    Positive result → A owes B on balance; negative → B owes A. Computed as
    (A-owes-B) minus (B-owes-A) over all non-settled debts.
    """
    a_owes_b = ZERO
    b_owes_a = ZERO
    qs = debts_qs().exclude(status=DebtStatus.SETTLED).filter(
        debtor_id__in=(business_a_id, business_b_id),
        creditor_id__in=(business_a_id, business_b_id),
    )
    for debt in qs:
        if debt.debtor_id == business_a_id and debt.creditor_id == business_b_id:
            a_owes_b += debt.outstanding
        elif debt.debtor_id == business_b_id and debt.creditor_id == business_a_id:
            b_owes_a += debt.outstanding
    return a_owes_b - b_owes_a


# --------------------------------------------------------------------------- #
# External receivables / payables (дебиторка / кредиторка)
# --------------------------------------------------------------------------- #
def external_debts_qs() -> QuerySet[ExternalDebt]:
    return ExternalDebt.objects.select_related("business", "created_by")


def external_registry(
    *, direction: str, include_settled: bool = False
) -> list[dict]:
    """Rows for one side (receivable / payable) with the outstanding balance."""
    qs = external_debts_qs().filter(direction=direction)
    if not include_settled:
        qs = qs.filter(outstanding__gt=ZERO)
    rows: list[dict] = []
    for d in qs.order_by("-outstanding", "-occurred_on"):
        rows.append(
            {
                "id": d.id,
                "direction": d.direction,
                "counterparty": d.counterparty,
                "business_id": d.business_id,
                "business_name": d.business.name if d.business_id else None,
                "amount": d.amount,
                "outstanding": d.outstanding,
                "status": d.status,
                "occurred_on": d.occurred_on,
                "due_on": d.due_on,
                "note": d.note,
            }
        )
    return rows


def external_summary() -> dict:
    """Totals + lists for both sides — feeds the dashboard дебиторка block."""
    from apps.core.enums import ExternalDebtDirection

    receivables = external_registry(direction=ExternalDebtDirection.RECEIVABLE)
    payables = external_registry(direction=ExternalDebtDirection.PAYABLE)
    total_receivable = sum((Decimal(r["outstanding"]) for r in receivables), ZERO)
    total_payable = sum((Decimal(r["outstanding"]) for r in payables), ZERO)
    return {
        "receivables": receivables,
        "payables": payables,
        "total_receivable": total_receivable,
        "total_payable": total_payable,
        "net": total_receivable - total_payable,
    }
