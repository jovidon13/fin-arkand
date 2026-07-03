"""
Base RBAC permission classes reused by every domain app (CONTRACT.md §1.8).

Object-level cash isolation ("касса видит только своё", КАС-04) is implemented
here via :class:`CashRegisterScoped` together with queryset filtering in the
cash selectors — never by hiding data only in the UI.
"""
from __future__ import annotations

from rest_framework.permissions import BasePermission

from .models import RoleCode


class IsAuthenticatedRole(BasePermission):
    """Authenticated user that has *some* role (or is superuser)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.role_id))


class HasRole(BasePermission):
    """Factory: ``HasRole('owner', 'admin')`` → permission class.

    Usage: ``permission_classes = [HasRole(RoleCode.OWNER, RoleCode.ADMIN)]``.
    """

    required_roles: tuple[str, ...] = ()

    def __init__(self, *roles: str) -> None:
        self.required_roles = tuple(roles)

    def __call__(self) -> HasRole:
        # DRF instantiates permission classes; when used as an instance we
        # return self so ``permission_classes = [HasRole(...)]`` works.
        return self

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser:
            return True
        return user.role_code in self.required_roles


class IsFinanceStaff(BasePermission):
    """Finance back office or owners/admin — may read all money data."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.is_finance_staff)


class CanManageFinance(BasePermission):
    """May write finance operations (confirm income, run payroll, close debts)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.can_manage_finance)


class IsOwner(BasePermission):
    """Holding owner — approves large expenses, changes limits/thresholds."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.is_owner))


class IsAdminRole(BasePermission):
    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.role_code == RoleCode.ADMIN)
        )


class CashRegisterScoped(BasePermission):
    """Object-level cash isolation (КАС-04).

    Finance staff & owners see every cash register. A cashier may act only on a
    register they are responsible for. The model is expected to expose
    ``is_visible_to(user)`` (implemented on ``cash.CashRegister`` and objects
    that carry a ``register`` FK).
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.role_id))

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        if user.is_superuser or user.is_finance_staff:
            return True
        register = getattr(obj, "register", obj)
        checker = getattr(register, "is_visible_to", None)
        return bool(checker and checker(user))
