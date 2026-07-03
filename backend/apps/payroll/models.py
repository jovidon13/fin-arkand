"""
Payroll — salaries with flexible bonus schemes (ЗРП-01…05).

Salaries are calculated in-system per period and paid out from the head office
(ЗРП-01). A :class:`PayrollScheme` carries a base fixed part plus a list of bonus
rules interpreted by the pure engine in ``services.compute_bonus`` — e.g. a plant
salesperson's "fix + 10% продаж" (ЗРП-04) or a developer's "500 сом/квартира, при
>10 кв/мес → 1000 сом/квартира" (ЗРП-05).

Money is always Decimal; money-bearing rows (Employee, PayrollItem) inherit
``MoneyBaseModel`` (soft-delete + timestamps) and are never physically deleted.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.enums import EmployeeSalaryType, PayrollStatus
from apps.core.models import MoneyBaseModel, TimeStampedModel


class PayrollScheme(TimeStampedModel):
    """Flexible salary scheme: base fixed part + JSON list of bonus rules (ЗРП-03).

    ``rules`` is a list of rule dicts interpreted by ``services.compute_bonus``.
    Supported types: ``percent_of_sales`` (ЗРП-04), ``per_unit`` (ЗРП-05),
    ``fixed_bonus``.
    """

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    base_fixed = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        help_text=_("Базовый фикс схемы"),
    )
    rules = models.JSONField(default=list, help_text=_("Список правил бонуса"))
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Схема ЗП")
        verbose_name_plural = _("Схемы ЗП")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Employee(MoneyBaseModel):
    """A holding employee with an оклад and an optional bonus scheme (ЗРП-02, ЗРП-03).

    ``salary_type`` distinguishes объектный vs административный staff (ЗРП-02);
    ``is_salesperson`` marks a продажник on fix + bonus (ЗРП-03).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="employee",
    )
    full_name = models.CharField(max_length=200)
    business = models.ForeignKey(
        "core.Business", on_delete=models.PROTECT, related_name="employees"
    )
    position = models.CharField(max_length=200, blank=True)
    salary_type = models.CharField(
        max_length=16, choices=EmployeeSalaryType.choices,
        default=EmployeeSalaryType.OBJECT,
    )
    base_salary = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, help_text=_("Оклад")
    )
    is_salesperson = models.BooleanField(default=False, help_text=_("Продажник (ЗРП-03)"))
    scheme = models.ForeignKey(
        PayrollScheme, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="employees",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Сотрудник")
        verbose_name_plural = _("Сотрудники")
        ordering = ["full_name"]
        indexes = [
            models.Index(fields=["business", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.full_name


class PayrollRun(TimeStampedModel):
    """A monthly payroll calculation for the whole holding (ЗРП-01).

    One run per (year, month). Lifecycle: draft → calculated → approved → paid.
    """

    year = models.IntegerField()
    month = models.IntegerField()
    status = models.CharField(
        max_length=16, choices=PayrollStatus.choices, default=PayrollStatus.DRAFT,
        db_index=True,
    )
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
        related_name="created_payroll_runs",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Расчёт ЗП")
        verbose_name_plural = _("Расчёты ЗП")
        ordering = ["-year", "-month"]
        constraints = [
            models.UniqueConstraint(fields=["year", "month"], name="uq_payroll_run_period"),
        ]

    def __str__(self) -> str:
        return f"ЗП {self.year}-{self.month:02d} [{self.status}]"


class PayrollItem(MoneyBaseModel):
    """One employee's line inside a run: base + bonus = total (ЗРП-01).

    ``details`` holds the bonus breakdown and ``metrics`` the input metrics
    (sales, apartments) used to compute it.
    """

    run = models.ForeignKey(
        PayrollRun, on_delete=models.CASCADE, related_name="items"
    )
    employee = models.ForeignKey(
        Employee, on_delete=models.PROTECT, related_name="payroll_items"
    )
    base_amount = models.DecimalField(max_digits=14, decimal_places=2)
    bonus_amount = models.DecimalField(max_digits=14, decimal_places=2)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    details = models.JSONField(default=dict, help_text=_("Разбивка бонуса"))
    metrics = models.JSONField(default=dict, help_text=_("Входные метрики расчёта"))

    class Meta:
        verbose_name = _("Строка ЗП")
        verbose_name_plural = _("Строки ЗП")
        ordering = ["run", "employee__full_name"]
        indexes = [
            models.Index(fields=["run", "employee"]),
        ]

    def __str__(self) -> str:
        return f"{self.employee_id}: {self.total_amount}"
