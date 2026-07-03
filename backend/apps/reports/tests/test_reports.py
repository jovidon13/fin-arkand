from decimal import Decimal

import pytest

from apps.core.enums import TxStatus
from apps.core.tests.factories import BusinessFactory, ExpenseCategoryFactory
from apps.finance.tests.factories import ExpenseFactory, TransactionFactory
from apps.reports import selectors

pytestmark = pytest.mark.django_db


def test_pnl_consolidates_across_businesses():
    """ФНС-10: consolidated income/expense/profit sums every business."""
    a = BusinessFactory()
    b = BusinessFactory()
    cat = ExpenseCategoryFactory()

    TransactionFactory(business=a, kind="income", amount=1000, status=TxStatus.CONFIRMED)
    ExpenseFactory(business=a, amount=400, category=cat, status=TxStatus.CONFIRMED)
    TransactionFactory(business=b, kind="income", amount=2000, status=TxStatus.CONFIRMED)
    ExpenseFactory(business=b, amount=500, category=cat, status=TxStatus.CONFIRMED)

    data = selectors.pnl()
    assert data["consolidated"]["income"] == Decimal("3000.00")
    assert data["consolidated"]["expense"] == Decimal("900.00")
    assert data["consolidated"]["profit"] == Decimal("2100.00")
    assert len(data["by_business"]) == 2


def test_dashboard_shape():
    """Dashboard returns the KPI keys the frontend relies on."""
    data = selectors.dashboard()
    for key in ("income", "expense", "profit", "cash_balance", "open_debts", "payroll_fund"):
        assert key in data
