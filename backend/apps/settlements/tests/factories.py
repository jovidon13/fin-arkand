import datetime as dt

import factory

from apps.core.enums import DebtStatus, TransferStatus
from apps.core.tests.factories import BusinessFactory
from apps.settlements.models import Debt, Transfer


class TransferFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Transfer

    from_business = factory.SubFactory(BusinessFactory)
    to_business = factory.SubFactory(BusinessFactory)
    amount = 1000
    occurred_on = factory.LazyFunction(dt.date.today)
    status = TransferStatus.PENDING
    is_barter = False


class DebtFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Debt

    debtor = factory.SubFactory(BusinessFactory)
    creditor = factory.SubFactory(BusinessFactory)
    amount = 1000
    outstanding = 1000
    status = DebtStatus.OPEN
    occurred_on = factory.LazyFunction(dt.date.today)
