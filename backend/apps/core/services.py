"""Write layer for core reference data (Часть 0)."""
from __future__ import annotations

from django.db import transaction
from rest_framework import status

from apps.audit.models import AuditLog
from apps.core.exceptions import DomainError
from apps.core.money import ZERO, money

from .models import Business


@transaction.atomic
def set_expense_limit(*, business_id: int, limit, actor) -> Business:
    """Change a business's «крупно/мелко» expense threshold (ХОЛ-21).

    Only holding owners may change limits/thresholds (enforced at the API layer
    via ``IsOwner``). ``0`` means no threshold (every expense is «мелко»). The
    change is audited.
    """
    limit = money(limit)
    if limit < ZERO:
        raise DomainError("limit_negative", "Порог не может быть отрицательным")

    try:
        business = Business.objects.select_for_update().get(pk=business_id)
    except Business.DoesNotExist:
        raise DomainError(
            "business_not_found", "Бизнес не найден",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from None

    before = {"expense_limit": str(business.expense_limit)}
    business.expense_limit = limit
    business.save(update_fields=["expense_limit", "updated_at"])
    AuditLog.record(
        actor, "business.limit.changed", business,
        before=before, after={"expense_limit": str(business.expense_limit)},
    )
    return business
