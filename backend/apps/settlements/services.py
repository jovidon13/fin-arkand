"""
Write layer for settlements: all business logic + transactions live here
(БАР-01…04 / ХОЛ-30…33).

Financial invariants enforced:
  * every mutation is atomic (``transaction.atomic``);
  * mutable money rows (transfers, debts) are locked with ``select_for_update``;
  * transfer approval is idempotent (repeat → same debt, no duplicate);
  * every money/status change is written to the audit log.
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import status

from apps.audit.models import AuditLog
from apps.core.enums import DebtStatus, SettlementKind, TransferStatus
from apps.core.exceptions import DomainError
from apps.core.idempotency import run_idempotent
from apps.core.money import ZERO, money

from .models import Debt, Settlement, Transfer


def _transfer_snapshot(t: Transfer) -> dict:
    return {
        "status": t.status,
        "amount": str(t.amount),
        "from_business": t.from_business_id,
        "to_business": t.to_business_id,
        "approved_by": t.approved_by_id,
        "is_barter": t.is_barter,
    }


def _debt_snapshot(d: Debt) -> dict:
    return {
        "status": d.status,
        "amount": str(d.amount),
        "outstanding": str(d.outstanding),
        "debtor": d.debtor_id,
        "creditor": d.creditor_id,
    }


def _debt_status_for(outstanding: Decimal, original: Decimal) -> str:
    """Derive a debt status from its remaining balance (БАР-03)."""
    if outstanding <= ZERO:
        return DebtStatus.SETTLED
    if outstanding < original:
        return DebtStatus.PARTIALLY_SETTLED
    return DebtStatus.OPEN


@transaction.atomic
def create_transfer(
    *,
    from_business_id: int,
    to_business_id: int,
    amount: Decimal,
    occurred_on: dt.date,
    actor,
    description: str = "",
    is_barter: bool = False,
    idempotency_key: str | None = None,
) -> Transfer:
    """Register a value hand-off between two businesses (БАР-01 / ХОЛ-30).

    Created ``pending``; a debt is only booked on approval. Businesses must
    differ and the amount must be positive. A repeat with the same
    ``idempotency_key`` returns the original transfer.
    """
    amount = money(amount)
    if amount <= ZERO:
        raise DomainError("amount_not_positive", "Сумма должна быть больше нуля")
    if from_business_id == to_business_id:
        raise DomainError(
            "same_business",
            "Передача возможна только между разными бизнесами",
        )

    def _create() -> Transfer:
        transfer = Transfer.objects.create(
            from_business_id=from_business_id,
            to_business_id=to_business_id,
            amount=amount,
            description=description,
            occurred_on=occurred_on,
            is_barter=is_barter,
            status=TransferStatus.PENDING,
            created_by=actor if getattr(actor, "pk", None) else None,
        )
        AuditLog.record(
            actor, "transfer.created", transfer, after=_transfer_snapshot(transfer)
        )
        return transfer

    return run_idempotent(
        scope="settlements.create_transfer",
        key=idempotency_key,
        create=_create,
        fetch=lambda pk: Transfer.objects.get(pk=pk),
    )


@transaction.atomic
def approve_transfer(*, transfer_id: int, actor) -> Debt:
    """Approve a transfer and auto-book the debt (БАР-01 / ХОЛ-30).

    Idempotent: approving an already-approved transfer returns the existing
    debt without creating a duplicate. A rejected transfer cannot be approved.
    The debt is owed by the receiver (``to_business``) to the sender
    (``from_business``).
    """
    transfer = Transfer.objects.select_for_update().get(pk=transfer_id)

    if transfer.status == TransferStatus.APPROVED:
        # Idempotent — return the debt already booked for this transfer.
        return Debt.objects.get(source_transfer=transfer)
    if transfer.status == TransferStatus.REJECTED:
        raise DomainError(
            "transfer_rejected", "Отклонённую передачу нельзя одобрить"
        )

    before = _transfer_snapshot(transfer)
    transfer.status = TransferStatus.APPROVED
    transfer.approved_by = actor if getattr(actor, "pk", None) else None
    transfer.approved_at = timezone.now()
    transfer.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])

    debt = Debt.objects.create(
        debtor_id=transfer.to_business_id,
        creditor_id=transfer.from_business_id,
        amount=transfer.amount,
        outstanding=transfer.amount,
        status=DebtStatus.OPEN,
        is_barter=transfer.is_barter,
        source_transfer=transfer,
        occurred_on=transfer.occurred_on,
    )

    AuditLog.record(
        actor, "transfer.approved", transfer,
        before=before, after=_transfer_snapshot(transfer),
        meta={"debt_id": debt.id},
    )
    AuditLog.record(actor, "debt.created", debt, after=_debt_snapshot(debt))
    return debt


@transaction.atomic
def reject_transfer(*, transfer_id: int, actor, reason: str = "") -> Transfer:
    """Reject a pending transfer (БАР-01). Idempotent for already-rejected rows;
    an approved transfer cannot be rejected (its debt already exists)."""
    transfer = Transfer.objects.select_for_update().get(pk=transfer_id)

    if transfer.status == TransferStatus.APPROVED:
        raise DomainError(
            "transfer_already_approved",
            "Одобренную передачу нельзя отклонить",
        )
    if transfer.status == TransferStatus.REJECTED:
        return transfer

    before = _transfer_snapshot(transfer)
    transfer.status = TransferStatus.REJECTED
    transfer.save(update_fields=["status", "updated_at"])
    AuditLog.record(
        actor, "transfer.rejected", transfer,
        before=before, after=_transfer_snapshot(transfer), meta={"reason": reason},
    )
    return transfer


@transaction.atomic
def settle_debt(
    *,
    debt_id: int,
    kind: str,
    amount: Decimal,
    actor,
    occurred_on: dt.date,
    counter_debt_id: int | None = None,
    note: str = "",
    idempotency_key: str | None = None,
) -> Settlement:
    """Close (fully or partially) a debt (БАР-03 / ХОЛ-32).

    Reduces ``outstanding`` by ``amount`` and flips status to
    ``partially_settled`` / ``settled``. For ``netting`` with a ``counter_debt``
    the counter obligation is reduced symmetrically (взаимозачёт). All mutable
    debt rows are locked for the duration of the transaction. A repeat with the
    same ``idempotency_key`` returns the original settlement (no double-close).
    """
    amount = money(amount)
    if amount <= ZERO:
        raise DomainError("amount_not_positive", "Сумма должна быть больше нуля")

    def _create() -> Settlement:
        try:
            debt = Debt.objects.select_for_update().get(pk=debt_id)
        except Debt.DoesNotExist:
            raise DomainError(
                "debt_not_found", "Долг не найден",
                status_code=status.HTTP_404_NOT_FOUND,
            ) from None
        if debt.outstanding <= ZERO:
            raise DomainError("debt_already_settled", "Долг уже полностью закрыт")
        if amount > debt.outstanding:
            raise DomainError(
                "settle_exceeds_outstanding",
                "Сумма закрытия превышает остаток долга",
                details={"outstanding": str(debt.outstanding), "amount": str(amount)},
            )

        counter_debt: Debt | None = None
        if kind == SettlementKind.NETTING:
            # Взаимозачёт (БАР-03 / ХОЛ-32): требуется реальный встречный долг тех же
            # двух бизнесов в обратную сторону — иначе можно ошибочно погасить чужой долг.
            if counter_debt_id is None:
                raise DomainError(
                    "counter_debt_required",
                    "Для взаимозачёта нужно указать встречный долг",
                )
            if counter_debt_id == debt_id:
                raise DomainError(
                    "counter_debt_self", "Нельзя зачесть долг сам с собой"
                )
            try:
                counter_debt = Debt.objects.select_for_update().get(pk=counter_debt_id)
            except Debt.DoesNotExist:
                raise DomainError(
                    "counter_debt_not_found", "Встречный долг не найден",
                    status_code=status.HTTP_404_NOT_FOUND,
                ) from None
            if (
                counter_debt.debtor_id != debt.creditor_id
                or counter_debt.creditor_id != debt.debtor_id
            ):
                raise DomainError(
                    "counter_debt_not_reciprocal",
                    "Взаимозачёт возможен только со встречным долгом тех же двух бизнесов",
                )
            if counter_debt.outstanding < amount:
                raise DomainError(
                    "counter_debt_insufficient",
                    "Остаток встречного долга меньше суммы взаимозачёта",
                    details={
                        "counter_outstanding": str(counter_debt.outstanding),
                        "amount": str(amount),
                    },
                )

        before = _debt_snapshot(debt)
        debt.outstanding = money(debt.outstanding - amount)
        debt.status = _debt_status_for(debt.outstanding, debt.amount)
        debt.save(update_fields=["outstanding", "status", "updated_at"])

        settlement = Settlement.objects.create(
            debt=debt,
            kind=kind,
            amount=amount,
            counter_debt=counter_debt,
            note=note,
            occurred_on=occurred_on,
            created_by=actor if getattr(actor, "pk", None) else None,
        )

        AuditLog.record(
            actor, "debt.settled", debt,
            before=before, after=_debt_snapshot(debt),
            meta={"settlement_id": settlement.id, "kind": kind, "amount": str(amount)},
        )

        if counter_debt is not None:
            counter_before = _debt_snapshot(counter_debt)
            counter_debt.outstanding = money(counter_debt.outstanding - amount)
            counter_debt.status = _debt_status_for(
                counter_debt.outstanding, counter_debt.amount
            )
            counter_debt.save(update_fields=["outstanding", "status", "updated_at"])
            AuditLog.record(
                actor, "debt.settled", counter_debt,
                before=counter_before, after=_debt_snapshot(counter_debt),
                meta={
                    "settlement_id": settlement.id,
                    "kind": kind,
                    "amount": str(amount),
                    "netting_with": debt.id,
                },
            )

        return settlement

    return run_idempotent(
        scope="settlements.settle_debt",
        key=idempotency_key,
        create=_create,
        fetch=lambda pk: Settlement.objects.get(pk=pk),
    )


@transaction.atomic
def create_barter(
    *,
    from_business_id: int,
    to_business_id: int,
    amount: Decimal,
    occurred_on: dt.date,
    actor,
    description: str = "",
    idempotency_key: str | None = None,
) -> Transfer:
    """Register a barter exchange (БАР-04 / ХОЛ-33).

    Convenience wrapper over :func:`create_transfer` with ``is_barter=True``.
    Under accountant control; still books a debt on approval.
    """
    return create_transfer(
        from_business_id=from_business_id,
        to_business_id=to_business_id,
        amount=amount,
        occurred_on=occurred_on,
        actor=actor,
        description=description,
        is_barter=True,
        idempotency_key=idempotency_key,
    )
