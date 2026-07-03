import datetime as dt
from decimal import Decimal

import pytest

from apps.core.enums import DebtStatus, SettlementKind, TransferStatus
from apps.core.exceptions import DomainError
from apps.core.tests.factories import BusinessFactory, UserFactory
from apps.settlements import selectors, services
from apps.settlements.models import Debt
from apps.settlements.tests.factories import DebtFactory, TransferFactory

pytestmark = pytest.mark.django_db


def test_approve_transfer_creates_debt():
    """БАР-01 / ХОЛ-30: approval books a debt debtor=to, creditor=from."""
    actor = UserFactory()
    sender = BusinessFactory()
    receiver = BusinessFactory()
    transfer = TransferFactory(
        from_business=sender, to_business=receiver, amount=1500,
        status=TransferStatus.PENDING,
    )

    debt = services.approve_transfer(transfer_id=transfer.id, actor=actor)

    transfer.refresh_from_db()
    assert transfer.status == TransferStatus.APPROVED
    assert transfer.approved_at is not None
    assert debt.debtor_id == receiver.id
    assert debt.creditor_id == sender.id
    assert debt.amount == Decimal("1500.00")
    assert debt.outstanding == Decimal("1500.00")
    assert debt.status == DebtStatus.OPEN
    assert debt.source_transfer_id == transfer.id


def test_approve_transfer_is_idempotent():
    """БАР-01: a second approval returns the same debt, no duplicate created."""
    actor = UserFactory()
    transfer = TransferFactory(status=TransferStatus.PENDING)

    first = services.approve_transfer(transfer_id=transfer.id, actor=actor)
    second = services.approve_transfer(transfer_id=transfer.id, actor=actor)

    assert first.id == second.id
    assert Debt.objects.filter(source_transfer=transfer).count() == 1


def test_reject_transfer_blocks_approval():
    """A rejected transfer cannot then be approved (БАР-01)."""
    actor = UserFactory()
    transfer = TransferFactory(status=TransferStatus.PENDING)
    services.reject_transfer(transfer_id=transfer.id, actor=actor)

    with pytest.raises(DomainError) as exc:
        services.approve_transfer(transfer_id=transfer.id, actor=actor)
    assert exc.value.code == "transfer_rejected"


def test_create_transfer_same_business_rejected():
    actor = UserFactory()
    biz = BusinessFactory()
    with pytest.raises(DomainError) as exc:
        services.create_transfer(
            from_business_id=biz.id, to_business_id=biz.id,
            amount=Decimal("100"), occurred_on=dt.date.today(), actor=actor,
        )
    assert exc.value.code == "same_business"


def test_settle_debt_repayment_reduces_outstanding_and_settles():
    """БАР-03: repayment reduces outstanding and flips to settled when fully paid."""
    actor = UserFactory()
    debt = DebtFactory(amount=1000, outstanding=1000)

    # Partial repayment.
    services.settle_debt(
        debt_id=debt.id, kind=SettlementKind.REPAYMENT, amount=Decimal("400"),
        actor=actor, occurred_on=dt.date.today(),
    )
    debt.refresh_from_db()
    assert debt.outstanding == Decimal("600.00")
    assert debt.status == DebtStatus.PARTIALLY_SETTLED

    # Final repayment closes the debt.
    services.settle_debt(
        debt_id=debt.id, kind=SettlementKind.REPAYMENT, amount=Decimal("600"),
        actor=actor, occurred_on=dt.date.today(),
    )
    debt.refresh_from_db()
    assert debt.outstanding == Decimal("0.00")
    assert debt.status == DebtStatus.SETTLED
    assert debt.is_settled


def test_netting_reduces_both_debts_symmetrically():
    """БАР-03: взаимозачёт reduces the debt and its counter debt equally."""
    actor = UserFactory()
    a = BusinessFactory()
    b = BusinessFactory()
    # A owes B 1000; B owes A 800 → net 300 net after full netting of 800.
    debt = DebtFactory(debtor=a, creditor=b, amount=1000, outstanding=1000)
    counter = DebtFactory(debtor=b, creditor=a, amount=800, outstanding=800)

    services.settle_debt(
        debt_id=debt.id, kind=SettlementKind.NETTING, amount=Decimal("800"),
        actor=actor, occurred_on=dt.date.today(), counter_debt_id=counter.id,
    )

    debt.refresh_from_db()
    counter.refresh_from_db()
    assert debt.outstanding == Decimal("200.00")
    assert debt.status == DebtStatus.PARTIALLY_SETTLED
    assert counter.outstanding == Decimal("0.00")
    assert counter.status == DebtStatus.SETTLED

    assert selectors.net_between(a.id, b.id) == Decimal("200.00")


def test_netting_requires_counter_debt():
    """БАР-03: netting without a counter debt is rejected (not a silent repayment)."""
    actor = UserFactory()
    debt = DebtFactory(amount=1000, outstanding=1000)
    with pytest.raises(DomainError) as exc:
        services.settle_debt(
            debt_id=debt.id, kind=SettlementKind.NETTING, amount=Decimal("100"),
            actor=actor, occurred_on=dt.date.today(),
        )
    assert exc.value.code == "counter_debt_required"


