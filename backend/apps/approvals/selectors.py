"""Read layer for approvals: queries only, no writes (ХОЛ-20…24)."""
from __future__ import annotations

from django.db.models import QuerySet

from apps.core.enums import ApprovalStatus
from apps.core.money import money

from .models import ApprovalRequest


def requests_qs() -> QuerySet[ApprovalRequest]:
    """Base queryset with related business/category/requester and votes."""
    return (
        ApprovalRequest.objects.select_related("business", "category", "requested_by")
        .prefetch_related("votes", "votes__owner")
    )


def pending_requests() -> QuerySet[ApprovalRequest]:
    """Requests still awaiting owners' decision (ХОЛ-22/23)."""
    return requests_qs().filter(status=ApprovalStatus.PENDING)


def pending_for_owner(user) -> QuerySet[ApprovalRequest]:
    """Pending requests this owner has not yet voted on (ХОЛ-22).

    Feeds an owner's "to decide" inbox — one vote per owner, so anything they
    already voted on drops out.
    """
    return pending_requests().exclude(votes__owner=user)


def requires_approval(business, amount) -> bool:
    """True when an expense is "large" and needs owners' agreement (ХОЛ-21/24).

    Large == strictly above the per-business ``expense_limit`` threshold; within
    the limit is a small expense that is auto-approved (ХОЛ-24).
    """
    return money(amount) > money(business.expense_limit)
