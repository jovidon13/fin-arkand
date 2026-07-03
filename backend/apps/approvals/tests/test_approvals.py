import datetime as dt
from decimal import Decimal

import pytest

from apps.approvals import selectors, services
from apps.approvals.tests.factories import OwnerFactory
from apps.core.enums import ApprovalStatus, VoteValue
from apps.core.exceptions import DomainError
from apps.core.tests.factories import BusinessFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_small_expense_auto_approved():
    """ХОЛ-24: an expense within the business limit needs no owners at all."""
    actor = UserFactory()
    biz = BusinessFactory(expense_limit=Decimal("10000"))

    req = services.create_request(
        business_id=biz.id,
        amount=Decimal("5000"),
        purpose="Мелкая закупка",
        actor=actor,
        occurred_on=dt.date.today(),
    )

    assert req.status == ApprovalStatus.APPROVED
    assert req.decided_at is not None
    assert req.required_votes == 0
    assert req.votes.count() == 0
    assert selectors.requires_approval(biz, Decimal("5000")) is False


def test_large_expense_needs_all_three_owners():
    """ХОЛ-22/23: above the limit → pending; approved only after the 3rd owner
    votes 'добро', and NOT one vote earlier."""
    actor = UserFactory()
    biz = BusinessFactory(expense_limit=Decimal("10000"))
    owners = [OwnerFactory(username=f"owner-{i}") for i in range(3)]

    req = services.create_request(
        business_id=biz.id,
        amount=Decimal("50000"),
        purpose="Крупная закупка",
        actor=actor,
        occurred_on=dt.date.today(),
    )
    assert req.status == ApprovalStatus.PENDING
    assert req.required_votes == 3
    assert selectors.requires_approval(biz, Decimal("50000")) is True

    # First two owners approve — still pending (ХОЛ-23 waits for all).
    services.cast_vote(request_id=req.id, owner=owners[0], value=VoteValue.APPROVE)
    r = services.cast_vote(request_id=req.id, owner=owners[1], value=VoteValue.APPROVE)
    assert r.status == ApprovalStatus.PENDING
    assert r.decided_at is None

    # Third owner approves → APPROVED (ХОЛ-22).
    r = services.cast_vote(request_id=req.id, owner=owners[2], value=VoteValue.APPROVE)
    assert r.status == ApprovalStatus.APPROVED
    assert r.decided_at is not None
    assert r.approvals_count == 3


def test_one_rejection_blocks_immediately():
    """ХОЛ-23: a single 'нет' rejects the whole expense at once."""
    actor = UserFactory()
    biz = BusinessFactory(expense_limit=Decimal("10000"))
    owner_a = OwnerFactory(username="owner-a")
    owner_b = OwnerFactory(username="owner-b")

    req = services.create_request(
        business_id=biz.id,
        amount=Decimal("50000"),
        purpose="Крупная закупка",
        actor=actor,
        occurred_on=dt.date.today(),
    )

    services.cast_vote(request_id=req.id, owner=owner_a, value=VoteValue.APPROVE)
    r = services.cast_vote(request_id=req.id, owner=owner_b, value=VoteValue.REJECT)

    assert r.status == ApprovalStatus.REJECTED
    assert r.decided_at is not None
    assert r.rejections_count == 1


def test_owner_cannot_vote_twice():
    """One vote per owner — a repeat is a rule violation (ХОЛ-22)."""
    actor = UserFactory()
    biz = BusinessFactory(expense_limit=Decimal("10000"))
    owner = OwnerFactory(username="owner-x")

    req = services.create_request(
        business_id=biz.id,
        amount=Decimal("50000"),
        purpose="Крупная закупка",
        actor=actor,
        occurred_on=dt.date.today(),
    )

    services.cast_vote(request_id=req.id, owner=owner, value=VoteValue.APPROVE)
    with pytest.raises(DomainError) as exc:
        services.cast_vote(request_id=req.id, owner=owner, value=VoteValue.APPROVE)
    assert exc.value.code == "already_voted"


def test_non_owner_cannot_vote():
    """Only holding owners may vote on an approval (ХОЛ-22)."""
    actor = UserFactory()
    biz = BusinessFactory(expense_limit=Decimal("10000"))
    non_owner = UserFactory(username="just-accountant")

    req = services.create_request(
        business_id=biz.id,
        amount=Decimal("50000"),
        purpose="Крупная закупка",
        actor=actor,
        occurred_on=dt.date.today(),
    )

    with pytest.raises(DomainError) as exc:
        services.cast_vote(request_id=req.id, owner=non_owner, value=VoteValue.APPROVE)
    assert exc.value.code == "not_owner"
    assert exc.value.status_code == 403
