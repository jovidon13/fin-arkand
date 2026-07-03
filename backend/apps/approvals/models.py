"""
Large-expense approval by all three holding owners (ХОЛ-20…24).

A per-business ``expense_limit`` sets the "large vs small" threshold (ХОЛ-21).
An expense above it must be agreed by every owner (ХОЛ-22); a single "no" blocks
it (ХОЛ-23); an expense within the limit is auto-approved without owners (ХОЛ-24).

Money is Decimal; requests inherit soft-delete + timestamps (never physically
removed). Structure + record-level invariants only — writes live in services.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.enums import ApprovalStatus, VoteValue
from apps.core.models import MoneyBaseModel, TimeStampedModel


class ApprovalRequest(MoneyBaseModel):
    """A request to agree a large expense/purchase (ХОЛ-20…24)."""

    business = models.ForeignKey(
        "core.Business", on_delete=models.PROTECT, related_name="approval_requests"
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)  # money = Decimal
    purpose = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        "core.ExpenseCategory", null=True, blank=True, on_delete=models.PROTECT,
        related_name="approval_requests",
    )
    status = models.CharField(
        max_length=16, choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING, db_index=True,
    )
    # ХОЛ-22: all three owners must agree (settings.OWNER_APPROVALS_REQUIRED).
    required_votes = models.IntegerField(default=3)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
        related_name="approval_requests",
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    occurred_on = models.DateField(db_index=True)

    class Meta:
        verbose_name = _("Запрос согласования")
        verbose_name_plural = _("Запросы согласования")
        ordering = ["-occurred_on", "-created_at"]
        indexes = [
            models.Index(fields=["business", "status"]),
            models.Index(fields=["status", "occurred_on"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0), name="approvals_amount_positive"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.purpose} {self.amount} [{self.status}]"

    @property
    def approvals_count(self) -> int:
        """Number of 'добро' votes cast on this request (ХОЛ-22)."""
        return sum(1 for v in self.votes.all() if v.value == VoteValue.APPROVE)

    @property
    def rejections_count(self) -> int:
        """Number of 'нет' votes cast on this request (ХОЛ-23)."""
        return sum(1 for v in self.votes.all() if v.value == VoteValue.REJECT)


class ApprovalVote(TimeStampedModel):
    """A single owner's vote on a request — one per owner (ХОЛ-22/23)."""

    request = models.ForeignKey(
        ApprovalRequest, on_delete=models.CASCADE, related_name="votes"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="approval_votes",
    )
    value = models.CharField(max_length=16, choices=VoteValue.choices)
    comment = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Голос согласования")
        verbose_name_plural = _("Голоса согласования")
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["request", "owner"], name="uq_approval_vote_owner"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.owner_id} → {self.value} (#{self.request_id})"
