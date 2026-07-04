from decimal import Decimal

from rest_framework import serializers

from .models import Business, City, ExpenseCategory, SiteObject


class PersonNameField(serializers.Field):
    """Human name of a related user with a username fallback.

    Unlike ``source="user.get_full_name"`` (which collapses to an empty string
    when first/last name are blank), this returns the username so «кто провёл /
    проверил / получил» is never shown as «—» just because the profile has no
    full name filled in.
    """

    def __init__(self, attr: str, **kwargs):
        self._attr = attr
        kwargs["read_only"] = True
        kwargs.setdefault("source", "*")
        super().__init__(**kwargs)

    def to_representation(self, obj):
        user = getattr(obj, self._attr, None)
        if user is None:
            return None
        return user.get_full_name() or user.username


class BusinessSerializer(serializers.ModelSerializer):
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = Business
        fields = ["id", "code", "name", "kind", "kind_display", "expense_limit", "is_active"]


class SetExpenseLimitSerializer(serializers.Serializer):
    """Payload for the owner-only expense-limit action (ХОЛ-21)."""

    expense_limit = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal("0")
    )


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["id", "name"]


class SiteObjectSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    business_name = serializers.CharField(source="business.name", read_only=True)

    class Meta:
        model = SiteObject
        fields = ["id", "name", "city", "city_name", "business", "business_name",
                  "address", "is_active"]


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ["id", "code", "name", "is_active"]
