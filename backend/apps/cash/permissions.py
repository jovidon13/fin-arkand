"""Cash permissions — composed from the shared RBAC base (CONTRACT.md §1.8).

Object-level cash isolation (КАС-04) is provided by ``CashRegisterScoped``
together with queryset filtering in ``cash.selectors``.
"""
from apps.accounts.permissions import (
    CanManageFinance,
    CashRegisterScoped,
    IsAdminRole,
    IsFinanceStaff,
    IsOwner,
)

__all__ = [
    "IsFinanceStaff",
    "CanManageFinance",
    "CashRegisterScoped",
    "IsAdminRole",
    "IsOwner",
]
