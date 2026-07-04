"""
Consolidated read layer (ФНС-10…13). Reports own no tables — they aggregate the
domain selectors of finance / cash / settlements / payroll into one picture for
the finance department and owners.
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

from apps.cash import selectors as cash_selectors
from apps.core.money import ZERO
from apps.finance import selectors as finance_selectors
from apps.payroll import selectors as payroll_selectors
from apps.settlements import selectors as settlements_selectors


def pnl(*, date_from: dt.date | None = None, date_to: dt.date | None = None) -> dict:
    """ФНС-10 / ФНС-04: income, expense, profit per business + consolidated."""
    rows = finance_selectors.profit_by_business(date_from=date_from, date_to=date_to)
    income = sum((r["income"] for r in rows), ZERO)
    expense = sum((r["expense"] for r in rows), ZERO)
    return {
        "by_business": rows,
        "consolidated": {
            "income": income,
            "expense": expense,
            "profit": income - expense,
        },
    }


def cash_report(*, date_from: dt.date | None = None, date_to: dt.date | None = None) -> dict:
    """ФНС-11: cash register balances and turnover (finance department view)."""
    rows = cash_selectors.register_balances(date_from=date_from, date_to=date_to)
    total_balance = sum((Decimal(r["balance"]) for r in rows), ZERO)
    total_turnover = sum((Decimal(r["turnover"]) for r in rows), ZERO)
    return {
        "registers": rows,
        "total_balance": total_balance,
        "total_turnover": total_turnover,
    }


def settlements_report(
    *, date_from: dt.date | None = None, date_to: dt.date | None = None
) -> dict:
    """ФНС-12: inter-business debts registry (who owes whom)."""
    registry = settlements_selectors.debt_registry(date_from=date_from, date_to=date_to)
    total_outstanding = sum((Decimal(r["outstanding"]) for r in registry), ZERO)
    return {"registry": registry, "total_outstanding": total_outstanding}


def payroll_report(*, year: int | None = None, month: int | None = None) -> dict:
    """ФНС-13: payroll fund overall and per business, + consolidated profit."""
    fund = payroll_selectors.payroll_fund(year=year, month=month)
    by_business = payroll_selectors.fund_by_business(year=year, month=month)
    return {
        "fund": fund,
        "by_business": by_business,
        "period": {"year": year, "month": month},
    }


def dashboard(*, date_from: dt.date | None = None, date_to: dt.date | None = None) -> dict:
    """High-level KPIs for the owner/finance dashboard."""
    from django.utils import timezone

    pnl_data = pnl(date_from=date_from, date_to=date_to)
    cash_data = cash_report(date_from=date_from, date_to=date_to)
    settle_data = settlements_report(date_from=date_from, date_to=date_to)
    fund = payroll_selectors.payroll_fund()

    # 📈 Доходы / 📉 Расходы / 💎 Чистая прибыль ЗА СЕГОДНЯ — always today's
    # numbers regardless of the selected period.
    today = timezone.localdate()
    today_totals = finance_selectors.business_totals(date_from=today, date_to=today)

    external = settlements_selectors.external_summary()

    return {
        "income": pnl_data["consolidated"]["income"],
        "expense": pnl_data["consolidated"]["expense"],
        "profit": pnl_data["consolidated"]["profit"],
        "today": {
            "income": today_totals["income"],
            "expense": today_totals["expense"],
            "profit": today_totals["profit"],
        },
        "cash_balance": cash_data["total_balance"],
        "open_debts": settle_data["total_outstanding"],
        "payroll_fund": fund,
        "by_business": pnl_data["by_business"],
        # Дебиторка / кредиторка с внешними контрагентами
        "receivables_total": external["total_receivable"],
        "payables_total": external["total_payable"],
        "receivables": external["receivables"],
        "payables": external["payables"],
    }
