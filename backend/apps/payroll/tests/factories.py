import factory

from apps.core.enums import EmployeeSalaryType
from apps.core.tests.factories import BusinessFactory
from apps.payroll.models import Employee, PayrollScheme


class PayrollSchemeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PayrollScheme

    name = factory.Sequence(lambda n: f"Схема {n}")
    base_fixed = 0
    rules = factory.LazyFunction(list)
    is_active = True


class SalespersonSchemeFactory(PayrollSchemeFactory):
    """ЗРП-04: фикс + 10% продаж."""

    name = "Продажник фикс+10%"
    rules = factory.LazyFunction(
        lambda: [{"type": "percent_of_sales", "percent": 10}]
    )


class DeveloperSchemeFactory(PayrollSchemeFactory):
    """ЗРП-05: 500 сом/квартира, при >10 кв/мес → 1000 сом/квартира."""

    name = "Застройщик за квартиры"
    rules = factory.LazyFunction(
        lambda: [{
            "type": "per_unit", "metric": "apartments",
            "rate": 500, "threshold": 10, "threshold_rate": 1000,
        }]
    )


class EmployeeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Employee

    full_name = factory.Sequence(lambda n: f"Сотрудник {n}")
    business = factory.SubFactory(BusinessFactory)
    salary_type = EmployeeSalaryType.OBJECT
    base_salary = 3000
    is_salesperson = False
    is_active = True
