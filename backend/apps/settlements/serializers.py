"""Serializers for settlements: validation of input + shape of responses.

Amounts are strings in JSON (money-in-JSON contract). No domain logic here.
"""
from decimal import Decimal

from rest_framework import serializers

from apps.core.enums import ExternalDebtDirection, SettlementKind

from .models import Debt, ExternalDebt, Settlement, Transfer


class TransferSerializer(serializers.ModelSerializer):
    """Read representation of a transfer (БАР-01)."""

    from_business_name = serializers.CharField(source="from_business.name", read_only=True)
    to_business_name = serializers.CharField(source="to_business.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    approved_by_name = serializers.CharField(
        source="approved_by.get_full_name", read_only=True, default=None
    )
    debt_id = serializers.IntegerField(source="debt.id", read_only=True, default=None)

    class Meta:
        model = Transfer
        fields = [
            "id", "from_business", "from_business_name",
            "to_business", "to_business_name",
            "amount", "description", "occurred_on", "is_barter",
            "status", "status_display", "created_by",
            "approved_by", "approved_by_name", "approved_at",
            "debt_id", "created_at",
        ]
        read_only_fields = ["status", "approved_by", "approved_at", "created_by"]


class TransferCreateSerializer(serializers.Serializer):
    """Write payload → passed to ``services.create_transfer``."""

    from_business = serializers.IntegerField()
    to_business = serializers.IntegerField()
    amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal("0.01")
    )
    occurred_on = serializers.DateField()
    description = serializers.CharField(required=False, allow_blank=True, default="")
    is_barter = serializers.BooleanField(required=False, default=False)


class ApproveSerializer(serializers.Serializer):
    """Optional/empty payload for the approve action."""


class RejectSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class DebtSerializer(serializers.ModelSerializer):
    """Read representation of a debt (БАР-02)."""

    debtor_name = serializers.CharField(source="debtor.name", read_only=True)
    creditor_name = serializers.CharField(source="creditor.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    is_settled = serializers.BooleanField(read_only=True)

    class Meta:
        model = Debt
        fields = [
            "id", "debtor", "debtor_name", "creditor", "creditor_name",
            "amount", "outstanding", "status", "status_display", "is_settled",
            "is_barter", "source_transfer", "occurred_on", "created_at",
        ]
        read_only_fields = fields


class SettlementSerializer(serializers.ModelSerializer):
    """Read representation of a debt closing (БАР-03)."""

    kind_display = serializers.CharField(source="get_kind_display", read_only=True)
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = Settlement
        fields = [
            "id", "debt", "kind", "kind_display", "amount",
            "counter_debt", "note", "occurred_on",
            "created_by", "created_by_name", "created_at",
        ]
        read_only_fields = fields


class SettleSerializer(serializers.Serializer):
    """Write payload → passed to ``services.settle_debt``."""

    kind = serializers.ChoiceField(choices=SettlementKind.choices)
    amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal("0.01")
    )
    occurred_on = serializers.DateField()
    counter_debt = serializers.IntegerField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True, default="")


class ExternalDebtSerializer(serializers.ModelSerializer):
    """Read representation of an external receivable / payable."""

    direction_display = serializers.CharField(source="get_direction_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    business_name = serializers.CharField(source="business.name", read_only=True, default=None)
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = ExternalDebt
        fields = [
            "id", "direction", "direction_display", "counterparty",
            "business", "business_name", "amount", "outstanding",
            "status", "status_display", "occurred_on", "due_on", "note",
            "created_by", "created_by_name", "created_at",
        ]
        read_only_fields = ["outstanding", "status", "created_by"]


class ExternalDebtCreateSerializer(serializers.Serializer):
    """Write payload → passed to ``services.create_external_debt``."""

    direction = serializers.ChoiceField(choices=ExternalDebtDirection.choices)
    counterparty = serializers.CharField(max_length=200)
    business = serializers.IntegerField(required=False, allow_null=True)
    amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal("0.01")
    )
    occurred_on = serializers.DateField()
    due_on = serializers.DateField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True, default="")


class ExternalDebtPaySerializer(serializers.Serializer):
    """Write payload → passed to ``services.pay_external_debt``."""

    amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal("0.01")
    )
    occurred_on = serializers.DateField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True, default="")
