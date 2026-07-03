"""Payroll permissions — composed from the shared RBAC base (CONTRACT.md §1.8)."""
from apps.accounts.permissions import CanManageFinance, IsFinanceStaff

__all__ = ["IsFinanceStaff", "CanManageFinance"]
