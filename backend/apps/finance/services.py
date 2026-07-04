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
from apps.core.idempotency import run_idempotent
from apps.core.money import money

from .models import Transaction


def _snapshot(tx: Transaction) -> dict:
    return {
        "status": tx.status,
        "amount": str(tx.amount),
        "kind": tx.kind,
        "checked_by": tx.checked_by_id,
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
    is_disbursement: bool = False,
    recipient_manager_id: int | None = None,
    status: str = TxStatus.PENDING,
    idempotency_key: str | None = None,
) -> Transaction:
    """Create a transaction (ФНС-01/02/03).

    Expenses require an article (ФНС-02) — except «выдача руководителю»
    (``is_disbursement``), which is booked as an expense to an owner without a
    statutory article. Operations start ``pending`` and go through the two-stage
    chain (менеджер → бухгалтер → владелец); an explicit ``status`` may seed
    already-confirmed rows (used by the seed command). A repeated request with
    the same ``idempotency_key`` returns the original row (no duplicate).
    """
    amount = money(amount)
    if amount <= 0:
        raise DomainError("amount_not_positive", "Сумма должна быть больше нуля")
    if is_disbursement:
        kind = TxKind.EXPENSE  # a disbursement is money leaving the business
    if kind == TxKind.EXPENSE and category_id is None and not is_disbursement:
        raise DomainError("category_required", "Для расхода обязательна статья (ФНС-02)")

    def _create() -> Transaction:
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
            is_disbursement=is_disbursement,
            recipient_manager_id=recipient_manager_id,
            created_by=actor if getattr(actor, "pk", None) else None,
        )
        if status == TxStatus.CONFIRMED:
            tx.confirmed_by = actor if getattr(actor, "pk", None) else None
            tx.confirmed_at = timezone.now()
            tx.save(update_fields=["confirmed_by", "confirmed_at", "updated_at"])

        AuditLog.record(actor, "tx.created", tx, after=_snapshot(tx))
        return tx

    return run_idempotent(
        scope="finance.create_transaction",
        key=idempotency_key,
        create=_create,
        fetch=lambda pk: Transaction.objects.get(pk=pk),
    )


@transaction.atomic
def check_transaction(*, tx_id: int, actor, idempotency_key: str | None = None) -> Transaction:
    """Accountant check — второй шаг цепочки (проверил бухгалтер).

    A ``pending`` operation is verified by the accountant. If it is «крупная»
    (сумма выше порога бизнеса, ХОЛ-21) it moves to ``awaiting_owner`` and still
    needs the owner's подтверждение; otherwise it is confirmed outright. Idempotent
    — re-checking an already-processed row is a no-op.
    """
    tx = Transaction.objects.select_for_update().select_related("business").get(pk=tx_id)

    if tx.status in (TxStatus.CONFIRMED, TxStatus.AWAITING_OWNER):
        return tx  # idempotent — already checked
    if tx.status in (TxStatus.REJECTED, TxStatus.VOID):
        raise DomainError(
            "tx_not_checkable",
            f"Операцию в статусе «{tx.get_status_display()}» нельзя проверить",
        )

    before = _snapshot(tx)
    tx.checked_by = actor if getattr(actor, "pk", None) else None
    tx.checked_at = timezone.now()
    if tx.requires_owner:
        tx.status = TxStatus.AWAITING_OWNER
        event = "tx.checked"
    else:
        tx.status = TxStatus.CONFIRMED  # мелкая — бухгалтер закрывает сразу
        event = "tx.confirmed"
    tx.save(update_fields=["status", "checked_by", "checked_at", "updated_at"])

    AuditLog.record(actor, event, tx, before=before, after=_snapshot(tx),
                    meta={"idempotency_key": idempotency_key, "stage": "accountant"})
    return tx


@transaction.atomic
def confirm_transaction(*, tx_id: int, actor, idempotency_key: str | None = None) -> Transaction:
    """Final confirmation (ФНС-01). Owners подтверждают крупные операции
    (``awaiting_owner``); финансисты/админ могут подтвердить и напрямую. Idempotent:
    re-confirming an already confirmed transaction is a no-op."""
    tx = Transaction.objects.select_for_update().select_related("business").get(pk=tx_id)

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
                    meta={"idempotency_key": idempotency_key, "stage": "owner"})
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
