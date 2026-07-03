"""
Write layer for approvals: all business logic + transactions (ХОЛ-20…24).

Financial invariants enforced:
  * every mutation is atomic (`transaction.atomic`);
  * a vote locks its request row (`select_for_update`) against races;
  * one vote per owner (unique) — a repeat is rejected, never double-counted;
  * every status change is written to the audit log in the same transaction.

An approved request may later be linked to a finance expense transaction; this
module does NOT post to the ledger itself (kept as an explicit follow-up step).
"""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.core.enums import ApprovalStatus, VoteValue
from apps.core.exceptions import DomainError
from apps.core.models import Business
from apps.core.money import money

from . import selectors
from .models import ApprovalRequest, ApprovalVote


def _snapshot(req: ApprovalRequest) -> dict:
    return {
        "status": req.status,
        "amount": str(req.amount),
        "required_votes": req.required_votes,
        "approvals": req.approvals_count,
        "rejections": req.rejections_count,
        "decided_at": req.decided_at.isoformat() if req.decided_at else None,
    }


@transaction.atomic
def create_request(
    *,
    business_id: int,
    amount: Decimal,
    purpose: str,
    actor,
    occurred_on,
    category_id: int | None = None,
    description: str = "",
    required_votes: int | None = None,
) -> ApprovalRequest:
    """Open an approval request for an expense (ХОЛ-20…24).

    Within the business ``expense_limit`` → small expense, auto-approved with no
    owners involved (ХОЛ-24). Above it → large expense, created ``pending`` and
    routed to all owners for agreement (ХОЛ-21/22).
    """
    amount = money(amount)
    if amount <= 0:
        raise DomainError("amount_not_positive", "Сумма должна быть больше нуля")

    business = Business.objects.get(pk=business_id)
    actor_pk = actor if getattr(actor, "pk", None) else None

    if not selectors.requires_approval(business, amount):
        # ХОЛ-24: small expense — approved automatically, no owners needed.
        req = ApprovalRequest.objects.create(
            business=business,
            amount=amount,
            purpose=purpose,
            description=description,
            category_id=category_id,
            status=ApprovalStatus.APPROVED,
            required_votes=0,
            requested_by=actor_pk,
            decided_at=timezone.now(),
            occurred_on=occurred_on,
        )
        AuditLog.record(
            actor, "approval.auto_approved", req, after=_snapshot(req),
            meta={"reason": "within_expense_limit",
                  "expense_limit": str(business.expense_limit)},
        )
        return req

    # ХОЛ-21/22: large expense — pending owners' agreement.
    needed = required_votes if required_votes is not None else settings.OWNER_APPROVALS_REQUIRED
    req = ApprovalRequest.objects.create(
        business=business,
        amount=amount,
        purpose=purpose,
        description=description,
        category_id=category_id,
        status=ApprovalStatus.PENDING,
        required_votes=needed,
        requested_by=actor_pk,
        occurred_on=occurred_on,
    )
    AuditLog.record(
        actor, "approval.requested", req, after=_snapshot(req),
        meta={"expense_limit": str(business.expense_limit)},
    )
    return req


@transaction.atomic
def cast_vote(*, request_id: int, owner, value: str, comment: str = "") -> ApprovalRequest:
    """Record an owner's vote and re-evaluate the request (ХОЛ-22/23).

    A single "нет" blocks the expense immediately (ХОЛ-23); otherwise the request
    is approved once the required number of "добро" votes is reached (ХОЛ-22).
    """
    req = ApprovalRequest.objects.select_for_update().get(pk=request_id)

    if req.status != ApprovalStatus.PENDING:
        raise DomainError(
            "approval_not_pending",
            "Запрос уже решён — голосование закрыто",
        )

    if not (getattr(owner, "is_superuser", False) or getattr(owner, "is_owner", False)):
        raise DomainError(
            "not_owner",
            "Голосовать за согласование могут только владельцы (ХОЛ-22)",
            status_code=403,
        )

    before = _snapshot(req)

    # Upsert-once: one vote per owner (unique constraint). A repeat is a rule
    # violation, not a silent overwrite — the vote must not be double-counted.
    if req.votes.filter(owner=owner).exists():
        raise DomainError("already_voted", "Владелец уже проголосовал по этому запросу")
    try:
        with transaction.atomic():
            ApprovalVote.objects.create(
                request=req, owner=owner, value=value, comment=comment
            )
    except IntegrityError:
        raise DomainError(
            "already_voted", "Владелец уже проголосовал по этому запросу"
        ) from None

    # Recompute from the (locked) request's votes.
    has_reject = req.votes.filter(value=VoteValue.REJECT).exists()
    approvals = req.votes.filter(value=VoteValue.APPROVE).count()

    if has_reject:
        # ХОЛ-23: one "no" blocks the whole expense, no waiting for the rest.
        req.status = ApprovalStatus.REJECTED
        req.decided_at = timezone.now()
        req.save(update_fields=["status", "decided_at", "updated_at"])
    elif approvals >= req.required_votes:
        # ХОЛ-22: all required owners agreed → approved.
        req.status = ApprovalStatus.APPROVED
        req.decided_at = timezone.now()
        req.save(update_fields=["status", "decided_at", "updated_at"])

    AuditLog.record(
        owner, "approval.voted", req, before=before, after=_snapshot(req),
        meta={"value": value},
    )
    return req
