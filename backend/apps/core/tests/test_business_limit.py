from decimal import Decimal

import pytest

from apps.audit.models import AuditLog
from apps.core import services
from apps.core.exceptions import DomainError
from apps.core.tests.factories import BusinessFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_set_expense_limit_updates_and_audits():
    """ХОЛ-21: the «крупно/мелко» threshold can be changed and is audited."""
    actor = UserFactory()
    business = BusinessFactory(expense_limit=0)

    updated = services.set_expense_limit(
        business_id=business.id, limit=Decimal("50000"), actor=actor
    )

    assert updated.expense_limit == Decimal("50000.00")
    business.refresh_from_db()
    assert business.expense_limit == Decimal("50000.00")
    assert AuditLog.objects.filter(
        action="business.limit.changed", object_id=str(business.id)
    ).exists()


def test_set_expense_limit_rejects_negative():
    actor = UserFactory()
    business = BusinessFactory(expense_limit=0)
    with pytest.raises(DomainError) as exc:
        services.set_expense_limit(
            business_id=business.id, limit=Decimal("-1"), actor=actor
        )
    assert exc.value.code == "limit_negative"


def test_set_expense_limit_missing_business_is_404():
    actor = UserFactory()
    with pytest.raises(DomainError) as exc:
        services.set_expense_limit(business_id=999999, limit=Decimal("100"), actor=actor)
    assert exc.value.code == "business_not_found"
    assert exc.value.status_code == 404
