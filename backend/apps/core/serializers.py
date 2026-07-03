from decimal import Decimal

from rest_framework import serializers

from .models import Business, City, ExpenseCategory, SiteObject


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
