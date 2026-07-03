"""
Write layer for finance: all business logic + transactions live here.

Financial invariants enforced:
  * every mutation is atomic (`transaction.atomic`);
  * confirmation locks the row (`select_for_update`) against races;
  * confirmation is idempotent (repeat → no second effect);
  * every money/status change is written to the audit log.
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.core.enums import TxKind, TxStatus
from apps.core.exceptions import DomainError
from apps.core.money import money

from .models import Transaction


def _snapshot(tx: Transaction) -> dict:
    return {
        "status": tx.status,
        "amount": str(tx.amount),
        "kind": tx.kind,
        "confirmed_by": tx.confirmed_by_id,
    }


@transaction.atomic
def create_transaction(
    *,
    business_id: int,
    kind: str,
    amount: Decimal,
    method: str,
    occurred_on: dt.date,
    actor,
    category_id: int | None = None,
    site_object_id: int | None = None,
    counterparty: str = "",
    note: str = "",
    is_barter: bool = False,
    source: str = "",
    status: str = TxStatus.PENDING,
) -> Transaction:
    """Create a transaction (ФНС-01/02/03).

    Expenses require an article (ФНС-02). Incomes start as ``pending`` and need
    a financier's confirmation (ФНС-01); an explicit ``status`` may seed
    already-confirmed rows (used by the seed command).
    """
    amount = money(amount)
    if amount <= 0:
        raise DomainError("amount_not_positive", "Сумма должна быть больше нуля")
    if kind == TxKind.EXPENSE and category_id is None:
        raise DomainError("category_required", "Для расхода обязательна статья (ФНС-02)")

    tx = Transaction.objects.create(
        business_id=business_id,
        kind=kind,
        category_id=category_id,
        amount=amount,
        method=method,
        status=status,
        occurred_on=occurred_on,
        site_object_id=site_object_id,
        counterparty=counterparty,
        note=note,
        is_barter=is_barter,
        source=source,
        created_by=actor if getattr(actor, "pk", None) else None,
    )
    if status == TxStatus.CONFIRMED:
        tx.confirmed_by = actor if getattr(actor, "pk", None) else None
        tx.confirmed_at = timezone.now()
        tx.save(update_fields=["confirmed_by", "confirmed_at", "updated_at"])

    AuditLog.record(actor, "tx.created", tx, after=_snapshot(tx))
    return tx


@transaction.atomic
def confirm_transaction(*, tx_id: int, actor, idempotency_key: str | None = None) -> Transaction:
    """Confirm an income/expense (ФНС-01). Idempotent: re-confirming a already
    confirmed transaction is a no-op that returns the same record."""
    tx = Transaction.objects.select_for_update().get(pk=tx_id)

    if tx.status == TxStatus.CONFIRMED:
        return tx  # idempotent — no second effect
    if tx.status in (TxStatus.REJECTED, TxStatus.VOID):
        raise DomainError(
            "tx_not_confirmable",
            f"Транзакцию в статусе «{tx.get_status_display()}» нельзя подтвердить",
        )

    before = _snapshot(tx)
    tx.status = TxStatus.CONFIRMED
    tx.confirmed_by = actor if getattr(actor, "pk", None) else None
    tx.confirmed_at = timezone.now()
    tx.save(update_fields=["status", "confirmed_by", "confirmed_at", "updated_at"])

    AuditLog.record(actor, "tx.confirmed", tx, before=before, after=_snapshot(tx),
                    meta={"idempotency_key": idempotency_key})
    return tx


@transaction.atomic
def reject_transaction(*, tx_id: int, actor, reason: str = "") -> Transaction:
    tx = Transaction.objects.select_for_update().get(pk=tx_id)
    if tx.status == TxStatus.CONFIRMED:
        raise DomainError("tx_already_confirmed", "Подтверждённую транзакцию нельзя отклонить")
    if tx.status == TxStatus.REJECTED:
        return tx
    before = _snapshot(tx)
    tx.status = TxStatus.REJECTED
    tx.save(update_fields=["status", "updated_at"])
    AuditLog.record(actor, "tx.rejected", tx, before=before, after=_snapshot(tx),
                    meta={"reason": reason})
    return tx


@transaction.atomic
def void_transaction(*, tx_id: int, actor, reason: str = "") -> Transaction:
    """Void a confirmed transaction (soft-delete for reversals)."""
    tx = Transaction.objects.select_for_update().get(pk=tx_id)
    if tx.status == TxStatus.VOID:
        return tx
    before = _snapshot(tx)
    tx.status = TxStatus.VOID
    tx.save(update_fields=["status", "updated_at"])
    AuditLog.record(actor, "tx.voided", tx, before=before, after=_snapshot(tx),
                    meta={"reason": reason})
    return tx
