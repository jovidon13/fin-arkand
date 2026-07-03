import datetime as dt

import factory

from apps.cash.models import CashOperation, CashRegister
from apps.core.enums import PayMethod, TxKind
from apps.core.tests.factories import BusinessFactory


class CashRegisterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CashRegister
        django_get_or_create = ("code",)

    business = factory.SubFactory(BusinessFactory)
    name = factory.Sequence(lambda n: f"Касса {n}")
    code = factory.Sequence(lambda n: f"cash-{n}")
    turnover_limit = 0
    is_active = True

    @factory.post_generation
    def responsible(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        for user in extracted:
            self.responsible.add(user)


class CashOperationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CashOperation

    register = factory.SubFactory(CashRegisterFactory)
    kind = TxKind.INCOME
    amount = 1000
    method = PayMethod.CASH
    occurred_on = factory.LazyFunction(dt.date.today)
