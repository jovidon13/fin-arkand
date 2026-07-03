import datetime as dt

import factory

from apps.core.enums import PayMethod, TxKind, TxStatus
from apps.core.tests.factories import BusinessFactory, ExpenseCategoryFactory
from apps.finance.models import Transaction


class TransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Transaction

    business = factory.SubFactory(BusinessFactory)
    kind = TxKind.INCOME
    amount = 1000
    method = PayMethod.CASH
    status = TxStatus.PENDING
    occurred_on = factory.LazyFunction(dt.date.today)


class ExpenseFactory(TransactionFactory):
    kind = TxKind.EXPENSE
    category = factory.SubFactory(ExpenseCategoryFactory)
