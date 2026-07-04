"""
Inter-business settlements: transfers, auto-debts, closings and barter
(БАР-01…04 / ХОЛ-30…33).

When one holding business hands value to another, an approved ``Transfer``
auto-creates a ``Debt`` (debtor=receiver, creditor=sender). Debts are closed by
``Settlement`` rows (repayment / netting / barter). Money is Decimal; records
are soft-deleted, never physically removed.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.enums import (
    DebtStatus,
    ExternalDebtDirection,
    SettlementKind,
    TransferStatus,
)
from apps.core.models import MoneyBaseModel


class Transfer(MoneyBaseModel):
    """A value hand-off between two holding businesses (БАР-01 / ХОЛ-30).

    Created ``pending``; approval by a financier books the auto-debt. When
    ``is_barter`` the transfer is a barter exchange (БАР-04 / ХОЛ-33) — still
    under accountant control and still creating a debt on approval.
    """

    from_business = models.ForeignKey(
        "core.Business", on_delete=models.PROTECT, related_name="transfers_out"
    )
    to_business = models.ForeignKey(
        "core.Business", on_delete=models.PROTECT, related_name="transfers_in"
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)  # money = Decimal
    description = models.TextField(blank=True)
    occurred_on = models.DateField(db_index=True)
    is_barter = models.BooleanField(default=False)  # БАР-04

    status = models.CharField(
        max_length=16, choices=TransferStatus.choices,
        default=TransferStatus.PENDING, db_index=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
        related_name="created_transfers",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Передача")
        verbose_name_plural = _("Передачи")
        ordering = ["-occurred_on", "-created_at"]
        indexes = [
            models.Index(fields=["from_business", "to_business", "status"]),
            models.Index(fields=["occurred_on", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0), name="settlements_transfer_amount_positive"
            ),
            models.CheckConstraint(
                check=~models.Q(from_business=models.F("to_business")),
                name="settlements_transfer_distinct_businesses",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.from_business_id}→{self.to_business_id} {self.amount} [{self.status}]"

    @property
    def is_approved(self) -> bool:
        return self.status == TransferStatus.APPROVED


class Debt(MoneyBaseModel):
    """An outstanding obligation of one business to another (БАР-02 / ХОЛ-31).

    ``amount`` is the original obligation, ``outstanding`` the remaining balance
    that settlements reduce toward zero.
    """

    debtor = models.ForeignKey(
        "core.Business", on_delete=models.PROTECT, related_name="debts_as_debtor"
    )
    creditor = models.ForeignKey(
        "core.Business", on_delete=models.PROTECT, related_name="debts_as_creditor"
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)  # original
    outstanding = models.DecimalField(max_digits=14, decimal_places=2)

    status = models.CharField(
        max_length=20, choices=DebtStatus.choices,
        default=DebtStatus.OPEN, db_index=True,
    )
    is_barter = models.BooleanField(default=False)
    source_transfer = models.OneToOneField(
        Transfer, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="debt",
    )
    occurred_on = models.DateField(db_index=True)

    class Meta:
        verbose_name = _("Долг")
        verbose_name_plural = _("Долги")
        ordering = ["-occurred_on", "-created_at"]
        indexes = [
            models.Index(fields=["debtor", "creditor", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0), name="settlements_debt_amount_positive"
            ),
            models.CheckConstraint(
                check=models.Q(outstanding__gte=0),
                name="settlements_debt_outstanding_nonneg",
            ),
            models.CheckConstraint(
                check=~models.Q(debtor=models.F("creditor")),
                name="settlements_debt_distinct_businesses",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.debtor_id}⇒{self.creditor_id} "
            f"{self.outstanding}/{self.amount} [{self.status}]"
        )

    @property
    def is_settled(self) -> bool:
        return self.status == DebtStatus.SETTLED


class ExternalDebt(MoneyBaseModel):
    """Дебиторская / кредиторская задолженность с ВНЕШНИМ контрагентом.

    Unlike :class:`Debt` (долг между своими бизнесами), this tracks money owed by
    or to outside parties — «кто должен компании» и «кому должна компания».
    ``direction`` splits the two sides; ``outstanding`` is the remaining balance
    a partial payment reduces toward zero. Money is Decimal; records are
    soft-deleted, never physically removed.
    """

    direction = models.CharField(
        max_length=16, choices=ExternalDebtDirection.choices, db_index=True
    )
    counterparty = models.CharField(max_length=200, help_text=_("Внешний контрагент"))
    # Which holding business the debt belongs to (optional — «на весь холдинг»).
    business = models.ForeignKey(
        "core.Business", null=True, blank=True, on_delete=models.PROTECT,
        related_name="external_debts",
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)  # original
    outstanding = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=DebtStatus.choices,
        default=DebtStatus.OPEN, db_index=True,
    )
    occurred_on = models.DateField(db_index=True)
    due_on = models.DateField(null=True, blank=True)
    note = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
        related_name="created_external_debts",
    )

    class Meta:
        verbose_name = _("Внешняя задолженность")
        verbose_name_plural = _("Внешние задолженности")
        ordering = ["-occurred_on", "-created_at"]
        indexes = [
            models.Index(fields=["direction", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0), name="settlements_extdebt_amount_positive"
            ),
            models.CheckConstraint(
                check=models.Q(outstanding__gte=0),
                name="settlements_extdebt_outstanding_nonneg",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_direction_display()}: {self.counterparty} {self.outstanding}"

    @property
    def is_settled(self) -> bool:
        return self.status == DebtStatus.SETTLED


class Settlement(MoneyBaseModel):
    """A closing event against a debt (БАР-03 / ХОЛ-32).

    ``kind`` is repayment / netting / barter. For netting a ``counter_debt`` is
    reduced symmetrically (взаимозачёт).
    """

    debt = models.ForeignKey(
        Debt, on_delete=models.PROTECT, related_name="settlements"
    )
    kind = models.CharField(max_length=16, choices=SettlementKind.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    counter_debt = models.ForeignKey(
        Debt, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="counter_settlements",  # for netting
    )
    note = models.TextField(blank=True)
    occurred_on = models.DateField(db_index=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
        related_name="created_settlements",
    )

    class Meta:
        verbose_name = _("Закрытие долга")
        verbose_name_plural = _("Закрытия долгов")
        ordering = ["-occurred_on", "-created_at"]
        indexes = [
            models.Index(fields=["debt", "kind"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0),
                name="settlements_settlement_amount_positive",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.kind} {self.amount} → debt {self.debt_id}"
