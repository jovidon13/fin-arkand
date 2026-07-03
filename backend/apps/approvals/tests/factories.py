import datetime as dt

import factory

from apps.accounts.models import RoleCode
from apps.approvals.models import ApprovalRequest, ApprovalVote
from apps.core.enums import ApprovalStatus, VoteValue
from apps.core.tests.factories import BusinessFactory, RoleFactory, UserFactory


class OwnerFactory(UserFactory):
    """A holding owner — the only role allowed to vote on approvals (ХОЛ-22)."""

    role = factory.SubFactory(RoleFactory, code=RoleCode.OWNER)


class ApprovalRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ApprovalRequest

    business = factory.SubFactory(BusinessFactory)
    amount = 50000
    purpose = factory.Sequence(lambda n: f"Крупная закупка {n}")
    status = ApprovalStatus.PENDING
    required_votes = 3
    occurred_on = factory.LazyFunction(dt.date.today)


class ApprovalVoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ApprovalVote

    request = factory.SubFactory(ApprovalRequestFactory)
    owner = factory.SubFactory(OwnerFactory)
    value = VoteValue.APPROVE
