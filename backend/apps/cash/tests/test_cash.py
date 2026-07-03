import datetime as dt
from decimal import Decimal

import pytest

from apps.accounts.models import RoleCode
from apps.audit.models import AuditLog
from apps.cash import selectors, services
from apps.cash.tests.factories import CashOperationFactory, CashRegisterFactory
from apps.core.enums import PayMethod, TxKind
from apps.core.exceptions import DomainError
from apps.core.tests.factories import RoleFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_turnover_limit_blocks_over_limit_operation():
    """КАС-03: an operation pushing monthly оборот past the limit is blocked."""
    actor = UserFactory()
    register = CashRegisterFactory(turnover_limit=Decimal("1000"))
    today = dt.date.today()

    # Within limit: 600 of turnover so far.
    services.add_operation(
        register_id=register.id, kind=TxKind.INCOME, amount=Decimal("600"),
        method=PayMethod.CASH, occurred_on=today, actor=actor,
    )

    # 600 + 500 = 1100 > 1000 → blocked.
    with pytest.raises(DomainError) as exc:
        services.add_operation(
            register_id=register.id, kind=TxKind.EXPENSE, amount=Decimal("500"),
            method=PayMethod.CASH, occurred_on=today, actor=actor,
        )
    assert exc.value.code == "cash_limit_exceeded"


def test_no_limit_when_zero():
    """КАС-03: turnover_limit == 0 means без лимита."""
    actor = UserFactory()
    register = CashRegisterFactory(turnover_limit=0)
    op = services.add_operation(
        register_id=register.id, kind=TxKind.INCOME, amount=Decimal("999999"),
        method=PayMethod.CASH, occurred_on=dt.date.today(), actor=actor,
    )
    assert op.amount == Decimal("999999.00")


def test_register_balance_income_minus_expense():
    """Balance = sum(income) − sum(expense)."""
    register = CashRegisterFactory(turnover_limit=0)
    CashOperationFactory(register=register, kind=TxKind.INCOME, amount=Decimal("1000"))
    CashOperationFactory(register=register, kind=TxKind.INCOME, amount=Decimal("250"))
    CashOperationFactory(register=register, kind=TxKind.EXPENSE, amount=Decimal("300"))

    assert selectors.register_balance(register.id) == Decimal("950.00")


def test_isolation_cashier_sees_only_own_register():
    """КАС-04: a cashier responsible for register A does not see register B;
    finance staff sees both."""
    cashier = UserFactory(role=RoleFactory(code=RoleCode.CASHIER))
    finance = UserFactory(role=RoleFactory(code=RoleCode.CHIEF_ACCOUNTANT))

    register_a = CashRegisterFactory(responsible=[cashier])
    register_b = CashRegisterFactory()

    cashier_ids = set(selectors.registers_visible_to(cashier).values_list("id", flat=True))
    assert cashier_ids == {register_a.id}
    assert register_b.id not in cashier_ids
    assert register_a.is_visible_to(cashier) is True
    assert register_b.is_visible_to(cashier) is False

    finance_ids = set(selectors.registers_visible_to(finance).values_list("id", flat=True))
    assert {register_a.id, register_b.id} <= finance_ids


def test_add_operation_writes_audit_log():
    """Every money change writes an AuditLog row."""
    actor = UserFactory()
    register = CashRegisterFactory(turnover_limit=0)

    op = services.add_operation(
        register_id=register.id, kind=TxKind.INCOME, amount=Decimal("500"),
        method=PayMethod.CASH, occurred_on=dt.date.today(), actor=actor,
    )

    entry = AuditLog.objects.filter(action="cash.operation.added", object_id=str(op.id)).first()
    assert entry is not None
    assert entry.actor_id == actor.id
    assert entry.after["amount"] == "500.00"


def test_set_turnover_limit_audits_and_rejects_negative():
    """КАС-03: limit change is audited; negative limit is rejected."""
    actor = UserFactory()
    register = CashRegisterFactory(turnover_limit=0)

    services.set_turnover_limit(register_id=register.id, limit=Decimal("5000"), actor=actor)
    register.refresh_from_db()
    assert register.turnover_limit == Decimal("5000.00")
    assert AuditLog.objects.filter(
        action="cash.limit.changed", object_id=str(register.id)
    ).exists()

    with pytest.raises(DomainError) as exc:
        services.set_turnover_limit(register_id=register.id, limit=Decimal("-1"), actor=actor)
    assert exc.value.code == "limit_negative"


def test_void_operation_excludes_from_balance():
    """Voided (soft-deleted) operations are excluded from balance/turnover."""
    actor = UserFactory()
    register = CashRegisterFactory(turnover_limit=0)
    op = CashOperationFactory(register=register, kind=TxKind.INCOME, amount=Decimal("400"))

    assert selectors.register_balance(register.id) == Decimal("400.00")
    services.void_operation(operation_id=op.id, actor=actor, reason="ошибка")
    assert selectors.register_balance(register.id) == Decimal("0.00")
