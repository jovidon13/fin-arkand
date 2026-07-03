"""
Write layer for cash: all business logic + transactions live here (КАС-01…04).

Financial invariants enforced:
  * every mutation is atomic (`transaction.atomic`);
  * the mutable register row is locked with `select_for_update()` so concurrent
    postings cannot race past the turnover limit (КАС-03);
  * money is always Decimal via `money()`; amounts must be strictly positive;
  * every money/status change is written to the audit log in the same transaction.
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

from django.db import transaction
from rest_framework import status

from apps.audit.models import AuditLog
from apps.core.exceptions import DomainError
from apps.core.idempotency import run_idempotent
from apps.core.money import money

from . import selectors
from .models import CashOperation, CashRegister


def _lock_register(register_id: int) -> CashRegister:
    """Fetch + lock a register, mapping a missing id to a 404 DomainError
    (not an unhandled 500)."""
    try:
        return CashRegister.objects.select_for_update().get(pk=register_id)
    except CashRegister.DoesNotExist:
        raise DomainError(
            "cash_register_not_found", "Касса не найдена",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from None


def _op_snapshot(op: CashOperation) -> dict:
    return {
        "register": op.register_id,
        "kind": op.kind,
        "amount": str(op.amount),
        "method": op.method,
        "occurred_on": op.occurred_on.isoformat(),
        "is_deleted": op.is_deleted,
    }


@transaction.atomic
def add_operation(
    *,
    register_id: int,
    kind: str,
    amount: Decimal,
    method: str,
    occurred_on: dt.date,
    actor,
    counterparty: str = "",
    note: str = "",
    idempotency_key: str | None = None,
) -> CashOperation:
    """Post an income/expense to a register (КАС-02), respecting the turnover
    limit (КАС-03).

    The register row is locked for the duration of the transaction so the limit
    check and the insert cannot be interleaved by a concurrent posting. A repeat
    with the same ``idempotency_key`` returns the original operation.
    """
    amount = money(amount)
    if amount <= 0:
        raise DomainError("amount_not_positive", "Сумма должна быть больше нуля")

    def _create() -> CashOperation:
        register = _lock_register(register_id)

        # КАС-03: enforce the monthly turnover limit (0 = без лимита).
        if register.turnover_limit > 0:
            turnover = selectors.month_turnover(register_id, occurred_on)
            projected = turnover + amount
            if projected > register.turnover_limit:
                raise DomainError(
                    "cash_limit_exceeded",
                    "Превышен лимит оборота кассы",
                    details={
                        "register_id": register_id,
                        "limit": str(register.turnover_limit),
                        "current_turnover": str(turnover),
                        "amount": str(amount),
                        "projected_turnover": str(projected),
                    },
                )

        op = CashOperation.objects.create(
            register=register,
            kind=kind,
            amount=amount,
            method=method,
            occurred_on=occurred_on,
            counterparty=counterparty,
            note=note,
            created_by=actor if getattr(actor, "pk", None) else None,
        )
        AuditLog.record(actor, "cash.operation.added", op, after=_op_snapshot(op))
        return op

    return run_idempotent(
        scope="cash.add_operation",
        key=idempotency_key,
        create=_create,
        fetch=lambda pk: CashOperation.objects.get(pk=pk),
    )


@transaction.atomic
def set_turnover_limit(*, register_id: int, limit, actor) -> CashRegister:
    """Change a register's turnover limit (КАС-03). 0 = без лимита."""
    register = _lock_register(register_id)
    limit = money(limit)
    if limit < 0:
        raise DomainError("limit_negative", "Лимит не может быть отрицательным")

    before = {"turnover_limit": str(register.turnover_limit)}
    register.turnover_limit = limit
    register.save(update_fields=["turnover_limit", "updated_at"])
    AuditLog.record(
        actor, "cash.limit.changed", register,
        before=before, after={"turnover_limit": str(register.turnover_limit)},
    )
    return register


@transaction.atomic
def void_operation(*, operation_id: int, actor, reason: str = "") -> CashOperation:
    """Void (soft-delete) a cash operation — reversals never physically delete."""
    # Use ``all_objects`` so an already-voided (soft-deleted) row is still found;
    # the default ``objects`` manager hides ``is_deleted`` rows, which would make
    # the idempotency guard below unreachable and raise ``DoesNotExist`` instead.
    op = CashOperation.all_objects.select_for_update().get(pk=operation_id)
    if op.is_deleted:
        return op  # idempotent — already voided
    before = _op_snapshot(op)
    op.soft_delete(actor if getattr(actor, "pk", None) else None)
    AuditLog.record(
        actor, "cash.operation.voided", op,
        before=before, after=_op_snapshot(op), meta={"reason": reason},
    )
    return op
