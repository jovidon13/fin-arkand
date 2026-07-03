from decimal import Decimal

from rest_framework import serializers

from apps.core.enums import PayMethod, TxKind, TxStatus

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    """Read representation. Amounts are strings (money-in-JSON contract)."""

    business_name = serializers.CharField(source="business.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    method_display = serializers.CharField(source="get_method_display", read_only=True)
    signed_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    confirmed_by_name = serializers.CharField(
        source="confirmed_by.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = Transaction
        fields = [
            "id", "business", "business_name", "kind", "kind_display",
            "category", "category_name", "amount", "signed_amount",
            "method", "method_display", "status", "status_display",
            "occurred_on", "site_object", "counterparty", "note",
            "is_barter", "source", "confirmed_by", "confirmed_by_name",
            "confirmed_at", "created_at",
        ]
        read_only_fields = ["status", "confirmed_by", "confirmed_at"]


class TransactionCreateSerializer(serializers.Serializer):
    """Write payload → passed to ``services.create_transaction``."""

    business = serializers.IntegerField()
    kind = serializers.ChoiceField(choices=TxKind.choices)
    category = serializers.IntegerField(required=False, allow_null=True)
    amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal("0.01")
    )
    method = serializers.ChoiceField(choices=PayMethod.choices)
    occurred_on = serializers.DateField()
    site_object = serializers.IntegerField(required=False, allow_null=True)
    counterparty = serializers.CharField(required=False, allow_blank=True, default="")
    note = serializers.CharField(required=False, allow_blank=True, default="")
    is_barter = serializers.BooleanField(required=False, default=False)
    source = serializers.CharField(required=False, allow_blank=True, default="")
    status = serializers.ChoiceField(
        choices=[TxStatus.DRAFT, TxStatus.PENDING], required=False, default=TxStatus.PENDING
    )


class ConfirmSerializer(serializers.Serializer):
    idempotency_key = serializers.CharField(required=False, allow_blank=True, default="")


class RejectSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")
