"""
Write layer for payroll: all business logic + transactions (ЗРП-01…05).

Financial invariants enforced:
  * every mutation is atomic (``transaction.atomic``);
  * a locked run cannot be recalculated (APPROVED/PAID raise ``payroll_locked``);
  * status transitions lock the run row (``select_for_update``) and are
    idempotent (re-approving / re-paying is a no-op);
  * every money/status change is written to the audit log in the same
    transaction.

The bonus engine (:func:`compute_bonus`) is a *pure* function — no DB, all
arithmetic through ``apps.core.money.money`` — so it can be unit-tested and
reused from API, Celery or management commands.
"""
from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.core.enums import PayrollStatus
from apps.core.exceptions import DomainError
from apps.core.money import ZERO, money

from .models import Employee, PayrollItem, PayrollRun, PayrollScheme


# --------------------------------------------------------------------------- #
# Bonus engine (pure) — ЗРП-04, ЗРП-05
# --------------------------------------------------------------------------- #
def compute_bonus(scheme: PayrollScheme, metrics: dict) -> tuple[Decimal, list[dict]]:
    """Compute the bonus for a scheme given input metrics (ЗРП-04, ЗРП-05).

    Returns ``(bonus_total, breakdown)`` where ``breakdown`` is a list of dicts
    describing each rule's contribution. All arithmetic goes through
    :func:`apps.core.money.money`. Supported rule ``type`` values:

    * ``percent_of_sales`` — ``bonus += money(sales) * percent / 100`` (ЗРП-04:
      фикс + 10% продаж).
    * ``per_unit`` — ``n = metrics[metric]``; if ``threshold`` is set and
      ``n > threshold`` then ``bonus += n * threshold_rate`` else ``bonus +=
      n * rate`` (ЗРП-05: 500 сом/квартира, при >10 кв/мес → 1000 сом/квартира).
    * ``fixed_bonus`` — ``bonus += money(amount)``.

    Unknown rule types are ignored but noted in the breakdown.
    """
    metrics = metrics or {}
    total = ZERO
    breakdown: list[dict] = []
    rules = scheme.rules if scheme and scheme.rules else []

    for rule in rules:
        rtype = rule.get("type")

        if rtype == "percent_of_sales":
            sales = money(metrics.get("sales", 0))
            percent = money(rule.get("percent", 0))
            amount = money(sales * percent / Decimal("100"))
            total += amount
            breakdown.append({
                "type": rtype,
                "sales": str(sales),
                "percent": str(percent),
                "amount": str(amount),
            })

        elif rtype == "per_unit":
            metric = rule.get("metric", "")
            n = money(metrics.get(metric, 0))
            rate = money(rule.get("rate", 0))
            threshold = rule.get("threshold")
            threshold_rate = rule.get("threshold_rate")
            if threshold is not None and n > money(threshold) and threshold_rate is not None:
                used_rate = money(threshold_rate)
            else:
                used_rate = rate
            amount = money(n * used_rate)
            total += amount
            breakdown.append({
                "type": rtype,
                "metric": metric,
                "n": str(n),
                "rate": str(used_rate),
                "amount": str(amount),
            })

        elif rtype == "fixed_bonus":
            amount = money(rule.get("amount", 0))
            total += amount
            breakdown.append({"type": rtype, "amount": str(amount)})

        else:
            breakdown.append({"type": rtype, "ignored": True})

    return money(total), breakdown


# --------------------------------------------------------------------------- #
# Payroll run lifecycle — ЗРП-01
# --------------------------------------------------------------------------- #
def _run_snapshot(run: PayrollRun) -> dict:
    return {
        "status": run.status,
        "total": str(run.total),
        "approved_by": run.approved_by_id,
        "paid_at": run.paid_at.isoformat() if run.paid_at else None,
    }


