import datetime as dt
from decimal import Decimal

import pytest

from apps.core.enums import PayMethod, TxKind, TxStatus
from apps.core.exceptions import DomainError
from apps.core.tests.factories import (
    BusinessFactory,
    ExpenseCategoryFactory,
    UserFactory,
)
from apps.finance import selectors, services
from apps.finance.tests.factories import ExpenseFactory, TransactionFactory

pytestmark = pytest.mark.django_db


def test_confirm_is_idempotent():
    """ФНС-01: re-confirming a transaction does not create a second effect."""
    actor = UserFactory()
    tx = TransactionFactory(status=TxStatus.PENDING)

    first = services.confirm_transaction(tx_id=tx.id, actor=actor)
    assert first.status == TxStatus.CONFIRMED
    assert first.confirmed_at is not None

    confirmed_at = first.confirmed_at
    second = services.confirm_transaction(tx_id=tx.id, actor=actor)
    # Idempotent — same record, timestamp unchanged, no new confirmation.
    assert second.status == TxStatus.CONFIRMED
    assert second.confirmed_at == confirmed_at


def test_expense_requires_category():
    """ФНС-02: an expense without an article is rejected."""
    actor = UserFactory()
    biz = BusinessFactory()
    with pytest.raises(DomainError) as exc:
        services.create_transaction(
            business_id=biz.id,
            kind=TxKind.EXPENSE,
            amount=Decimal("500"),
            method=PayMethod.CASH,
            occurred_on=dt.date.today(),
            actor=actor,
        )
    assert exc.value.code == "category_required"


def test_profit_by_business_excludes_barter_and_unconfirmed():
    """ФНС-04: profit = confirmed income − confirmed expense; barter excluded."""
    biz = BusinessFactory()
    cat = ExpenseCategoryFactory()

    # confirmed income 1000
    TransactionFactory(business=biz, kind=TxKind.INCOME, amount=1000,
                       status=TxStatus.CONFIRMED)
    # confirmed expense 300
    ExpenseFactory(business=biz, amount=300, category=cat, status=TxStatus.CONFIRMED)
    # pending income should NOT count
    TransactionFactory(business=biz, kind=TxKind.INCOME, amount=9999,
                       status=TxStatus.PENDING)
    # barter income should NOT count as revenue
    TransactionFactory(business=biz, kind=TxKind.INCOME, amount=5000,
                       status=TxStatus.CONFIRMED, is_barter=True)

    totals = selectors.business_totals(business_id=biz.id)
    assert totals["income"] == Decimal("1000.00")
    assert totals["expense"] == Decimal("300.00")
    assert totals["profit"] == Decimal("700.00")

    rows = selectors.profit_by_business()
    row = next(r for r in rows if r["business_id"] == biz.id)
    assert row["profit"] == Decimal("700.00")


def test_amount_must_be_positive():
    actor = UserFactory()
    biz = BusinessFactory()
    with pytest.raises(DomainError) as exc:
        services.create_transaction(
            business_id=biz.id,
            kind=TxKind.INCOME,
            amount=Decimal("0"),
            method=PayMethod.CASH,
            occurred_on=dt.date.today(),
            actor=actor,
        )
    assert exc.value.code == "amount_not_positive"
