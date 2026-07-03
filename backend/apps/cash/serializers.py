from decimal import Decimal

from rest_framework import serializers

from apps.core.enums import PayMethod, TxKind

from . import selectors
from .models import CashOperation, CashRegister


class CashRegisterSerializer(serializers.ModelSerializer):
    """Read/write representation of a cash register. Balance is computed via the
    selector layer; amounts are strings (money-in-JSON contract)."""

    business_name = serializers.CharField(source="business.name", read_only=True)
    balance = serializers.SerializerMethodField()

    class Meta:
        model = CashRegister
        fields = [
            "id", "business", "business_name", "name", "code",
            "turnover_limit", "responsible", "is_active", "balance",
            "created_at",
        ]
        read_only_fields = ["balance"]

    def get_balance(self, obj) -> str:
        return str(selectors.register_balance(obj.id))


class CashOperationSerializer(serializers.ModelSerializer):
    """Read representation. Amounts (incl. signed) are strings."""

    register_name = serializers.CharField(source="register.name", read_only=True)
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)
    method_display = serializers.CharField(source="get_method_display", read_only=True)
    signed_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = CashOperation
        fields = [
            "id", "register", "register_name", "kind", "kind_display",
            "amount", "signed_amount", "method", "method_display",
            "occurred_on", "counterparty", "note",
            "created_by", "created_by_name", "finance_transaction",
            "created_at",
        ]


class CashOperationCreateSerializer(serializers.Serializer):
    """Write payload → passed to ``services.add_operation``."""

    register = serializers.IntegerField()
    kind = serializers.ChoiceField(choices=TxKind.choices)
    amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal("0.01")
    )
    method = serializers.ChoiceField(choices=PayMethod.choices)
    occurred_on = serializers.DateField()
    counterparty = serializers.CharField(required=False, allow_blank=True, default="")
    note = serializers.CharField(required=False, allow_blank=True, default="")


class SetLimitSerializer(serializers.Serializer):
    """Payload for the ``set_limit`` action (КАС-03)."""

    limit = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal("0")
    )