def test_netting_rejects_non_reciprocal_counter():
    """БАР-03: взаимозачёт only against the reciprocal obligation of the same two
    businesses — an unrelated debt cannot be discharged."""
    actor = UserFactory()
    a = BusinessFactory()
    b = BusinessFactory()
    c = BusinessFactory()
    debt = DebtFactory(debtor=a, creditor=b, amount=1000, outstanding=1000)
    # c owes a — NOT the reciprocal of a→b.
    counter = DebtFactory(debtor=c, creditor=a, amount=1000, outstanding=1000)
    with pytest.raises(DomainError) as exc:
        services.settle_debt(
            debt_id=debt.id, kind=SettlementKind.NETTING, amount=Decimal("100"),
            actor=actor, occurred_on=dt.date.today(), counter_debt_id=counter.id,
        )
    assert exc.value.code == "counter_debt_not_reciprocal"


def test_netting_rejects_self():
    """БАР-03: a debt cannot be netted against itself."""
    actor = UserFactory()
    debt = DebtFactory(amount=1000, outstanding=1000)
    with pytest.raises(DomainError) as exc:
        services.settle_debt(
            debt_id=debt.id, kind=SettlementKind.NETTING, amount=Decimal("100"),
            actor=actor, occurred_on=dt.date.today(), counter_debt_id=debt.id,
        )
    assert exc.value.code == "counter_debt_self"


def test_settle_debt_is_idempotent():
    """A repeated settle with the same Idempotency-Key does not double-close."""
    actor = UserFactory()
    debt = DebtFactory(amount=1000, outstanding=1000)
    first = services.settle_debt(
        debt_id=debt.id, kind=SettlementKind.REPAYMENT, amount=Decimal("400"),
        actor=actor, occurred_on=dt.date.today(), idempotency_key="settle-1",
    )
    second = services.settle_debt(
        debt_id=debt.id, kind=SettlementKind.REPAYMENT, amount=Decimal("400"),
        actor=actor, occurred_on=dt.date.today(), idempotency_key="settle-1",
    )
    assert first.id == second.id
    debt.refresh_from_db()
    assert debt.outstanding == Decimal("600.00")  # reduced once, not twice


def test_netting_insufficient_counter_debt():
    actor = UserFactory()
    a = BusinessFactory()
    b = BusinessFactory()
    debt = DebtFactory(debtor=a, creditor=b, amount=1000, outstanding=1000)
    counter = DebtFactory(debtor=b, creditor=a, amount=300, outstanding=300)

    with pytest.raises(DomainError) as exc:
        services.settle_debt(
            debt_id=debt.id, kind=SettlementKind.NETTING, amount=Decimal("500"),
            actor=actor, occurred_on=dt.date.today(), counter_debt_id=counter.id,
        )
    assert exc.value.code == "counter_debt_insufficient"


def test_settle_exceeds_outstanding_raises():
    """БАР-03: closing more than the outstanding balance is rejected."""
    actor = UserFactory()
    debt = DebtFactory(amount=500, outstanding=500)
    with pytest.raises(DomainError) as exc:
        services.settle_debt(
            debt_id=debt.id, kind=SettlementKind.REPAYMENT, amount=Decimal("600"),
            actor=actor, occurred_on=dt.date.today(),
        )
    assert exc.value.code == "settle_exceeds_outstanding"


def test_settle_already_settled_raises():
    actor = UserFactory()
    debt = DebtFactory(amount=500, outstanding=0, status=DebtStatus.SETTLED)
    with pytest.raises(DomainError) as exc:
        services.settle_debt(
            debt_id=debt.id, kind=SettlementKind.REPAYMENT, amount=Decimal("100"),
            actor=actor, occurred_on=dt.date.today(),
        )
    assert exc.value.code == "debt_already_settled"


def test_settle_non_positive_amount_raises():
    actor = UserFactory()
    debt = DebtFactory(amount=500, outstanding=500)
    with pytest.raises(DomainError) as exc:
        services.settle_debt(
            debt_id=debt.id, kind=SettlementKind.REPAYMENT, amount=Decimal("0"),
            actor=actor, occurred_on=dt.date.today(),
        )
    assert exc.value.code == "amount_not_positive"


def test_create_barter_flags_transfer_and_debt():
    """БАР-04: barter wrapper sets is_barter and still books a debt on approval."""
    actor = UserFactory()
    sender = BusinessFactory()
    receiver = BusinessFactory()
    transfer = services.create_barter(
        from_business_id=sender.id, to_business_id=receiver.id,
        amount=Decimal("700"), occurred_on=dt.date.today(), actor=actor,
    )
    assert transfer.is_barter is True

    debt = services.approve_transfer(transfer_id=transfer.id, actor=actor)
    assert debt.is_barter is True


def test_debt_registry_excludes_settled_by_default():
    """БАР-02: registry lists only debts with outstanding > 0 by default."""
    a = BusinessFactory()
    b = BusinessFactory()
    open_debt = DebtFactory(debtor=a, creditor=b, amount=1000, outstanding=400,
                            status=DebtStatus.PARTIALLY_SETTLED)
    DebtFactory(debtor=a, creditor=b, amount=500, outstanding=0,
                status=DebtStatus.SETTLED)

    rows = selectors.debt_registry()
    ids = {r["debt_id"] for r in rows}
    assert open_debt.id in ids
    assert all(r["outstanding"] > Decimal("0") for r in rows)

    rows_all = selectors.debt_registry(include_settled=True)
    assert len(rows_all) >= 2
