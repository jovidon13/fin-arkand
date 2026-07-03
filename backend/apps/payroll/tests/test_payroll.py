from decimal import Decimal

import pytest

from apps.core.enums import PayrollStatus
from apps.core.exceptions import DomainError
from apps.core.tests.factories import BusinessFactory, UserFactory
from apps.payroll import selectors, services
from apps.payroll.models import PayrollItem
from apps.payroll.services import compute_bonus
from apps.payroll.tests.factories import (
    DeveloperSchemeFactory,
    EmployeeFactory,
    SalespersonSchemeFactory,
)

pytestmark = pytest.mark.django_db


def test_salesperson_scheme_percent_of_sales():
    """ЗРП-04: фикс 3000 + 10% от продаж 20000 → 3000 + 2000 = 5000."""
    actor = UserFactory()
    scheme = SalespersonSchemeFactory()
    EmployeeFactory(base_salary=3000, is_salesperson=True, scheme=scheme)

    run = services.run_payroll(
        year=2026, month=1, actor=actor,
        metrics_by_employee={},  # metrics passed per employee below via re-run
    )
    # Re-run with metrics for the created employee.
    emp = scheme.employees.get()
    run = services.run_payroll(
        year=2026, month=1, actor=actor,
        metrics_by_employee={emp.id: {"sales": 20000}},
    )
    item = PayrollItem.objects.get(run=run, employee=emp)
    assert item.base_amount == Decimal("3000.00")
    assert item.bonus_amount == Decimal("2000.00")
    assert item.total_amount == Decimal("5000.00")


def test_compute_bonus_percent_of_sales_pure():
    """ЗРП-04: pure engine — 10% of 20000 = 2000."""
    scheme = SalespersonSchemeFactory.build()
    bonus, breakdown = compute_bonus(scheme, {"sales": 20000})
    assert bonus == Decimal("2000.00")
    assert breakdown[0]["type"] == "percent_of_sales"


def test_developer_scheme_below_threshold():
    """ЗРП-05: 8 квартир ≤ 10 → base 3000 + 8*500 = 7000."""
    scheme = DeveloperSchemeFactory.build()
    bonus, _ = compute_bonus(scheme, {"apartments": 8})
    assert bonus == Decimal("4000.00")


def test_developer_scheme_above_threshold():
    """ЗРП-05: 12 квартир > 10 → base 3000 + 12*1000 = 15000."""
    actor = UserFactory()
    scheme = DeveloperSchemeFactory()
    emp = EmployeeFactory(base_salary=3000, scheme=scheme)

    run = services.run_payroll(
        year=2026, month=2, actor=actor,
        metrics_by_employee={emp.id: {"apartments": 12}},
    )
    item = PayrollItem.objects.get(run=run, employee=emp)
    assert item.base_amount == Decimal("3000.00")
    assert item.bonus_amount == Decimal("12000.00")
    assert item.total_amount == Decimal("15000.00")

    # And below threshold gives 7000 total.
    run2 = services.run_payroll(
        year=2026, month=3, actor=actor,
        metrics_by_employee={emp.id: {"apartments": 8}},
    )
    item2 = PayrollItem.objects.get(run=run2, employee=emp)
    assert item2.total_amount == Decimal("7000.00")


def test_run_total_sums_items():
    """The run total equals the sum of its item totals (ЗРП-01)."""
    actor = UserFactory()
    scheme = SalespersonSchemeFactory()
    e1 = EmployeeFactory(base_salary=3000, scheme=scheme)
    EmployeeFactory(base_salary=2000, scheme=None)  # picked up by the run too

    run = services.run_payroll(
        year=2026, month=4, actor=actor,
        metrics_by_employee={e1.id: {"sales": 20000}},
    )
    # e1: 3000 + 2000 = 5000; e2: 2000 + 0 = 2000 → 7000
    assert run.total == Decimal("7000.00")
    assert selectors.run_total(run.id) == Decimal("7000.00")


def test_approve_is_idempotent_and_pay_requires_approval():
    """approve is idempotent; mark_paid requires an approved run (ЗРП-01)."""
    actor = UserFactory()
    EmployeeFactory(base_salary=3000)
    run = services.run_payroll(year=2026, month=5, actor=actor)
    assert run.status == PayrollStatus.CALCULATED

    # Cannot pay before approval.
    with pytest.raises(DomainError) as exc:
        services.mark_paid(run_id=run.id, actor=actor)
    assert exc.value.code == "payroll_not_payable"

    approved = services.approve_payroll(run_id=run.id, actor=actor)
    assert approved.status == PayrollStatus.APPROVED
    approved_at = approved.approved_at

    # Idempotent re-approve — no change.
    again = services.approve_payroll(run_id=run.id, actor=actor)
    assert again.status == PayrollStatus.APPROVED
    assert again.approved_at == approved_at

    paid = services.mark_paid(run_id=run.id, actor=actor)
    assert paid.status == PayrollStatus.PAID
    assert paid.paid_at is not None
    paid_at = paid.paid_at

    # Idempotent re-pay.
    paid_again = services.mark_paid(run_id=run.id, actor=actor)
    assert paid_again.paid_at == paid_at


def test_run_payroll_locked_after_approval():
    """A run that is APPROVED cannot be recalculated (ЗРП-01)."""
    actor = UserFactory()
    EmployeeFactory(base_salary=3000)
    run = services.run_payroll(year=2026, month=6, actor=actor)
    services.approve_payroll(run_id=run.id, actor=actor)

    with pytest.raises(DomainError) as exc:
        services.run_payroll(year=2026, month=6, actor=actor)
    assert exc.value.code == "payroll_locked"


def test_payroll_fund_sums_period_items():
    """ФНС-13: payroll fund = sum of item totals for the period."""
    actor = UserFactory()
    biz = BusinessFactory()
    scheme = SalespersonSchemeFactory()
    e1 = EmployeeFactory(business=biz, base_salary=3000, scheme=scheme)
    EmployeeFactory(business=biz, base_salary=2000)

    run = services.run_payroll(
        year=2026, month=7, actor=actor,
        metrics_by_employee={e1.id: {"sales": 20000}},
    )
    # calculated run counts towards the fund
    assert selectors.payroll_fund(year=2026, month=7) == Decimal("7000.00")
    assert selectors.payroll_fund(year=2026, month=7, business_id=biz.id) == Decimal("7000.00")

    rows = selectors.fund_by_business(year=2026, month=7)
    row = next(r for r in rows if r["business_id"] == biz.id)
    assert row["fund"] == Decimal("7000.00")

    # Different period → empty fund.
    assert selectors.payroll_fund(year=2025, month=1) == Decimal("0.00")
    assert run.status == PayrollStatus.CALCULATED
