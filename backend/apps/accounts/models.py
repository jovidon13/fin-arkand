"""
Users & roles (accounts). RBAC per CONTRACT.md §1.8.

Roles: owner, chief_accountant, accountant, cashier, admin.
Owners have a responsibility *zone* (a Business); cashiers are scoped to their
own cash register(s) — the scope is enforced in cash selectors/permissions.
"""
from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class RoleCode(models.TextChoices):
    OWNER = "owner", _("Владелец")
    CHIEF_ACCOUNTANT = "chief_accountant", _("Главный бухгалтер")
    ACCOUNTANT = "accountant", _("Бухгалтер")
    CASHIER = "cashier", _("Кассир")
    ADMIN = "admin", _("Администратор системы")


#: Roles that make up the finance department back office.
FINANCE_STAFF_ROLES = frozenset(
    {RoleCode.CHIEF_ACCOUNTANT, RoleCode.ACCOUNTANT, RoleCode.OWNER, RoleCode.ADMIN}
)
#: Roles allowed to write finance operations (confirm income, run payroll, …).
FINANCE_MANAGER_ROLES = frozenset(
    {RoleCode.CHIEF_ACCOUNTANT, RoleCode.ACCOUNTANT, RoleCode.ADMIN}
)


class Role(models.Model):
    code = models.CharField(max_length=32, choices=RoleCode.choices, unique=True)
    name = models.CharField(max_length=120)

    class Meta:
        verbose_name = _("Роль")
        verbose_name_plural = _("Роли")

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    """Custom user. Kept username-based (separate login per system, ХОЛ-02)."""

    role = models.ForeignKey(
        Role, null=True, blank=True, on_delete=models.SET_NULL, related_name="users"
    )
    # Owner zone / home business. For owners this is their responsibility zone
    # (Сохиб→финансы, Ифтихор→заводы, Довуд→проектная).
    business = models.ForeignKey(
        "core.Business", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="users",
    )
    phone = models.CharField(max_length=32, blank=True)

    class Meta:
        verbose_name = _("Пользователь")
        verbose_name_plural = _("Пользователи")

    # -- role helpers -------------------------------------------------------- #
    @property
    def role_code(self) -> str | None:
        return self.role.code if self.role_id else None

    @property
    def is_owner(self) -> bool:
        return self.role_code == RoleCode.OWNER

    @property
    def is_admin_role(self) -> bool:
        return self.role_code == RoleCode.ADMIN

    @property
    def is_chief_accountant(self) -> bool:
        return self.role_code == RoleCode.CHIEF_ACCOUNTANT

    @property
    def is_cashier(self) -> bool:
        return self.role_code == RoleCode.CASHIER

    @property
    def is_finance_staff(self) -> bool:
        """Back-office finance user (sees all money) or superuser."""
        return self.is_superuser or self.role_code in FINANCE_STAFF_ROLES

    @property
    def can_manage_finance(self) -> bool:
        """Allowed to write finance operations."""
        return self.is_superuser or self.role_code in FINANCE_MANAGER_ROLES

    def __str__(self) -> str:
        full = self.get_full_name()
        return full or self.username
