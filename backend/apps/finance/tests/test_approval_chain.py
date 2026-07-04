"""
Two-stage approval chain: менеджер → бухгалтер → владелец (API-level).

Locks the fix for the owner-step bypass found in the TZ audit: a large operation
(amount above the business expense limit) that sits in ``awaiting_owner`` must NOT
be confirmable by a plain accountant — only by an owner (or superuser).
"""
import datetime as dt
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import RoleCode
from apps.core.enums import PayMethod, TxKind, TxStatus
from apps.core.tests.factories import (
    BusinessFactory,
    ExpenseCategoryFactory,
    RoleFactory,
    UserFactory,
)
from apps.finance.models import Transaction


def _large_awaiting_owner_tx():
    # expense_limit=10000 → an expense of 50000 is «крупная» (requires_owner).
    biz = BusinessFactory(expense_limit=Decimal("10000"))
    return Transaction.objects.create(
        business=biz,
        kind=TxKind.EXPENSE,
        category=ExpenseCategoryFactory(),
        amount=Decimal("50000"),
        method=PayMethod.CASH,
        status=TxStatus.AWAITING_OWNER,
        occurred_on=dt.date.today(),
    )


@pytest.mark.django_db
def test_accountant_cannot_confirm_large_operation():
    tx = _large_awaiting_owner_tx()
    accountant = UserFactory(role=RoleFactory(code=RoleCode.ACCOUNTANT))

    client = APIClient()
    client.force_authenticate(accountant)
    resp = client.post(f"/api/v1/transactions/{tx.id}/confirm", {}, format="json")

    assert resp.status_code == 403
    tx.refresh_from_db()
    assert tx.status == TxStatus.AWAITING_OWNER  # unchanged — owner step not bypassed


@pytest.mark.django_db
def test_owner_confirms_large_operation():
    tx = _large_awaiting_owner_tx()
    owner = UserFactory(role=RoleFactory(code=RoleCode.OWNER))

    client = APIClient()
    client.force_authenticate(owner)
    resp = client.post(f"/api/v1/transactions/{tx.id}/confirm", {}, format="json")

    assert resp.status_code == 200
    tx.refresh_from_db()
    assert tx.status == TxStatus.CONFIRMED
    assert tx.confirmed_by_id == owner.id
