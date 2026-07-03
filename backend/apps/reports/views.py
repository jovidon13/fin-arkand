"""
Report endpoints (ФНС-10…13). Thin read-only APIViews → reports.selectors.
Decimal amounts are stringified so money stays a string in JSON (never float).
"""
from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsFinanceStaff
from apps.core.money import stringify as _stringify
from apps.core.selectors import parse_int_param, parse_period

from . import selectors


class _ReportView(APIView):
    permission_classes = [IsFinanceStaff]


class PnlReportView(_ReportView):
    """ФНС-10: поступления/расходы/прибыль по бизнесам и сводно."""

    def get(self, request: Request) -> Response:
        date_from, date_to = parse_period(request.query_params)
        return Response(_stringify(selectors.pnl(date_from=date_from, date_to=date_to)))


class CashReportView(_ReportView):
    """ФНС-11: остатки и обороты касс."""

    def get(self, request: Request) -> Response:
        date_from, date_to = parse_period(request.query_params)
        return Response(_stringify(selectors.cash_report(date_from=date_from, date_to=date_to)))


class SettlementsReportView(_ReportView):
    """ФНС-12: взаиморасчёты и долги между бизнесами."""

    def get(self, request: Request) -> Response:
        date_from, date_to = parse_period(request.query_params)
        return Response(
            _stringify(selectors.settlements_report(date_from=date_from, date_to=date_to))
        )


class PayrollReportView(_ReportView):
    """ФНС-13: зарплатный фонд; прибыль по бизнесам и по холдингу."""

    def get(self, request: Request) -> Response:
        year = parse_int_param(request.query_params, "year")
        month = parse_int_param(request.query_params, "month")
        return Response(
            _stringify(selectors.payroll_report(year=year, month=month))
        )


class DashboardView(_ReportView):
    """Consolidated KPIs for the owner/finance dashboard."""

    def get(self, request: Request) -> Response:
        date_from, date_to = parse_period(request.query_params)
        return Response(_stringify(selectors.dashboard(date_from=date_from, date_to=date_to)))
