from django.urls import path

from .views import (
    CashReportView,
    DashboardView,
    PayrollReportView,
    PnlReportView,
    SettlementsReportView,
)

urlpatterns = [
    path("reports/dashboard", DashboardView.as_view(), name="report-dashboard"),
    path("reports/pnl", PnlReportView.as_view(), name="report-pnl"),
    path("reports/cash", CashReportView.as_view(), name="report-cash"),
    path("reports/settlements", SettlementsReportView.as_view(), name="report-settlements"),
    path("reports/payroll", PayrollReportView.as_view(), name="report-payroll"),
]
