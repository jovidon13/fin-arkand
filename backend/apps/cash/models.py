"""
Cash registers with turnover limits and isolation (КАС-01…04).

A ``CashRegister`` belongs to a holding business and is operated by responsible
cashiers. Each ``CashOperation`` is an income (приход) or expense (расход) posted
against a register; money is Decimal and operations are soft-deleted, never
physically removed (financial invariants). Turnover limits (КАС-03) and the
"своё/чужое" isolation (КАС-04) are enforced in selectors/services/permissions.
"""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.enums import PayMethod, TxKind
from apps.core.models import MoneyBaseModel, TimeStampedModel


class CashRegister(TimeStampedModel):
    """A cash register of a business (КАС-01), operated by responsible cashiers.

    ``turnover_limit`` caps the оборот per calendar month (КАС-03); ``0`` means
    no limit. Visibility follows the isolation rule (КАС-04).
    """

    business = models.ForeignKey(
        "core.Business", on_delete=models.PROTECT, related_name="cash_registers"
    )
    name = models.CharField(max_length=200)
    code = models.SlugField(unique=True, help_text=_("Стабильный машинный код кассы"))
    # КАС-03: 0 = без лимита оборота.
    turnover_limit = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        help_text=_("Лимит оборота за месяц; 0 = без лимита (КАС-03)"),
    )
    # Кассиры, ответственные за кассу (КАС-04).
    responsible = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="cash_registers",
        help_text=_("Кассиры, ответственные за кассу"),
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Касса")
        verbose_name_plural = _("Кассы")
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def is_visible_to(self, user) -> bool:
        """Isolation check (КАС-04): finance staff / superuser see every register;
        a cashier sees only registers they are responsible for."""
        if user is None or not getattr(user, "is_authenticated", False):
            return False
        if user.is_superuser or user.is_finance_staff:
            return True
        return self.responsible.filter(pk=user.pk).exists()


class CashOperation(MoneyBaseModel):
    """A single income/expense posted against a register (КАС-02).

    ``kind`` = income (приход) / expense (расход); ``method`` is the pay method
    (КАС-02, наличные/перевод). May optionally mirror a finance ledger row.
    """

    register = models.ForeignKey(
        CashRegister, on_delete=models.PROTECT, related_name="operations"
    )
    kind = models.CharField(max_length=16, choices=TxKind.choices, db_index=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)  # money = Decimal
    method = models.CharField(max_length=16, choices=PayMethod.choices)  # cash | transfer

    occurred_on = models.DateField(db_index=True)
    counterparty = models.CharField(max_length=200, blank=True)
    note = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
        related_name="created_cash_operations",
    )
    # Optional link to the finance ledger (a cash operation may mirror a Transaction).
    finance_transaction = models.OneToOneField(
        "finance.Transaction", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="cash_operation",
    )

    class Meta:
        verbose_name = _("Кассовая операция")
        verbose_name_plural = _("Кассовые операции")
        ordering = ["-occurred_on", "-created_at"]
        indexes = [
            models.Index(fields=["register", "kind"]),
            models.Index(fields=["occurred_on", "register"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0), name="cash_operation_amount_positive"
            ),
        ]

    def __str__(self) -> str:
        sign = "+" if self.kind == TxKind.INCOME else "−"
        return f"{sign}{self.amount} @ {self.register_id} [{self.occurred_on}]"

    @property
    def signed_amount(self) -> Decimal:
        """+amount for income, −amount for expense (for balance/display)."""
        return self.amount if self.kind == TxKind.INCOME else -self.amount
