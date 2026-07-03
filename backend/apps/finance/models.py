"""
Finance ledger — the single source of truth for money movements per business
(ФНС-01…04). Income needs confirmation by a financier; expenses are booked by
article. Money is Decimal; records are soft-deleted, never physically removed.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.enums import PayMethod, TxKind, TxStatus
from apps.core.models import MoneyBaseModel


class Transaction(MoneyBaseModel):
    """A single income or expense record (ФНС-01, ФНС-02, ФНС-03)."""

    business = models.ForeignKey(
        "core.Business", on_delete=models.PROTECT, related_name="transactions"
    )
    kind = models.CharField(max_length=16, choices=TxKind.choices, db_index=True)
    category = models.ForeignKey(
        "core.ExpenseCategory", null=True, blank=True, on_delete=models.PROTECT,
        related_name="transactions",
        help_text=_("Статья — обязательна для расходов (ФНС-02)"),
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)  # money = Decimal
    method = models.CharField(max_length=16, choices=PayMethod.choices)  # cash | transfer
    status = models.CharField(
        max_length=16, choices=TxStatus.choices, default=TxStatus.PENDING, db_index=True
    )

    occurred_on = models.DateField(db_index=True)
    # Cross-cutting object/city dimension (ХОЛ-06).
    site_object = models.ForeignKey(
        "core.SiteObject", null=True, blank=True, on_delete=models.PROTECT,
        related_name="transactions",
    )
    counterparty = models.CharField(max_length=200, blank=True)
    note = models.TextField(blank=True)

    # Barter between own businesses is not revenue (БЕТ-62 / БАР-04).
    is_barter = models.BooleanField(default=False)
    # Source tag, e.g. "external_sales" — developer income from the external
    # apartment-sales system enters the finance loop here (ЗАС-41 / ХОЛ-52).
    source = models.CharField(max_length=50, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
        related_name="created_transactions",
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="confirmed_transactions",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Транзакция")
        verbose_name_plural = _("Транзакции")
        ordering = ["-occurred_on", "-created_at"]
        indexes = [
            models.Index(fields=["business", "kind", "status"]),
            models.Index(fields=["occurred_on", "business"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0), name="finance_tx_amount_positive"
            ),
        ]

    def __str__(self) -> str:
        sign = "+" if self.kind == TxKind.INCOME else "−"
        return f"{sign}{self.amount} {self.business_id} [{self.status}]"

    @property
    def is_confirmed(self) -> bool:
        return self.status == TxStatus.CONFIRMED

    @property
    def signed_amount(self):
        """+amount for income, −amount for expense (for aggregation/display)."""
        return self.amount if self.kind == TxKind.INCOME else -self.amount