@transaction.atomic
def run_payroll(
    *, year: int, month: int, actor, metrics_by_employee: dict[int, dict] | None = None
) -> PayrollRun:
    """Calculate payroll for a period (ЗРП-01).

    Get-or-create the run for ``(year, month)``. A run already APPROVED or PAID
    is locked (``payroll_locked``). Otherwise existing draft items are discarded
    and every active employee is recalculated: ``total = base_salary + bonus``,
    where the bonus comes from the employee's scheme (ЗРП-04/05). The run is set
    to CALCULATED with the summed total.
    """
    metrics_by_employee = metrics_by_employee or {}

    run, _created = PayrollRun.objects.select_for_update().get_or_create(
        year=year,
        month=month,
        defaults={"created_by": actor if getattr(actor, "pk", None) else None},
    )
    if run.status in (PayrollStatus.APPROVED, PayrollStatus.PAID):
        raise DomainError(
            "payroll_locked",
            f"Расчёт за {year}-{month:02d} уже {run.get_status_display().lower()} — пересчёт запрещён",
        )

    # Recalculation: soft-delete previously computed items — money-bearing rows
    # are never physically deleted (the AliveManager hides them, history stays).
    for prior in list(PayrollItem.objects.filter(run=run)):
        prior.soft_delete(actor if getattr(actor, "pk", None) else None)

    run_total = ZERO
    count = 0
    for employee in Employee.objects.filter(is_active=True).select_related("scheme"):
        base = money(employee.base_salary)
        metrics = metrics_by_employee.get(employee.id, {})
        if employee.scheme:
            bonus, breakdown = compute_bonus(employee.scheme, metrics)
        else:
            bonus, breakdown = ZERO, []
        total = money(base + bonus)

        PayrollItem.objects.create(
            run=run,
            employee=employee,
            base_amount=base,
            bonus_amount=bonus,
            total_amount=total,
            details={"base": str(base), "bonus": str(bonus), "breakdown": breakdown},
            metrics=metrics,
        )
        run_total += total
        count += 1

    run.total = money(run_total)
    run.status = PayrollStatus.CALCULATED
    run.save(update_fields=["total", "status", "updated_at"])

    AuditLog.record(
        actor, "payroll.calculated", run,
        after={"total": str(run.total), "count": count},
        meta={"year": year, "month": month},
    )
    return run


@transaction.atomic
def approve_payroll(*, run_id: int, actor) -> PayrollRun:
    """Approve a calculated run (ЗРП-01). Idempotent: re-approving is a no-op."""
    run = PayrollRun.objects.select_for_update().get(pk=run_id)

    if run.status == PayrollStatus.APPROVED:
        return run  # idempotent
    if run.status != PayrollStatus.CALCULATED:
        # Only a calculated run may be approved (a DRAFT has no items / zero total).
        raise DomainError(
            "payroll_not_approvable",
            f"Утвердить можно только рассчитанный расчёт "
            f"(текущий статус: «{run.get_status_display()}»)",
        )

    before = _run_snapshot(run)
    run.status = PayrollStatus.APPROVED
    run.approved_by = actor if getattr(actor, "pk", None) else None
    run.approved_at = timezone.now()
    run.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])

    AuditLog.record(actor, "payroll.approved", run, before=before, after=_run_snapshot(run))
    return run


@transaction.atomic
def mark_paid(*, run_id: int, actor) -> PayrollRun:
    """Mark an approved run as paid from head office (ЗРП-01).

    Requires the run to be APPROVED. Idempotent: re-paying a PAID run is a no-op.
    """
    run = PayrollRun.objects.select_for_update().get(pk=run_id)

    if run.status == PayrollStatus.PAID:
        return run  # idempotent
    if run.status != PayrollStatus.APPROVED:
        raise DomainError(
            "payroll_not_payable",
            "Выплатить можно только утверждённый расчёт (ЗРП-01)",
        )

    before = _run_snapshot(run)
    run.status = PayrollStatus.PAID
    run.paid_at = timezone.now()
    run.save(update_fields=["status", "paid_at", "updated_at"])

    AuditLog.record(actor, "payroll.paid", run, before=before, after=_run_snapshot(run))
    return run
