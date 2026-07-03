"""Shared test factories for foundation models (core + accounts)."""
import factory
from django.contrib.auth import get_user_model

from apps.accounts.models import Role, RoleCode
from apps.core.enums import BusinessKind
from apps.core.models import Business, City, ExpenseCategory, SiteObject

User = get_user_model()


class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role
        django_get_or_create = ("code",)

    code = RoleCode.ACCOUNTANT
    name = factory.LazyAttribute(lambda o: dict(RoleCode.choices).get(o.code, o.code))


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user{n}")
    first_name = factory.Faker("first_name")
    role = factory.SubFactory(RoleFactory)

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(extracted or "pass12345")
        if create:
            self.save()


class BusinessFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Business
        django_get_or_create = ("code",)

    code = factory.Sequence(lambda n: f"biz-{n}")
    name = factory.Sequence(lambda n: f"Бизнес {n}")
    kind = BusinessKind.DEVELOPER
    expense_limit = 10000


class CityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = City
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Город {n}")


class SiteObjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SiteObject

    name = factory.Sequence(lambda n: f"Объект {n}")
    business = factory.SubFactory(BusinessFactory)
    city = factory.SubFactory(CityFactory)


class ExpenseCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExpenseCategory
        django_get_or_create = ("code",)

    code = factory.Sequence(lambda n: f"cat-{n}")
    name = factory.Sequence(lambda n: f"Статья {n}")
